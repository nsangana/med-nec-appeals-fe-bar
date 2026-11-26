#!/usr/bin/env bash
# Creates the Lakebase synced table fe_bar_appeals.worklist_serving (TRIGGERED, snapshot-style refresh from Delta).
# Idempotent: exits 0 if it already exists. Requires the Delta source worklist_serving (run 50_lakebase_sync.py once first).
set -euo pipefail
export DATABRICKS_AUTH_STORAGE=plaintext
PROFILE="${FEBAR_PROFILE:-fevm-appeals-hackathon}"
SRC="appeals_hackathon_catalog.fe_bar_appeals.worklist_serving"
DST="fe_bar_appeals_lakebase.fe_bar_appeals.worklist_serving"   # UC name; Postgres table = fe_bar_appeals.worklist_serving
BR="projects/fe-bar-appeals-lakebase/branches/production"
STORAGE_CATALOG="${FEBAR_STORAGE_CATALOG:-appeals_hackathon_catalog}"  # must be a regular UC catalog (not the Lakebase one)

if databricks --profile "$PROFILE" postgres get-synced-table "synced_tables/$DST" -o json >/dev/null 2>&1; then
  echo "synced table $DST exists"; exit 0
fi
cat > /tmp/fe_bar_synced.$$.json <<JSON
{"spec": {
  "source_table_full_name": "$SRC",
  "primary_key_columns": ["FACILITY_ID", "PATIENT_CONTROL_NUMBER", "ENCOUNTER_NBR"],
  "scheduling_policy": "TRIGGERED",
  "branch": "$BR",
  "postgres_database": "appeals",
  "create_database_objects_if_missing": true,
  "new_pipeline_spec": {"storage_catalog": "$STORAGE_CATALOG", "storage_schema": "fe_bar_appeals"}
}}
JSON
databricks --profile "$PROFILE" postgres create-synced-table "$DST" --json @/tmp/fe_bar_synced.$$.json -o json
rm -f /tmp/fe_bar_synced.$$.json
