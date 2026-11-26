# Databricks notebook source
# MAGIC %md
# MAGIC # 50 — Lakebase sync (FE Bar)
# MAGIC 1. MERGE `gold_denial_worklist` LEFT JOIN `appeals_output` into Delta `worklist_serving` (CDF on, PK set).
# MAGIC 2. Trigger a refresh of the Lakebase synced table `fe_bar_appeals_lakebase.fe_bar_appeals.worklist_serving`.
# MAGIC 3. Copy Lakebase `review_state` into Delta `review_state_uc` (reviewer state back to UC for Genie).
# MAGIC
# MAGIC Idempotent: safe to re-run. Synthetic data only. Job task on serverless compute.

# COMMAND ----------

CAT = "appeals_hackathon_catalog"
SCH = "fe_bar_appeals"
GOLD = f"{CAT}.{SCH}.gold_denial_worklist"
APPEALS = f"{CAT}.{SCH}.appeals_output"
DATA_SHEET = f"{CAT}.{SCH}.data_sheet_facts"  # deterministic data sheet (no LLM); one row per grounded encounter
SERVING = f"{CAT}.{SCH}.worklist_serving"
SYNCED_NAME = f"fe_bar_appeals_lakebase.{SCH}.worklist_serving"  # UC name of the synced table (Lakebase catalog)
REVIEW_STATE_LB = "fe_bar_appeals_lakebase.public.review_state"
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
WHERE table_schema = '{SCH}' AND table_name = 'worklist_serving' AND constraint_type = 'PRIMARY KEY'
""").count() > 0
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

trigger_synced_refresh()

# COMMAND ----------

# 3. Copy Lakebase review_state into Delta (reviewer state back to UC). Runs via the registered UC catalog.
spark.sql(f"""
CREATE OR REPLACE TABLE {REVIEW_STATE_UC}
COMMENT 'SIMULATED reviewer state copied from Lakebase review_state (fe_bar_appeals_lakebase)'
AS SELECT *, current_timestamp() AS copied_at FROM {REVIEW_STATE_LB}
""")
print(f"review_state_uc rows: {spark.table(REVIEW_STATE_UC).count()}")
