# Databricks notebook source
# MAGIC %md
# MAGIC # 10_generate_raw_data: FE Bar synthetic caseload (job task, serverless)
# MAGIC
# MAGIC Lands one seeded synthetic batch into the UC volume `landing` and writes the eval ground truth to Delta.
# MAGIC The generator is the pure-Python package `generator/` in this repo (stdlib only).
# MAGIC
# MAGIC | Output | Where | Notes |
# MAGIC |---|---|---|
# MAGIC | claim-line JSON lines | `/Volumes/<catalog>/<schema>/landing/claims/batch_<as_of>_seed<seed>_n<n>.json` | Auto Loader source (`bronze_claims`) |
# MAGIC | clinical-note JSON lines | `/Volumes/<catalog>/<schema>/landing/clinical_notes/<same name>` | Auto Loader source (`bronze_clinical_notes`) |
# MAGIC | batch manifest (defects, plan) | `/Volumes/<catalog>/<schema>/landing/_manifests/<same name>` | not an Auto Loader source |
# MAGIC | `eval_case_labels` | Delta `<catalog>.<schema>.eval_case_labels` | never written to landing or the pipeline |
# MAGIC
# MAGIC **Idempotency and Auto Loader re-run behaviour**
# MAGIC - The file name is deterministic (`as_of` + `seed` + `n`). If the claims file already exists the batch is
# MAGIC   treated as landed and nothing is written (`skipped_exists`). The claims file is written last and is the commit
# MAGIC   marker, so a crashed run leaves no claims file and the next run lands the batch cleanly.
# MAGIC - Files are staged under `landing/_staging` and atomically renamed into place, so Auto Loader never reads a partial file.
# MAGIC - Auto Loader records processed file paths in its checkpoint. A skipped run adds no new file, so nothing is re-ingested.
# MAGIC   The notebook never overwrites a landed file in place: an in-place rewrite would be silently ignored by Auto Loader.
# MAGIC - A re-run with the same seed + as_of + n is a no-op for the files. The labels table is rewritten for that seed + as_of
# MAGIC   (delete then insert of identical rows), so repeated runs leave it unchanged.
# MAGIC - A re-run for a **new** as_of (or seed/n) lands a new batch. The pipeline keeps the latest `_ingested_at` per natural
# MAGIC   key, so overlapping keys are replaced rather than duplicated. Keys that exist only in an older batch remain.
# MAGIC   Use a full refresh of the SDP pipeline for a clean reset.

# COMMAND ----------
import json
import os
import re
import sys
from datetime import date

# COMMAND ----------
def _param(name, default):
    """Job base_parameters / widgets with a local default for interactive runs."""
    try:
        dbutils.widgets.text(name, default)  # noqa: F821 (provided by the Databricks runtime)
        return dbutils.widgets.get(name)  # noqa: F821
    except NameError:
        return default


CATALOG = _param("catalog", "appeals_hackathon_catalog")
SCHEMA = _param("schema", "fe_bar_appeals")
SEED = int(_param("seed", "20261124"))
N_ENCOUNTERS = int(_param("n_encounters", "500"))
AS_OF_RAW = (_param("as_of_date", "") or "").strip()
AS_OF = date.fromisoformat(AS_OF_RAW) if AS_OF_RAW else date.today()

for _name, _val in (("catalog", CATALOG), ("schema", SCHEMA)):
    if not re.fullmatch(r"[A-Za-z0-9_]+", _val):
        raise ValueError(f"{_name} must be a plain identifier, got {_val!r}")
if N_ENCOUNTERS < 1:
    raise ValueError("n_encounters must be >= 1")

# COMMAND ----------
def _repo_root():
    """Bundle sync puts this notebook at <root>/pipeline/10_generate_raw_data; the package is <root>/generator."""
    try:
        nb_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()  # noqa: F821
        return "/Workspace" + os.path.dirname(os.path.dirname(nb_path))
    except Exception:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # local/IDE fallback


