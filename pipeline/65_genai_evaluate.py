# Databricks notebook source
# MAGIC %md
# MAGIC # 65_genai_evaluate — MLflow 3 GenAI evaluation of the stored appeal generations
# MAGIC
# MAGIC Replays the stored `appeals_output` rows (no LLM generation call) through `mlflow.genai.evaluate`.
# MAGIC Each row becomes a trace: a RETRIEVER span carries the grounding the generator saw (criteria, dated notes,
# MAGIC clinical digest, claim facts, MPFS context); the root span carries the stored determination, letter and worksheet.
# MAGIC
# MAGIC Scorers
# MAGIC - `groundedness` — built-in `RetrievalGroundedness` (judge: Databricks-hosted Claude Sonnet 4.6). Every factual claim in the letter/worksheet must be implied by the retrieved grounding. The retrieval context is the generator's own CLAIM / criteria / MPFS / notes / digest / denial blocks (genai/eval_logic.py, drift-tested against 30_generate_appeals.sql), plus the placeholder rule.
# MAGIC - `no_fabricated_evidence` — `Guidelines` judge. No dates, test results, treatments or events absent from the notes.
# MAGIC - `quote_verified_strict` / `quote_verified_normalised` — deterministic `@scorer` (same logic as `60_evaluate.py`, in `genai/eval_logic.py`).
# MAGIC - `determination_matches_label` — deterministic `@scorer`; joins `eval_case_labels` as **expectations only**. Labels never reach generation.
# MAGIC
# MAGIC Outputs: experiment `/Shared/fe-bar-appeals-eval` (run + traces), Delta `genai_eval_results` (per row), `genai_eval_summary` (per run).
# MAGIC Cost guard: token-count estimate is printed first; the run aborts if the estimate exceeds `cost_cap_usd`.

# COMMAND ----------

import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone

import mlflow
from mlflow.entities import Feedback
from mlflow.genai.scorers import Guidelines, RetrievalGroundedness, scorer

def _param(name, default):
    """Job base_parameters / widgets with a local default for interactive runs."""
    try:
        dbutils.widgets.text(name, default)  # noqa: F821 (provided by the Databricks runtime)
        return dbutils.widgets.get(name)  # noqa: F821
    except NameError:
        return default

dbutils.widgets.text("max_rows", "60")  # noqa: F821
dbutils.widgets.text("cost_cap_usd", "5")  # noqa: F821
dbutils.widgets.text("judge_model", "databricks:/databricks-claude-sonnet-4-6")  # noqa: F821

CATALOG_DEFAULT = "appeals_hackathon_catalog"  # live value; the job passes the bundle target's catalog
SCHEMA_DEFAULT = "fe_bar_appeals"  # live value; the job passes the bundle target's schema
CATALOG = _param("catalog", CATALOG_DEFAULT).strip()
SCHEMA = _param("schema", SCHEMA_DEFAULT).strip()
for _name, _val in (("catalog", CATALOG), ("schema", SCHEMA)):
    # Object names (tables, views, functions, volumes, paths) are built from these two values only.
    # Plain identifiers only: no quotes, dots, spaces or SQL, so nothing user-supplied reaches SQL text.
    if not re.fullmatch(r"[A-Za-z0-9_]+", _val):
        raise ValueError(f"{_name} must be a plain identifier, got {_val!r}")
FQ = f"{CATALOG}.{SCHEMA}"
MAX_ROWS = int(dbutils.widgets.get("max_rows"))  # noqa: F821
COST_CAP_USD = float(dbutils.widgets.get("cost_cap_usd"))  # noqa: F821
JUDGE_MODEL = dbutils.widgets.get("judge_model")  # noqa: F821
EXPERIMENT = "/Shared/fe-bar-appeals-eval"
RUN_ID = str(uuid.uuid4())
RUN_TS = datetime.now(timezone.utc)

# list price, Claude Sonnet 4.6 (claude-api pricing table: $3 input / $15 output per 1M tokens)
PRICE_IN_PER_M = 3.0
PRICE_OUT_PER_M = 15.0
JUDGE_CALLS_PER_ROW = 2  # groundedness + no_fabricated_evidence (quote and determination scorers are deterministic)


def _repo_root():
    """Bundle sync puts this notebook at <root>/pipeline/65_genai_evaluate; the package is <root>/genai."""
    try:
        nb_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()  # noqa: F821
        return "/Workspace" + os.path.dirname(os.path.dirname(nb_path))
    except Exception:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # local/IDE fallback


