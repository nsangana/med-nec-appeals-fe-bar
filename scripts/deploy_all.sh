#!/usr/bin/env bash
# FE Bar medical-necessity appeals: single idempotent runbook, from a clean checkout.
#
# Targets (-t, default: default):
#   default  the live build. Runs every step below.
#   smoke    test deploy in schema fe_bar_appeals_test (names fe-bar-appeals-smoke-*). The bundle deploys only the
#            schema, volumes, SDP pipeline, job, dashboard and Genie space. Steps 3-4 run the smoke job; the Lakebase,
#            chat agent, app, grant steps and the SQL that hard-codes the live schema (governance, metric view) are skipped.
#
# Order (each step is safe to re-run on a warm workspace):
#   1  render dashboard + Genie JSON for the target (scripts/render_configs.py -> build/<target>/)
#   2  bundle validate + bundle deploy   (schema, volumes, SDP pipeline, job, dashboard, Genie space; default also
#                                         Lakebase project/branch/endpoint/db/synced table, UC model + VS index, chat endpoint)
#   3  Lakebase DDL (lakebase/setup_lakebase.sh)                                    [default only]
#   4  data layer: bundle run fe_bar_appeals_job   (creates the tables that the later steps read; includes cost_views)
#   5  Lakebase synced table (create_synced_table.sh), then setup again for the review_state view   [default only]
#   6  governance 01 (PHI tags) and 05 (column masks)                               [default only: SQL hard-codes the live schema]
#   7  Genie metric view (genie/00 + genie/01), then redeploy so the bundle Genie space sees it   [default only, same reason]
#   8  chat agent: agent/build_and_deploy.py as a one-time serverless run (agents.deploy creates the endpoint)  [default only]
#   9  app: workspace import, apps create/update (resources + scopes), apps deploy   [default only]
#   10 governance 04 (app SP SELECT on the 5 Genie objects)                          [default only]
#   11 final bundle plan (must show no deletes/recreates for default)
#
# NOT run here: governance/02_reviewer_grants.sql (needs an account-level group).
# Clean-workspace caveat (default): the chat endpoint is a bundle resource and needs agent version 2 registered, so the
# first deploy (step 2) can fail on that one resource. The runbook warns and continues; the second deploy creates it.
#
# Usage:
#   scripts/deploy_all.sh [-t default|smoke] --dry-run   print every step, run nothing that changes state
#   scripts/deploy_all.sh [-t default|smoke]             run the steps (asks no questions; stops on the first real error)
# Env: FEBAR_PROFILE (default fevm-appeals-hackathon), FEBAR_WAREHOUSE (default 559faf81d610a2a1).
# CATALOG and the per-target SCHEMA below must match variables in databricks.yml.
set -euo pipefail

DRY_RUN=0
TARGET="default"
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    -t|--target) TARGET="${2:?-t needs a target: default or smoke}"; shift 2 ;;
    -h|--help) sed -n '2,31p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1 (use -t default|smoke, --dry-run or -h)" >&2; exit 2 ;;
  esac
done

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE="${FEBAR_PROFILE:-fevm-appeals-hackathon}"
WAREHOUSE="${FEBAR_WAREHOUSE:-559faf81d610a2a1}"
CATALOG="appeals_hackathon_catalog"
case "$TARGET" in
  default) SCHEMA="fe_bar_appeals"; FULL=1 ;;
  smoke)   SCHEMA="fe_bar_appeals_test"; FULL=0 ;;
  *) echo "unknown target: $TARGET (default or smoke)" >&2; exit 2 ;;
esac
APP="fe-bar-appeals-app"
JOB="fe_bar_appeals_job"
export DATABRICKS_AUTH_STORAGE=plaintext
export FEBAR_PROFILE="$PROFILE"
export FEBAR_WAREHOUSE="$WAREHOUSE"

cd "$REPO"

step() { printf '\n== %s\n' "$*"; }
info() { printf '   %s\n' "$*"; }
skip() { printf '   SKIPPED for target %s: %s\n' "$TARGET" "$*"; }
# run: print the command; execute it unless --dry-run.
run() {
  printf '+ %s\n' "$*"
  if [ "$DRY_RUN" -eq 0 ]; then "$@"; fi
}
# warn_run: like run, but a failure is reported and the runbook continues (used only for the clean-workspace deploy).
warn_run() {
  printf '+ %s\n' "$*"
  if [ "$DRY_RUN" -eq 0 ]; then
    if ! "$@"; then printf '   WARNING: step failed; continuing (see the clean-workspace caveat above)\n'; fi
  fi
}

ME="<current user>"
if [ "$DRY_RUN" -eq 0 ] && [ "$FULL" -eq 1 ]; then
  ME="$(databricks --profile "$PROFILE" current-user me -o json | jq -r .userName)"
fi
WS_HOME="/Workspace/Users/$ME"
APP_SRC="$WS_HOME/fe-bar-appeals-app"
AGENT_NB="$WS_HOME/fe-bar-appeals/agent/build_and_deploy"

step "0. Context"
info "repo=$REPO target=$TARGET catalog=$CATALOG schema=$SCHEMA profile=$PROFILE warehouse=$WAREHOUSE dry_run=$DRY_RUN user=$ME"

step "1. Render dashboard and Genie JSON for $TARGET (catalog.schema rewrite; default output == source)"
run python3 scripts/render_configs.py --catalog "$CATALOG" --schema "$SCHEMA" --out "build/$TARGET"

