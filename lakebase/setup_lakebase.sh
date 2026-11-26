#!/usr/bin/env bash
# Idempotent setup for the FE Bar Lakebase Autoscaling project (Agent C).
# Creates: project fe-bar-appeals-lakebase (0.5 CU fixed, autosuspend 300s), database `appeals`,
# then applies lakebase/ddl.sql. Safe to re-run. No secrets are written to disk.
set -euo pipefail
export DATABRICKS_AUTH_STORAGE=plaintext
PROFILE="${FEBAR_PROFILE:-fevm-appeals-hackathon}"
PROJECT="fe-bar-appeals-lakebase"
BRANCH="production"
DB_ID="appeals"
DIR="$(cd "$(dirname "$0")" && pwd)"
BR="projects/$PROJECT/branches/$BRANCH"

db() { databricks --profile "$PROFILE" "$@"; }

# 1. Project (skip if exists)
if ! db postgres get-project "projects/$PROJECT" -o json >/dev/null 2>&1; then
  cat > /tmp/fe_bar_proj.$$.json <<JSON
{"spec": {"display_name": "$PROJECT", "pg_version": 17,
  "default_endpoint_settings": {"autoscaling_limit_min_cu": 0.5, "autoscaling_limit_max_cu": 0.5, "suspend_timeout_duration": "300s"}}}
JSON
  db postgres create-project "$PROJECT" --json @/tmp/fe_bar_proj.$$.json -o json >/dev/null
  rm -f /tmp/fe_bar_proj.$$.json
  echo "created project $PROJECT"
else
  echo "project $PROJECT exists"
fi

# 2. Database `appeals` on production branch (skip if exists); owner = the CLI user's Postgres role
ROLE_ID="$(db postgres list-databases "$BR" -o json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d[0]['status']['role'])")"
if ! db postgres get-database "$BR/databases/$DB_ID" -o json >/dev/null 2>&1; then
  db postgres create-database "$BR" --database-id "$DB_ID" \
    --json "{\"spec\": {\"postgres_database\": \"$DB_ID\", \"role\": \"$ROLE_ID\"}}" -o json >/dev/null
  echo "created database $DB_ID"
else
  echo "database $DB_ID exists"
fi

# 3. DDL (idempotent: IF NOT EXISTS / CREATE OR REPLACE)
EP="$BR/endpoints/primary"
HOST="$(db postgres get-endpoint "$EP" -o json | python3 -c "import json,sys; print(json.load(sys.stdin)['status']['hosts']['host'])")"
USER_NAME="$(db current-user me -o json | python3 -c "import json,sys; print(json.load(sys.stdin)['userName'])")"
TOKEN="$(db postgres generate-database-credential "$EP" -o json | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")"
PGPASSWORD="$TOKEN" psql "host=$HOST port=5432 dbname=$DB_ID user=$USER_NAME sslmode=require" -v ON_ERROR_STOP=1 -f "$DIR/ddl.sql"
echo "DDL applied to $DB_ID on $HOST"

# 4. review_state view needs the synced worklist table (applied only once it exists)
if PGPASSWORD="$TOKEN" psql "host=$HOST port=5432 dbname=$DB_ID user=$USER_NAME sslmode=require" -tAc "SELECT to_regclass('fe_bar_appeals.worklist_serving') IS NOT NULL" | grep -q t; then
  PGPASSWORD="$TOKEN" psql "host=$HOST port=5432 dbname=$DB_ID user=$USER_NAME sslmode=require" -v ON_ERROR_STOP=1 -f "$DIR/ddl_review_state.sql"
  echo "review_state view applied"
else
  echo "fe_bar_appeals.worklist_serving not yet synced; review_state view deferred"
fi