REPO_ROOT = _repo_root()
if not os.path.isdir(os.path.join(REPO_ROOT, "genai")):
    raise FileNotFoundError(f"genai package not found under {REPO_ROOT}; check the bundle sync root")
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from genai.eval_logic import (  # noqa: E402
    build_grounding_docs, determination_matches, estimate_judge_cost, grounding_text, quote_check,
    quote_text, rate,
)

NO_FABRICATION_GUIDELINE = (
    "The response must not contain any date, test or lab result, score, measurement, procedure, device, "
    "medication, treatment, or clinical event that is absent from the retrieved context (the dated clinical notes, "
    "the clinical digest, the criteria and the claim facts). Every dated clinical fact cited in brackets, for example "
    "[2026-03-14 PT_VISIT], must match a dated note in the context. Identifiers copied from the claim facts are in the "
    "context and are not violations. Stating that a "
    "fact is unknown, missing or needs review is compliant. Bracketed placeholders such as [Provider NPI], "
    "[Health System Name] and [Member ID] are instructed template fields the generator was told to use when a value is "
    "not supplied; they are allowed and are not claims. Fail the response if any invented or mismatched evidence appears."
)

# COMMAND ----------
# MAGIC %md ## 1. Build the eval dataset (latest generations, labels joined for evaluation only)

# COMMAND ----------

# The 60 most recent generations by default. Rows whose grounding changed after generation (input_hash mismatch)
# are excluded: the judge must see the grounding the model actually saw.
DATASET_SQL = f"""
WITH labels AS (
  SELECT * FROM {FQ}.eval_case_labels
  QUALIFY row_number() OVER (PARTITION BY FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR
                             ORDER BY as_of_date DESC, generator_seed DESC) = 1
)
SELECT o.FACILITY_ID, o.PATIENT_CONTROL_NUMBER, o.ENCOUNTER_NBR, o.recommendation, o.needs_review_reason,
       o.appeal_letter, o.cheat_sheet, o.generated_at, o.priority_rank,
       l.expected_determination,
       g.criteria_block, g.notes_full, g.clinical_digest, g.mpfs_context, g.reason_text, g.what_to_prove,
       g.hcpcs_codes, g.dx_codes, g.payer_name, g.dob, g.sex, g.member_id, g.claim_number, g.dos, g.pos,
       g.modifiers, g.provider_name, g.total_charges, g.denial_code, g.patient_name, g.criteria_payer
FROM {FQ}.appeals_output o
JOIN {FQ}.encounter_grounding g
  ON g.FACILITY_ID = o.FACILITY_ID AND g.PATIENT_CONTROL_NUMBER = o.PATIENT_CONTROL_NUMBER AND g.ENCOUNTER_NBR = o.ENCOUNTER_NBR
JOIN labels l
  ON l.FACILITY_ID = o.FACILITY_ID AND l.PATIENT_CONTROL_NUMBER = o.PATIENT_CONTROL_NUMBER AND l.ENCOUNTER_NBR = o.ENCOUNTER_NBR
WHERE o.input_hash = g.input_hash
ORDER BY o.generated_at DESC, o.priority_rank
"""
candidates = spark.sql(DATASET_SQL)  # noqa: F821
stale = spark.sql(f"""SELECT count(*) n FROM {FQ}.appeals_output o
                      JOIN {FQ}.encounter_grounding g USING (FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR)
                      WHERE o.input_hash <> g.input_hash""").first().n  # noqa: F821
rows = [r.asDict() for r in candidates.limit(MAX_ROWS).collect()]
total_outputs = spark.sql(f"SELECT count(*) n FROM {FQ}.appeals_output").first().n  # noqa: F821
print(f"selected {len(rows)} rows (max_rows={MAX_ROWS}); appeals_output rows={total_outputs}; "
      f"excluded stale-grounding rows={stale}")

# COMMAND ----------
# MAGIC %md ## 2. Cost estimate from token counts (printed before any judge call)

# COMMAND ----------

def _flat(v):
    return "" if v is None else str(v)


char_counts = []
for r in rows:
    docs = build_grounding_docs(r)
    ctx = sum(len(d["page_content"]) for d in docs)
    resp = len(_flat(r["appeal_letter"])) + len(_flat(r["cheat_sheet"]))
    char_counts.append(ctx + resp)

