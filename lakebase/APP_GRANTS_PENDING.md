> **Status 2026-11-25 — all items below are DONE except reviewer UC grants (need an account-level group).** Serving endpoint bound (CAN_QUERY), Genie space bound (CAN_RUN; app scope `genie`; Genie tab runs as the app SP with SELECT on its 5 objects, `governance/04_app_sp_genie_grants.sql`).

# Pending grants and bindings for fe-bar-appeals-app (Agent E)

Status 2026-11-24 ~10:10 UTC. Agent E applied nothing. The orchestrator applied the SP Postgres grants (`lakebase/app_grants.sql`).

## Postgres (app SP `059b0419-b956-41e1-a788-e5104b645dc9`): DONE
Covers every statement the app issues (SELECT worklist_serving, SELECT review_state, SELECT+INSERT review_actions + sequence USAGE).
Verified: worklist, summary, case and review-action (201) routes all 200 with no 42501 in the app logs. No further Postgres grants needed.

## Resolved: data_sheet_pdf_path missing from worklist_serving
Was a blocker (503 42703). Agent C's `50_lakebase_sync.py` now carries it (460 rows filled). The app selects `w.data_sheet_pdf_path` again (no fallback).

## User-level UC grants for reviewers (OBO path; not the SP): PENDING
Reviewers need these in addition to the platform resources below (the letter text and PDFs are read as the signed-in user):
- USE CATALOG `appeals_hackathon_catalog`; USE SCHEMA `appeals_hackathon_catalog.fe_bar_appeals`
- SELECT on `appeals_hackathon_catalog.fe_bar_appeals.appeals_output`
- READ VOLUME on `appeals_hackathon_catalog.fe_bar_appeals.appeal_pdfs`
- CAN_USE on warehouse `559faf81d610a2a1`; CAN_QUERY on `fe-bar-appeals-chat` once it exists
Group `fe-bar-appeals-reviewers` is blocked on an account-level group. Governance file: `governance/02_reviewer_grants.sql` (Agent D); the orchestrator applies it.

## App resource bindings still to add
1. Serving endpoint `fe-bar-appeals-chat` (Agent B, not created yet). Add with `databricks apps create-update fe-bar-appeals-app` (update_mask=resources),
   merging `{"name":"serving-endpoint","serving_endpoint":{"name":"fe-bar-appeals-chat","permission":"CAN_QUERY"}}` into the existing resources
   (keep sql-warehouse, files, postgres). Then change `app/app.yaml` DATABRICKS_SERVING_ENDPOINT_NAME to `valueFrom: serving-endpoint` and redeploy.
   Until then the chat route returns 502 with the endpoint-not-found message.
2. Genie space (Agent D, optional): `genie-space` resource (CAN_RUN) + `DATABRICKS_GENIE_SPACE_ID` env + `dashboards.genie` in user_api_scopes. See app/README.md "Genie wiring".
