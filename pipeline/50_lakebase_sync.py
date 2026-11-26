# Databricks notebook source
# MAGIC %md
# MAGIC # 50 — Lakebase sync (FE Bar)
# MAGIC 1. MERGE `gold_denial_worklist` LEFT JOIN `appeals_output` into Delta `worklist_serving` (CDF on, PK set).
# MAGIC 2. Trigger a refresh of the Lakebase synced table `fe_bar_appeals_lakebase.fe_bar_appeals.worklist_serving`.
# MAGIC 3. Copy Lakebase `review_state` into Delta `review_state_uc` (reviewer state back to UC for Genie).
# MAGIC
# MAGIC Job parameters (notebook widgets): `catalog`, `schema` (validated plain identifiers) and
# MAGIC `enable_lakebase_sync` ("true" | "false").
# MAGIC - `true` (default, live behaviour): steps 1-3 run.
# MAGIC - `false`: step 1 still runs (MERGE into the Delta table `worklist_serving`, no Lakebase dependency);
# MAGIC   the synced-table refresh (step 2) and the Lakebase review_state copy (step 3) are SKIPPED with a printed
# MAGIC   message. `review_state_uc` keeps its last copied content. Use this to run the pipeline without Lakebase
# MAGIC   compute, for example the smoke target.
# MAGIC
# MAGIC Idempotent: safe to re-run. Synthetic data only. Job task on serverless compute.

# COMMAND ----------
import re


def _param(name, default):
    """Job base_parameters / widgets with a local default for interactive runs."""
    try:
        dbutils.widgets.text(name, default)  # noqa: F821 (provided by the Databricks runtime)
        return dbutils.widgets.get(name)  # noqa: F821
    except NameError:
        return default


CATALOG_DEFAULT = "appeals_hackathon_catalog"  # live value; the job passes the bundle target's catalog
SCHEMA_DEFAULT = "fe_bar_appeals"  # live value; the job passes the bundle target's schema
CAT = _param("catalog", CATALOG_DEFAULT).strip()
SCH = _param("schema", SCHEMA_DEFAULT).strip()
for _name, _val in (("catalog", CAT), ("schema", SCH)):
    # Object names are built from these two values only: plain identifiers, nothing user-supplied in SQL text.
    if not re.fullmatch(r"[A-Za-z0-9_]+", _val):
        raise ValueError(f"{_name} must be a plain identifier, got {_val!r}")

ENABLE_LAKEBASE_SYNC_RAW = _param("enable_lakebase_sync", "true").strip().lower()
if ENABLE_LAKEBASE_SYNC_RAW not in ("true", "false"):
    raise ValueError(f"enable_lakebase_sync must be 'true' or 'false', got {ENABLE_LAKEBASE_SYNC_RAW!r}")
ENABLE_LAKEBASE_SYNC = ENABLE_LAKEBASE_SYNC_RAW == "true"
print(f"enable_lakebase_sync={ENABLE_LAKEBASE_SYNC}")

# Lakebase UC catalog (the registered catalog of the Lakebase project). Not a per-build catalog, so not a parameter.
# The synced table and the review_state table live under it in schema SCH, so SCH must match the synced table's schema
# whenever enable_lakebase_sync is true.
LAKEBASE_CATALOG = "fe_bar_appeals_lakebase"

GOLD = f"{CAT}.{SCH}.gold_denial_worklist"
APPEALS = f"{CAT}.{SCH}.appeals_output"
DATA_SHEET = f"{CAT}.{SCH}.data_sheet_facts"  # deterministic data sheet (no LLM); one row per grounded encounter
SERVING = f"{CAT}.{SCH}.worklist_serving"
SYNCED_NAME = f"{LAKEBASE_CATALOG}.{SCH}.worklist_serving"  # UC name of the synced table (Lakebase catalog)
REVIEW_STATE_LB = f"{LAKEBASE_CATALOG}.public.review_state"
REVIEW_STATE_UC = f"{CAT}.{SCH}.review_state_uc"
KEYS = ["FACILITY_ID", "PATIENT_CONTROL_NUMBER", "ENCOUNTER_NBR"]

# Columns pulled from appeals_output (Agent B schema). Keys are joined; rn de-dupes to the latest generation.
OUT_COLS = ["recommendation", "needs_review_reason", "cheat_sheet", "appeal_letter",
            "letter_pdf_path", "cheat_sheet_pdf_path", "generated_at"]