estimate = estimate_judge_cost(char_counts, JUDGE_CALLS_PER_ROW, PRICE_IN_PER_M, PRICE_OUT_PER_M)
print("COST ESTIMATE (judge calls only; generation is not re-run):", json.dumps(estimate, indent=2))
print(f"cost_cap_usd={COST_CAP_USD}")
if estimate["est_cost_usd"] > COST_CAP_USD:
    raise ValueError(
        f"estimated judge cost ${estimate['est_cost_usd']} exceeds cost_cap_usd=${COST_CAP_USD}; "
        f"lower max_rows (currently {len(rows)}) or raise the cap deliberately")

# COMMAND ----------
# MAGIC %md ## 3. Tracing: replay the stored generation inside a trace (no model call)

# COMMAND ----------

STORED = {}  # encounter_key -> stored generation; read-only during evaluation (thread-safe)
for r in rows:
    key = f"{r['FACILITY_ID']}_{r['PATIENT_CONTROL_NUMBER']}_{r['ENCOUNTER_NBR']}"
    STORED[key] = {
        "determination": r["recommendation"],
        "appeal_letter": _flat(r["appeal_letter"]),
        "cheat_sheet": _flat(r["cheat_sheet"]),
    }


@mlflow.trace(span_type="RETRIEVER", name="grounding_retrieval")
def grounding_retrieval(encounter_key, grounding_docs):
    """The grounding the generator saw, recorded as the retrieval step (RetrievalGroundedness reads this span)."""
    return grounding_docs


@mlflow.trace(name="appeal_generation_replay")
def appeal_generation_replay(encounter_key, grounding_docs, grounding_flat):
    grounding_retrieval(encounter_key, grounding_docs)
    return STORED[encounter_key]


# COMMAND ----------
# MAGIC %md ## 4. Scorers

# COMMAND ----------

@scorer
def quote_verified(inputs, outputs):
    """Deterministic. Same rule as 60_evaluate.py: quoted spans in letter + worksheet found in the grounding."""
    text = quote_text(outputs.get("appeal_letter"), outputs.get("cheat_sheet"))
    q = quote_check(text, inputs["grounding_flat"])
    strict_ok = q["strict"] == q["total"]
    norm_ok = q["normalised"] == q["total"]
    why = f"{q['strict']}/{q['total']} quoted spans verbatim; {q['normalised']}/{q['total']} after normalisation"
    return [
        Feedback(name="quote_verified_strict", value="yes" if strict_ok else "no", rationale=why),
        Feedback(name="quote_verified_normalised", value="yes" if norm_ok else "no", rationale=why),
    ]


@scorer
def determination_matches_label(outputs, expectations):
    """Deterministic. The designed label is an expectation: used for scoring only, never for generation."""
    expected = (expectations or {}).get("expected_determination")
    predicted = (outputs or {}).get("determination")
    ok = determination_matches(predicted, expected)
    return Feedback(
        name="determination_matches_label", value="yes" if ok else "no",
        rationale=f"predicted={predicted!r} expected={expected!r}",
    )


groundedness = RetrievalGroundedness(name="groundedness", model=JUDGE_MODEL)
no_fabricated_evidence = Guidelines(name="no_fabricated_evidence", guidelines=NO_FABRICATION_GUIDELINE,
                                    model=JUDGE_MODEL)
SCORERS = [groundedness, no_fabricated_evidence, quote_verified, determination_matches_label]

# COMMAND ----------
# MAGIC %md ## 5. Run mlflow.genai.evaluate

# COMMAND ----------

eval_data = []
for r in rows:
    key = f"{r['FACILITY_ID']}_{r['PATIENT_CONTROL_NUMBER']}_{r['ENCOUNTER_NBR']}"
    eval_data.append({
        "inputs": {
            "encounter_key": key,
            "grounding_docs": build_grounding_docs(r),
            "grounding_flat": grounding_text(r),
        },
        "expectations": {"expected_determination": r["expected_determination"]},
    })

mlflow.set_experiment(EXPERIMENT)
result = mlflow.genai.evaluate(
    data=eval_data,
    predict_fn=appeal_generation_replay,
    scorers=SCORERS,
)
MLFLOW_RUN_ID = result.run_id
print("mlflow run", MLFLOW_RUN_ID, "experiment", EXPERIMENT)

