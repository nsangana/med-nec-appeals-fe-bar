# Databricks notebook source
# MAGIC %md
# MAGIC # 60_evaluate — score appeals_output against eval_case_labels
# MAGIC
# MAGIC `eval_case_labels` (ground truth from the generator) is joined HERE ONLY. It is never fed to the model.
# MAGIC
# MAGIC Writes (append, one run_id per execution):
# MAGIC - `eval_results`: one row per evaluated encounter (expected, predicted, correct, unsafe flag, quote check)
# MAGIC - `eval_summary`: accuracy, per-class precision/recall, confusion matrix (JSON), `unsafe_rate`,
# MAGIC   `quote_verified_rate`, coverage, run_id, timestamp
# MAGIC
# MAGIC Definitions
# MAGIC - `unsafe_rate` = encounters predicted WARRANTED where expected is not WARRANTED, divided by all evaluated encounters.
# MAGIC - `quote_verified_rate` (METRIC ONLY, never changes a determination) = share of quoted spans (>= 20 chars, in double
# MAGIC   quotes on ONE line) in the letter or AI worksheet that appear verbatim (whitespace-normalised) in the grounding inputs.
# MAGIC   `quote_verified_rate_normalised` is a diagnostic only: same check, ignoring punctuation/case and splitting on
# MAGIC   ellipses. The gap between the two is mostly PDF extraction artifacts and paraphrase; it is reported, not hidden.

# COMMAND ----------

import json
import re
import uuid
from datetime import datetime, timezone

import mlflow
from pyspark.sql import functions as F

def _param(name, default):
    """Job base_parameters / widgets with a local default for interactive runs."""
    try:
        dbutils.widgets.text(name, default)  # noqa: F821 (provided by the Databricks runtime)
        return dbutils.widgets.get(name)  # noqa: F821
    except NameError:
        return default

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
CLASSES = ["WARRANTED", "NOT WARRANTED", "NEEDS REVIEW"]
MLFLOW_EXPERIMENT = "/Shared/fe-bar-appeals-eval"  # shared path: no personal user folder in the repo
RUN_ID = str(uuid.uuid4())
RUN_TS = datetime.now(timezone.utc).isoformat()

# COMMAND ----------
# MAGIC %md ## 1. Join predictions to labels

# COMMAND ----------

joined = spark.sql(f"""
    SELECT o.FACILITY_ID, o.PATIENT_CONTROL_NUMBER, o.ENCOUNTER_NBR,
           l.expected_determination, l.scenario, l.is_hero,
           o.recommendation AS predicted, o.needs_review_reason, o.cheat_sheet, o.appeal_letter,
           g.reason_text, g.notes_full, g.criteria_block, g.mpfs_context, g.hcpcs_codes, g.dx_codes,
           g.patient_name, g.payer_name, g.what_to_prove
    FROM {FQ}.appeals_output o
    -- eval_case_labels keeps one batch per (seed, as_of). Keys repeat across batches, so join only the latest
    -- label per encounter; otherwise a re-run with a new as_of would double-count every evaluated case.
    JOIN (
      SELECT * FROM {FQ}.eval_case_labels
      QUALIFY row_number() OVER (PARTITION BY FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR
                                 ORDER BY as_of_date DESC, generator_seed DESC) = 1
    ) l
      ON l.FACILITY_ID = o.FACILITY_ID AND l.PATIENT_CONTROL_NUMBER = o.PATIENT_CONTROL_NUMBER AND l.ENCOUNTER_NBR = o.ENCOUNTER_NBR
    LEFT JOIN {FQ}.encounter_grounding g
      ON g.FACILITY_ID = o.FACILITY_ID AND g.PATIENT_CONTROL_NUMBER = o.PATIENT_CONTROL_NUMBER AND g.ENCOUNTER_NBR = o.ENCOUNTER_NBR
""")
rows = [r.asDict() for r in joined.collect()]
total_outputs = spark.sql(f"SELECT count(*) n FROM {FQ}.appeals_output").first().n
print(f"evaluated {len(rows)} encounters (appeals_output rows: {total_outputs})")