step "2. Bundle validate + deploy (target $TARGET)"
run databricks bundle validate -t "$TARGET" -p "$PROFILE"
if [ "$FULL" -eq 1 ]; then
  warn_run databricks bundle deploy -t "$TARGET" -p "$PROFILE"
else
  run databricks bundle deploy -t "$TARGET" -p "$PROFILE"
fi

step "3. Lakebase project, database and DDL"
if [ "$FULL" -eq 1 ]; then run bash lakebase/setup_lakebase.sh; else skip "Lakebase"; fi

step "4. Data layer: full job run (bootstrap, generator, SDP, grounding, appeals, cost_views, lakebase_sync, eval)"
info "Long-running; the job is PAUSED on its schedule, so this manual run is the only one."
run databricks bundle run -t "$TARGET" -p "$PROFILE" "$JOB"

step "5. Lakebase synced table, then apply the review_state view"
if [ "$FULL" -eq 1 ]; then
  run bash lakebase/create_synced_table.sh
  run bash lakebase/setup_lakebase.sh
else
  skip "Lakebase synced table"
fi

step "6. Governance: PHI tags and column masks (02 is NOT run: needs an account-level group)"
if [ "$FULL" -eq 1 ]; then
  run python3 tools/run_sql.py -f governance/01_phi_tags.sql
  run python3 tools/run_sql.py -f governance/05_column_masks.sql
else
  skip "governance 01/05 (the SQL hard-codes appeals_hackathon_catalog.fe_bar_appeals; it would tag and mask the live tables)"
fi

step "7. Genie metric view, then redeploy so the bundle-managed Genie space sees it"
if [ "$FULL" -eq 1 ]; then
  run python3 tools/run_sql.py -f genie/00_cost_assumptions.sql
  run python3 tools/run_sql.py -f genie/01_appeals_metrics.sql
  info "The space itself is in the bundle (genie/appeals_metrics.geniespace.json); genie/build_space.py is superseded."
  run databricks bundle deploy -t "$TARGET" -p "$PROFILE"
else
  skip "metric view SQL (genie/00, 01 hard-code the live schema); smoke's Genie space needs a parameterized metric view first"
fi

step "8. Chat agent: one-time serverless run of agent/build_and_deploy.py (agents.deploy creates the endpoint)"
if [ "$FULL" -eq 1 ]; then
  run databricks workspace mkdirs "$WS_HOME/fe-bar-appeals/agent"
  run databricks workspace import "$AGENT_NB" --file agent/build_and_deploy.py --format SOURCE --language PYTHON --overwrite
  AGENT_JOB='{"run_name":"fe-bar-appeals-agent-deploy","environments":[{"environment_key":"agent","spec":{"client":"2","dependencies":["mlflow[databricks]>=3.1","databricks-agents"]}}],"tasks":[{"task_key":"agent_deploy","environment_key":"agent","notebook_task":{"notebook_path":"'"$AGENT_NB"'"}}]}'
  run databricks jobs submit -p "$PROFILE" --timeout 60m --json "$AGENT_JOB"
  run databricks bundle deploy -t "$TARGET" -p "$PROFILE"
else
  skip "chat agent (no chat endpoint in smoke)"
fi

step "9. App: workspace import, create if missing, full definition (scopes + resources), deploy"
if [ "$FULL" -eq 1 ]; then
  if [ "$DRY_RUN" -eq 0 ] && ! databricks --profile "$PROFILE" apps get "$APP" -o json >/dev/null 2>&1; then
    info "app $APP missing: creating it without compute (the start is below)"
    run databricks apps create -p "$PROFILE" --no-compute --json "{\"name\":\"$APP\",\"description\":\"FE Bar medical-necessity appeals worklist\"}"
  else
    info "create $APP if missing (apps get check runs for real)"
  fi
  STAGE="<temp dir>"
  if [ "$DRY_RUN" -eq 0 ]; then STAGE="$(mktemp -d "${TMPDIR:-/tmp}/fe_bar_app.XXXXXX")"; fi
  info "stage (no node_modules, dist or .env): rsync app/ -> temp dir"
  run rsync -a --exclude node_modules --exclude dist --exclude client/dist --exclude '.env' --exclude '.env.*' --exclude '*.pyc' "$REPO/app/" "$STAGE/"
  run databricks workspace import-dir "$STAGE" "$APP_SRC" -p "$PROFILE" --overwrite
  run databricks apps update "$APP" -p "$PROFILE" --json @app/app_resources.json
  warn_run databricks apps start "$APP" -p "$PROFILE"   # already-running apps may report an error here; not fatal
  run databricks apps deploy "$APP" -p "$PROFILE" --source-code-path "$APP_SRC"
  if [ "$DRY_RUN" -eq 0 ]; then rm -rf "$STAGE"; fi
  info "Bindings: lakebase/APP_GRANTS.md (sql-warehouse, files, postgres, genie-space, serving-endpoint) are in app/app_resources.json."
else
  skip "app"
fi

step "10. Governance 04: app SP SELECT on the 5 Genie objects"
if [ "$FULL" -eq 1 ]; then
  run python3 tools/run_sql.py -f governance/04_app_sp_genie_grants.sql
else
  skip "grants"
fi

step "11. Final bundle plan (default must show no deletes or recreates)"
run databricks bundle plan -t "$TARGET" -p "$PROFILE"

step "Done"
info "Runbook complete for target $TARGET. Re-run is safe; check the plan output above before any destructive change."
