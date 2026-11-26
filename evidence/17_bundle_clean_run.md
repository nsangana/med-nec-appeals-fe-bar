# Evidence 17 — Clean run: from-scratch smoke deployment + live verification

REAL runs on workspace fevm-appeals-hackathon, 2026-11-26. Synthetic data. Bundle `med-nec-appeals-fe-bar`,
targets `default` (live) and `smoke` (isolated schema `appeals_hackathon_catalog.fe_bar_appeals_test`).

## Why this test exists
Binding the live resources proves the bundle **matches** what exists; it does not prove the bundle can **create**
the stack. This run deploys the bundle into an empty, isolated schema, runs the whole job, verifies every layer,
then destroys it — and re-verifies live without changing live data.

## 0. Preconditions (parameterization)
- Bundle variables + targets: `catalog`, `schema`, `name_prefix`, `max_appeals`, `enable_lakebase_sync`, Lakebase/VS names, per-target dashboard/Genie files (`databricks.yml`, `targets/default/*.yml`).
- Task code reads `catalog`/`schema`: SQL tasks start with `USE CATALOG IDENTIFIER(:catalog); USE SCHEMA IDENTIFIER(:schema);` (no string interpolation); notebooks read validated widgets; SDP reads `${landing_root}` / `${refs_root}` from pipeline configuration.
- Exported dashboard/Genie JSON rendered per target (`scripts/render_configs.py`; default output byte-identical to source).
- Tests: Python 202 passed, app 73 passed (`evidence/18_test_results.md`).
- Live plan before any change: `0 to add, 2 to change (job params, pipeline config keys), 0 to delete, 15 unchanged`.

## 1. Smoke target — from scratch
| Step | Result |
|---|---|
| `bundle deploy -t smoke` | 8 resources created: schema, 3 volumes, SDP pipeline, job, dashboard, Genie space (Genie created on the second deploy, after the job built its tables — see ordering) |
| Full job run `308145351572869` (as_of 2026-11-25, max_appeals 5, Lakebase sync off) | **SUCCESS — all 12 tasks** |
| Layer counts in `fe_bar_appeals_test` | bronze 538 → silver 532 → gold 500; encounter_grounding 450; data_sheet_facts 450; appeals_output generated (5 per run); data-sheet + letter PDFs in the test volume; eval_summary written |
| Smoke dashboard | dataset `ds_cpa` returned rows from the test schema |
| Smoke Genie space | answered from `fe_bar_appeals_test.appeals_metrics` ("7 WARRANTED" across the smoke runs) |
| Parameter propagation | `USE CATALOG/SCHEMA IDENTIFIER(:…)` held across every statement of each Jobs SQL file task (proved by the run itself) |

**Fix found by the smoke run:** with `enable_lakebase_sync=false`, `review_state_uc` was never created, which broke the metric
view and Genie in a fresh schema. `pipeline/50_lakebase_sync.py` now creates an empty table in the flag-off branch (test added).
Live runs with the flag on, so live behaviour is unchanged.

**Ordering that works from scratch:** deploy (Genie creation waits for its tables) → run job → run `genie/00` + `genie/01` with
catalog/schema → redeploy (Genie created).

**Runs:** `1019750181021044` (first, SUCCESS), `308145351572869` (run of record, SUCCESS), `872139547279584` (a duplicate
`bundle run` launched by the build tooling in the same minute under the builder's identity, SUCCESS), `405490969333152`
(queued duplicate, cancelled). Smoke therefore held 15 generated appeals (5 per successful run).

## 2. Teardown
- Delete protection (`prevent_destroy`) moved from the shared resource files to **live-only** overrides (`targets/default/guards.yml`):
  default target 15 guarded resources, smoke target 0. Live plan unchanged by the move.
- `bundle destroy -t smoke --auto-approve` → **8 deleted**; `DROP SCHEMA … fe_bar_appeals_test CASCADE` (job-created tables).
- Verified: smoke job and pipeline gone, smoke Genie gone, smoke dashboard trashed, only `fe_bar_appeals` schema remains.

## 3. Live verification (no data churn)
| Check | Result |
|---|---|
| Live counts before | bronze 538, gold 500, appeals_output 180 (72 / 66 / 42), encounter_grounding 450 |
| `bundle deploy -t default` | 0 created, 2 changed (job, pipeline), 0 deleted, 15 unchanged |
| Live job run `120234699538992` (max_appeals 0, as_of 2026-11-25) | **SUCCESS — all 12 tasks** (bootstrap, generate_raw_data, sdp_pipeline, grounding, data_sheet_facts, generate_appeals, cost_views, evaluate, register_tools, render_pdfs, genai_evaluate, lakebase_sync) |
| Live counts after | bronze 538, gold 500, **appeals_output 180**, encounter_grounding 450, Lakebase worklist 500 — unchanged |
| Final `bundle plan -t default` | **0 to add, 0 to change, 0 to delete, 17 unchanged** |
| Chat endpoint | answers the hero question: WARRANTED |
| Genie (live) | "How many appeals are WARRANTED?" → 72 |

## Not covered (and why)
- Lakebase project, chat serving endpoint, registered model and vector index are **not** created in smoke (slow/costly and
  already proven live; they exist only in the default target). The app and grants run through `scripts/deploy_all.sh`.
