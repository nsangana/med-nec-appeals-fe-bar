# Grants and bindings for fe-bar-appeals-app (current state)

App service principal (SP) client id `059b0419-b956-41e1-a788-e5104b645dc9`. The app runs as this SP for the worklist, review actions and the Genie tab. The signed-in user's token (OBO) is used for letter and data-sheet PDFs and for chat.

## Status

| Item | Who | How | State |
|---|---|---|---|
| Postgres grants on the Lakebase database `appeals` | App SP | `lakebase/app_grants.sql` | **Applied** |
| Serving endpoint `fe-bar-appeals-chat` | App SP | `serving-endpoint` resource, CAN_QUERY | **Applied** |
| Genie space `01f1e7ec913217158b231c3e2f18fa20` | App SP | `genie-space` resource, CAN_RUN | **Applied** |
| SELECT on the 5 Genie objects | App SP | `governance/04_app_sp_genie_grants.sql` | **Applied** |
| Reviewer UC grants (`fe-bar-appeals-reviewers`) | Reviewer group, OBO | `governance/02_reviewer_grants.sql` | **PENDING: needs an account-level group** |

## 1. Postgres (app SP): applied

`lakebase/app_grants.sql`. Covers every statement the app issues:
- CONNECT on `appeals`; USAGE on schemas `public` and `fe_bar_appeals`
- SELECT on `fe_bar_appeals.worklist_serving` (read-only synced copy)
- SELECT and INSERT on `public.review_actions` (append-only; no UPDATE or DELETE), plus USAGE on its sequence
- SELECT on the `public.review_state` view

The worklist, summary, case and review-action routes return 200 or 201 with no 42501 in the app logs.

## 2. Resource bindings (app): applied

- `sql-warehouse` (CAN_USE)
- `files`: UC volume `appeals_hackathon_catalog.fe_bar_appeals.appeal_pdfs` (READ_VOLUME)
- `postgres`: Lakebase database `appeals` (CAN_CONNECT_AND_CREATE)
- `serving-endpoint`: `fe-bar-appeals-chat` (CAN_QUERY). `app/app.yaml` reads it through `valueFrom: serving-endpoint`.
- `genie-space`: `01f1e7ec913217158b231c3e2f18fa20` (CAN_RUN). `DATABRICKS_GENIE_SPACE_ID` is set, and `genie` is in the app's user API scopes. The forwarded token still does not carry `genie` in practice, so the Genie tab runs as the SP.

## 3. Genie objects (app SP): applied

`governance/04_app_sp_genie_grants.sql`, approved 2026-11-24. Least privilege:
- USE CATALOG `appeals_hackathon_catalog`; USE SCHEMA `appeals_hackathon_catalog.fe_bar_appeals`
- SELECT on the five objects in the space: `appeals_metrics`, `gold_denial_worklist`, `appeals_output`, `eval_summary`, `review_state_uc`

Trade-off: Genie answers reflect the app's access, not each reviewer's grants.

## 4. Reviewer UC grants (OBO): PENDING

This is the only pending item. The reviewer persona is the workspace group `fe-bar-appeals-reviewers`. UC grants cannot be issued to a workspace-local group (`PRINCIPAL_DOES_NOT_EXIST`), so the grants wait for an account-level group. Once it exists, replace the placeholder group name in `governance/02_reviewer_grants.sql` and apply it. The file grants:
- USE CATALOG and USE SCHEMA on `appeals_hackathon_catalog.fe_bar_appeals`
- SELECT on `gold_denial_worklist`, `appeals_output`, `worklist_serving` and the `appeals_metrics` view
- READ VOLUME on `appeal_pdfs`
- EXECUTE on the lookup functions `get_appeal`, `get_encounter`, `mpfs_lookup` and `descriptor_lookup`

It does not grant bronze, the landing volume, eval labels or `encounter_grounding`. Until it is applied, the reviewer path depends on grants the group does not yet hold, and the non-member column-mask branch is verified at logic level only (`evidence/13_column_masks.md`).