ON = " AND ".join(f"t.{k} = s.{k}" for k in KEYS)
SOURCE_SQL = f"""
WITH o AS (
  SELECT {", ".join(KEYS)}, {", ".join(OUT_COLS)},
         ROW_NUMBER() OVER (PARTITION BY {", ".join(KEYS)} ORDER BY generated_at DESC) AS rn
  FROM {APPEALS}
)
SELECT g.*, {", ".join("o." + c for c in OUT_COLS)}, d.data_sheet_pdf_path
FROM {GOLD} g
LEFT JOIN (SELECT {", ".join(KEYS + OUT_COLS)} FROM o WHERE rn = 1) o USING ({", ".join(KEYS)})
LEFT JOIN (SELECT {", ".join(KEYS)}, data_sheet_pdf_path FROM {DATA_SHEET}) d USING ({", ".join(KEYS)})
"""

# COMMAND ----------

# 1a. Create the serving table once with the gold + appeals_output schema (no rows), CDF on.
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {SERVING}
TBLPROPERTIES (delta.enableChangeDataFeed = true)
AS SELECT * FROM ({SOURCE_SQL}) WHERE 1 = 0
""")

# 1b. Primary key (required by synced tables). Idempotent.
for k in KEYS:
    spark.sql(f"ALTER TABLE {SERVING} ALTER COLUMN {k} SET NOT NULL")
pk_exists = spark.sql(f"""
SELECT 1 FROM {CAT}.information_schema.table_constraints
WHERE table_schema = :schema_name AND table_name = 'worklist_serving' AND constraint_type = 'PRIMARY KEY'
""", args={"schema_name": SCH}).count() > 0
if not pk_exists:
    spark.sql(f"ALTER TABLE {SERVING} ADD CONSTRAINT worklist_serving_pk PRIMARY KEY ({', '.join(KEYS)})")

# 1c. MERGE: upsert every gold row with its latest appeal output; drop rows no longer in gold.
#     WITH SCHEMA EVOLUTION adds new source columns (e.g. data_sheet_pdf_path) to an existing serving table;
#     synced tables accept additive schema changes on the next triggered refresh.
spark.sql(f"""
MERGE WITH SCHEMA EVOLUTION INTO {SERVING} t
USING ({SOURCE_SQL}) s
ON {ON}
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE THEN DELETE
""")
serving_rows = spark.table(SERVING).count()
print(f"worklist_serving rows: {serving_rows}")

# COMMAND ----------

# 2. Trigger the synced-table refresh (TRIGGERED policy) and wait for it to finish.
#    A TRIGGERED synced table refreshes by starting an update on its sync pipeline (pipeline_id in status).
import time
from databricks.sdk import WorkspaceClient

def trigger_synced_refresh(timeout_s=1800):
    w = WorkspaceClient()
    st = w.api_client.do("GET", f"/api/2.0/postgres/synced_tables/{SYNCED_NAME}")
    pipeline_id = st["status"]["pipeline_id"]
    update_id = w.pipelines.start_update(pipeline_id=pipeline_id).update_id
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        state = w.pipelines.get_update(pipeline_id=pipeline_id, update_id=update_id).update.state.value
        if state in ("COMPLETED", "FAILED", "CANCELED"):
            if state != "COMPLETED":
                raise RuntimeError(f"synced table refresh {update_id} ended in {state}")
            print(f"synced table refresh COMPLETED (pipeline {pipeline_id}, update {update_id})")
            return
        time.sleep(15)
    raise TimeoutError(f"synced table refresh {update_id} still running after {timeout_s}s")

if ENABLE_LAKEBASE_SYNC:
    trigger_synced_refresh()
else:
    print("enable_lakebase_sync=false: SKIPPED the synced-table refresh (Lakebase). worklist_serving was still merged.")

# COMMAND ----------

# 3. Copy Lakebase review_state into Delta (reviewer state back to UC). Runs via the registered UC catalog.
if ENABLE_LAKEBASE_SYNC:
    spark.sql(f"""
    CREATE OR REPLACE TABLE {REVIEW_STATE_UC}
    COMMENT 'SIMULATED reviewer state copied from Lakebase review_state ({LAKEBASE_CATALOG})'
    AS SELECT *, current_timestamp() AS copied_at FROM {REVIEW_STATE_LB}
    """)
    print(f"review_state_uc rows: {spark.table(REVIEW_STATE_UC).count()}")
else:
    # Flag off: no copy, but the metric view and the Genie space read review_state_uc, so it must exist.
    # IF NOT EXISTS creates an EMPTY placeholder with the same columns only when the table is missing; an existing
    # table (live) is left as it was.
    spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {REVIEW_STATE_UC} (
      facility_id BIGINT, patient_control_number BIGINT, encounter_nbr BIGINT, status STRING,
      last_reviewer STRING, last_action_at TIMESTAMP, submitted_at TIMESTAMP, deadline_met BOOLEAN,
      copied_at TIMESTAMP
    ) COMMENT 'Reviewer state copied from Lakebase. EMPTY placeholder when enable_lakebase_sync=false.'
    """)
    print("enable_lakebase_sync=false: SKIPPED the Lakebase review_state copy. review_state_uc left as it was "
          "(created empty if missing).")