# COMMAND ----------
# MAGIC %md ## 6. Per-row results and per-scorer rollup

# COMMAND ----------

SCORER_NAMES = ["groundedness", "no_fabricated_evidence", "quote_verified_strict",
                "quote_verified_normalised", "determination_matches_label"]


def _passed(v):
    return v is True or str(v).strip().lower() in ("yes", "true")


# Read scores from the traces of this run (one trace per row). The result frame's column layout is not relied on:
# the encounter key comes from the root span inputs, scores from the trace assessments.
exp_id = mlflow.get_experiment_by_name(EXPERIMENT).experiment_id
traces = mlflow.search_traces(locations=[exp_id], run_id=MLFLOW_RUN_ID,
                              max_results=max(2 * len(rows), 100), return_type="list")
by_key, trace_ids = {}, []
for t in traces:
    root = next(s for s in t.data.spans if s.parent_id is None)
    key = (root.inputs or {}).get("encounter_key")
    trace_ids.append(t.info.trace_id)
    rec = {"trace_id": t.info.trace_id}
    for a in t.info.assessments:
        if a.name in SCORER_NAMES:
            rec[a.name] = {"value": None if a.value is None else str(a.value),
                           "rationale": a.rationale, "error": None if a.error is None else str(a.error)}
    by_key[key] = rec
print(f"traces in run: {len(traces)} (rows selected: {len(rows)})")


def _get(rec, name, field):
    return (rec.get(name) or {}).get(field)


row_out = []
for r in rows:
    key = f"{r['FACILITY_ID']}_{r['PATIENT_CONTROL_NUMBER']}_{r['ENCOUNTER_NBR']}"
    rec = by_key.get(key, {})
    q = quote_check(quote_text(r["appeal_letter"], r["cheat_sheet"]), grounding_text(r))
    row_out.append({
        "run_id": RUN_ID, "run_ts": RUN_TS, "mlflow_run_id": MLFLOW_RUN_ID,
        "FACILITY_ID": int(r["FACILITY_ID"]), "PATIENT_CONTROL_NUMBER": int(r["PATIENT_CONTROL_NUMBER"]),
        "ENCOUNTER_NBR": int(r["ENCOUNTER_NBR"]), "expected_determination": r["expected_determination"],
        "predicted": r["recommendation"], "trace_id": rec.get("trace_id"),
        "groundedness": _get(rec, "groundedness", "value"),
        "groundedness_rationale": _get(rec, "groundedness", "rationale"),
        "no_fabricated_evidence": _get(rec, "no_fabricated_evidence", "value"),
        "no_fabricated_evidence_rationale": _get(rec, "no_fabricated_evidence", "rationale"),
        "quote_verified_strict": _get(rec, "quote_verified_strict", "value"),
        "quote_verified_normalised": _get(rec, "quote_verified_normalised", "value"),
        "quote_rationale": _get(rec, "quote_verified_strict", "rationale"),
        "quotes_total": q["total"], "quotes_strict": q["strict"], "quotes_normalised": q["normalised"],
        "determination_matches_label": _get(rec, "determination_matches_label", "value"),
        "scorer_errors": sum(1 for s in SCORER_NAMES if _get(rec, s, "error")),
        "judge_model": JUDGE_MODEL,
    })

pass_rates = {}
for s in ["groundedness", "no_fabricated_evidence", "quote_verified_strict", "quote_verified_normalised",
          "determination_matches_label"]:
    vals = [o[s] for o in row_out if o[s] is not None]
    pass_rates[s] = {"pass": sum(_passed(v) for v in vals), "scored": len(vals),
                     "rate": rate(sum(_passed(v) for v in vals), len(vals))}

qt = sum(o["quotes_total"] for o in row_out)
summary = {
    "run_id": RUN_ID, "run_ts_utc": RUN_TS.isoformat(), "experiment_path": EXPERIMENT,
    "mlflow_run_id": MLFLOW_RUN_ID, "rows_evaluated": len(rows), "appeals_output_rows": total_outputs,
    "excluded_stale_grounding_rows": stale, "max_rows": MAX_ROWS, "judge_model": JUDGE_MODEL,
    "trace_count": len(trace_ids), "estimated_judge_cost_usd": estimate["est_cost_usd"],
    "pass_rates": pass_rates,
    "per_quote_strict_rate": rate(sum(o["quotes_strict"] for o in row_out), qt),
    "per_quote_normalised_rate": rate(sum(o["quotes_normalised"] for o in row_out), qt),
    "quotes_total": qt,
    "scorer_error_rows": sum(1 for o in row_out if o["scorer_errors"]),
}
print(json.dumps(summary, indent=2, default=str))