# COMMAND ----------
# MAGIC %md ## 2. Quote verification (metric only)

# COMMAND ----------

QUOTE_RE = re.compile(r'"([^"\n]{20,})"')  # single-line only: pairing across lines produced false spans


def norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def alnum(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def quote_check(r):
    """Return (quotes_total, verified_strict, verified_normalised) for the letter and AI worksheet text."""
    ground = norm(" ".join(str(r.get(k) or "") for k in (
        "notes_full", "criteria_block", "mpfs_context", "reason_text", "what_to_prove",
        "hcpcs_codes", "dx_codes", "patient_name", "payer_name")))
    text = (r.get("appeal_letter") or "") + "\n" + (r.get("cheat_sheet") or "")
    raw = [m for m in QUOTE_RE.findall(text) if len(norm(m)) >= 20]
    strict = sum(1 for m in raw if norm(m) in ground)
    ground_al = alnum(ground)
    norm_ok = 0
    for m in raw:
        frags = [f for f in re.split(r"\.\.\.|\u2026", m) if len(alnum(f)) >= 12]
        if frags and all(alnum(f) in ground_al for f in frags):
            norm_ok += 1
    return len(raw), strict, norm_ok


for r in rows:
    r["quotes_total"], r["quotes_verified"], r["quotes_verified_normalised"] = quote_check(r)

# COMMAND ----------
# MAGIC %md ## 3. Metrics

# COMMAND ----------

n = len(rows)
correct = [r for r in rows if r["predicted"] == r["expected_determination"]]
unsafe = [r for r in rows if r["predicted"] == "WARRANTED" and r["expected_determination"] != "WARRANTED"]
parse_failures = [r for r in rows if (r["needs_review_reason"] or "").startswith("PARSE_FAILURE")]

per_class = {}
for c in CLASSES:
    tp = sum(1 for r in rows if r["predicted"] == c and r["expected_determination"] == c)
    fp = sum(1 for r in rows if r["predicted"] == c and r["expected_determination"] != c)
    fn = sum(1 for r in rows if r["predicted"] != c and r["expected_determination"] == c)
    per_class[c] = {
        "precision": round(tp / (tp + fp), 4) if tp + fp else None,
        "recall": round(tp / (tp + fn), 4) if tp + fn else None,
        "support": tp + fn,
    }

confusion = {e: {p: 0 for p in CLASSES} for e in CLASSES}
for r in rows:
    if r["expected_determination"] in confusion and r["predicted"] in confusion[r["expected_determination"]]:
        confusion[r["expected_determination"]][r["predicted"]] += 1

qt = sum(r["quotes_total"] for r in rows)
qv = sum(r["quotes_verified"] for r in rows)
qvn = sum(r["quotes_verified_normalised"] for r in rows)
summary = {
    "run_id": RUN_ID,
    "run_ts_utc": RUN_TS,
    "encounters_evaluated": n,
    "appeals_output_rows": total_outputs,
    "coverage": round(n / total_outputs, 4) if total_outputs else None,
    "accuracy": round(len(correct) / n, 4) if n else None,
    "per_class": per_class,
    "confusion_matrix": confusion,
    "unsafe_rate": round(len(unsafe) / n, 4) if n else None,
    "unsafe_encounters": [f"{r['FACILITY_ID']}_{r['PATIENT_CONTROL_NUMBER']}_{r['ENCOUNTER_NBR']}" for r in unsafe],
    "parse_failures": len(parse_failures),
    "quotes_total": qt,
    "quotes_verified": qv,
    "quote_verified_rate": round(qv / qt, 4) if qt else None,
    "quote_verified_rate_normalised": round(qvn / qt, 4) if qt else None,
}
print(json.dumps(summary, indent=2))

# COMMAND ----------
# MAGIC %md ## 4. Write eval_results + eval_summary (append; history per run_id)

# COMMAND ----------

from pyspark.sql.types import (BooleanType, DoubleType, IntegerType, LongType, StringType, StructField,
                               StructType, TimestampType)

res_schema = StructType([
    StructField("run_id", StringType()), StructField("run_ts", TimestampType()),
    StructField("FACILITY_ID", LongType()), StructField("PATIENT_CONTROL_NUMBER", LongType()), StructField("ENCOUNTER_NBR", LongType()),
    StructField("scenario", StringType()), StructField("is_hero", BooleanType()),
    StructField("expected_determination", StringType()), StructField("predicted", StringType()),
    StructField("correct", BooleanType()), StructField("unsafe", BooleanType()),
    StructField("parse_failure", BooleanType()), StructField("quotes_total", IntegerType()),
    StructField("quotes_verified", IntegerType()), StructField("quotes_verified_normalised", IntegerType()),
])
now = datetime.now(timezone.utc)
res_rows = [(RUN_ID, now, r["FACILITY_ID"], r["PATIENT_CONTROL_NUMBER"], r["ENCOUNTER_NBR"], r["scenario"],
             bool(r["is_hero"]), r["expected_determination"], r["predicted"],
             r["predicted"] == r["expected_determination"],
             r["predicted"] == "WARRANTED" and r["expected_determination"] != "WARRANTED",
             (r["needs_review_reason"] or "").startswith("PARSE_FAILURE"),
             r["quotes_total"], r["quotes_verified"], r["quotes_verified_normalised"]) for r in rows]
if res_rows:
    spark.createDataFrame(res_rows, res_schema).write.mode("append").saveAsTable(f"{FQ}.eval_results")

sum_schema = StructType([
    StructField("run_id", StringType()), StructField("run_ts", TimestampType()),
    StructField("encounters_evaluated", IntegerType()), StructField("appeals_output_rows", IntegerType()),
    StructField("coverage", DoubleType()), StructField("accuracy", DoubleType()),
    StructField("unsafe_rate", DoubleType()), StructField("quote_verified_rate", DoubleType()),
    StructField("quote_verified_rate_normalised", DoubleType()),
    StructField("parse_failures", IntegerType()), StructField("per_class_json", StringType()),
    StructField("confusion_matrix_json", StringType()), StructField("unsafe_encounters_json", StringType()),
])
spark.createDataFrame([(RUN_ID, now, n, total_outputs, summary["coverage"], summary["accuracy"],
                        summary["unsafe_rate"], summary["quote_verified_rate"],
                        summary["quote_verified_rate_normalised"], len(parse_failures),
                        json.dumps(per_class), json.dumps(confusion), json.dumps(summary["unsafe_encounters"]))],
                      sum_schema).write.mode("append").saveAsTable(f"{FQ}.eval_summary")

# COMMAND ----------
# MAGIC %md ## 5. Log to MLflow (lightweight; the groundedness scorers are P1 and not run here)

# COMMAND ----------

mlflow.set_experiment(MLFLOW_EXPERIMENT)
with mlflow.start_run(run_name=f"eval-{RUN_ID[:8]}"):
    mlflow.log_params({"run_id": RUN_ID, "encounters_evaluated": n})
    metrics = {"accuracy": summary["accuracy"] or 0.0, "unsafe_rate": summary["unsafe_rate"] or 0.0,
               "quote_verified_rate": summary["quote_verified_rate"] or 0.0,
               "parse_failures": float(len(parse_failures)), "coverage": summary["coverage"] or 0.0}
    for c in CLASSES:
        if per_class[c]["precision"] is not None:
            metrics[f"precision_{c.replace(' ', '_').lower()}"] = per_class[c]["precision"]
        if per_class[c]["recall"] is not None:
            metrics[f"recall_{c.replace(' ', '_').lower()}"] = per_class[c]["recall"]
    mlflow.log_metrics(metrics)
    mlflow.log_dict(summary, "eval_summary.json")
print("eval complete", RUN_ID)