REPO_ROOT = _repo_root()
if not os.path.isdir(os.path.join(REPO_ROOT, "generator")):
    raise FileNotFoundError(f"generator package not found under {REPO_ROOT}; check the bundle sync root")
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from generator import generate, write_landing  # noqa: E402

print("repo root:", REPO_ROOT)

# COMMAND ----------
# MAGIC %md ## 1. Generate the batch (pure Python, deterministic for seed + as_of)

# COMMAND ----------
batch = generate(seed=SEED, n_encounters=N_ENCOUNTERS, as_of_date=AS_OF)
print("source_batch:", batch.source_batch)
print("claim lines (incl. injected defects):", len(batch.claims), "| notes:", len(batch.notes))
print("label counts:", batch.manifest["label_counts"], "| injected defects:", len(batch.manifest["defects"]))

# COMMAND ----------
# MAGIC %md ## 2. Land the JSON-lines files (idempotent)

# COMMAND ----------
LANDING = f"/Volumes/{CATALOG}/{SCHEMA}/landing"
landing_result = write_landing(batch, LANDING)
print(json.dumps(landing_result, indent=2))

# COMMAND ----------
# MAGIC %md ## 3. Write eval_case_labels to Delta (overwrite for this seed + as_of only)
# MAGIC Labels are ground truth. They are never landed and never read by the pipeline or the model.

# COMMAND ----------
TBL = f"{CATALOG}.{SCHEMA}.eval_case_labels"
spark.sql(f"""
  CREATE TABLE IF NOT EXISTS {TBL} (
    FACILITY_ID BIGINT, PATIENT_CONTROL_NUMBER BIGINT, ENCOUNTER_NBR BIGINT,
    expected_determination STRING, scenario STRING, is_hero BOOLEAN,
    generator_seed INT, as_of_date DATE
  ) COMMENT 'Eval ground truth from the synthetic generator (seeded). Never used as model input.'
""")
spark.sql(
    f"DELETE FROM {TBL} WHERE generator_seed = :seed AND as_of_date = CAST(:as_of AS DATE)",
    args={"seed": SEED, "as_of": AS_OF.isoformat()},
)
label_rows = [
    {
        "FACILITY_ID": int(r["FACILITY_ID"]),
        "PATIENT_CONTROL_NUMBER": int(r["PATIENT_CONTROL_NUMBER"]),
        "ENCOUNTER_NBR": int(r["ENCOUNTER_NBR"]),
        "expected_determination": r["expected_determination"],
        "scenario": r["scenario"],
        "is_hero": bool(r["is_hero"]),
        "generator_seed": int(r["generator_seed"]),
        "as_of_date": AS_OF,
    }
    for r in batch.labels
]
from pyspark.sql.types import (  # noqa: E402
    BooleanType, DateType, IntegerType, LongType, StringType, StructField, StructType,
)
label_schema = StructType([
    StructField("FACILITY_ID", LongType(), False),
    StructField("PATIENT_CONTROL_NUMBER", LongType(), False),
    StructField("ENCOUNTER_NBR", LongType(), False),
    StructField("expected_determination", StringType(), False),
    StructField("scenario", StringType(), False),
    StructField("is_hero", BooleanType(), False),
    StructField("generator_seed", IntegerType(), False),
    StructField("as_of_date", DateType(), False),
])
spark.createDataFrame(label_rows, schema=label_schema).write.mode("append").saveAsTable(TBL)
print(f"eval_case_labels: wrote {len(label_rows)} rows for seed={SEED} as_of={AS_OF.isoformat()}")

# COMMAND ----------
summary = {
    "source_batch": batch.source_batch,
    "landing_status": landing_result["status"],
    "claims_file": landing_result["claims_file"],
    "notes_file": landing_result["notes_file"],
    "n_encounters": N_ENCOUNTERS,
    "n_claim_lines_total": len(batch.claims),
    "n_notes": len(batch.notes),
    "label_counts": batch.manifest["label_counts"],
    "defects": len(batch.manifest["defects"]),
    "eval_case_labels_rows": len(label_rows),
}
print(json.dumps(summary, indent=2))