# COMMAND ----------
# MAGIC %md ## 7. Write Delta tables (append, one run_id per execution) and log the summary to the MLflow run

# COMMAND ----------

import pandas as pd  # noqa: E402
from pyspark.sql.types import (BooleanType, DoubleType, IntegerType, LongType, StringType, StructField,  # noqa: E402
                               StructType, TimestampType)

res_schema = StructType([
    StructField("run_id", StringType()), StructField("run_ts", TimestampType()),
    StructField("mlflow_run_id", StringType()),
    StructField("FACILITY_ID", LongType()), StructField("PATIENT_CONTROL_NUMBER", LongType()),
    StructField("ENCOUNTER_NBR", LongType()), StructField("expected_determination", StringType()),
    StructField("predicted", StringType()), StructField("trace_id", StringType()),
    StructField("groundedness", StringType()), StructField("groundedness_rationale", StringType()),
    StructField("no_fabricated_evidence", StringType()), StructField("no_fabricated_evidence_rationale", StringType()),
    StructField("quote_verified_strict", StringType()), StructField("quote_verified_normalised", StringType()),
    StructField("quote_rationale", StringType()), StructField("quotes_total", IntegerType()),
    StructField("quotes_strict", IntegerType()), StructField("quotes_normalised", IntegerType()),
    StructField("determination_matches_label", StringType()), StructField("scorer_errors", IntegerType()),
    StructField("judge_model", StringType()),
])
res_pdf = pd.DataFrame(row_out)
res_pdf["run_ts"] = pd.to_datetime(res_pdf["run_ts"])
spark.createDataFrame(res_pdf.astype(object).where(res_pdf.notna(), None), res_schema) \
    .write.mode("append").saveAsTable(f"{FQ}.genai_eval_results")  # noqa: F821

sum_schema = StructType([
    StructField("run_id", StringType()), StructField("run_ts", TimestampType()),
    StructField("experiment_path", StringType()), StructField("mlflow_run_id", StringType()),
    StructField("rows_evaluated", IntegerType()), StructField("appeals_output_rows", IntegerType()),
    StructField("excluded_stale_grounding_rows", IntegerType()), StructField("max_rows", IntegerType()),
    StructField("judge_model", StringType()), StructField("trace_count", IntegerType()),
    StructField("estimated_judge_cost_usd", DoubleType()),
    StructField("groundedness_pass_rate", DoubleType()), StructField("no_fabricated_evidence_pass_rate", DoubleType()),
    StructField("quote_verified_strict_pass_rate", DoubleType()),
    StructField("quote_verified_normalised_pass_rate", DoubleType()),
    StructField("determination_matches_label_rate", DoubleType()),
    StructField("per_quote_strict_rate", DoubleType()), StructField("per_quote_normalised_rate", DoubleType()),
    StructField("scorer_error_rows", IntegerType()), StructField("pass_rates_json", StringType()),
])
pr = pass_rates
spark.createDataFrame([(
    RUN_ID, RUN_TS, EXPERIMENT, MLFLOW_RUN_ID, len(rows), total_outputs, stale, MAX_ROWS, JUDGE_MODEL,
    len(trace_ids), float(estimate["est_cost_usd"]),
    pr["groundedness"]["rate"], pr["no_fabricated_evidence"]["rate"], pr["quote_verified_strict"]["rate"],
    pr["quote_verified_normalised"]["rate"], pr["determination_matches_label"]["rate"],
    summary["per_quote_strict_rate"], summary["per_quote_normalised_rate"], summary["scorer_error_rows"],
    json.dumps(pass_rates),
)], sum_schema).write.mode("append").saveAsTable(f"{FQ}.genai_eval_summary")  # noqa: F821

from mlflow.tracking import MlflowClient  # noqa: E402

client = MlflowClient()
client.log_dict(MLFLOW_RUN_ID, summary, "genai_eval_summary.json")
client.set_tag(MLFLOW_RUN_ID, "fe_bar_eval_run_id", RUN_ID)
print("genai eval complete", RUN_ID, "mlflow run", MLFLOW_RUN_ID)
