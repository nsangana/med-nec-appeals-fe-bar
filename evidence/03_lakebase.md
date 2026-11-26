# Evidence 03: Lakebase serving layer

REFRESHED 2026-11-26 UTC (clean data-layer rerun and regeneration). Worklist counts, top 5 and hero review state re-read on 2026-11-26. Workspace profile `fevm-appeals-hackathon`. Warehouse `559faf81d610a2a1`. No secrets or tokens recorded.

Read path: UC catalog `fe_bar_appeals_lakebase` (warehouse `559faf81d610a2a1`). The sync is refreshed by the job task `lakebase_sync` in each job run (evidence/08).

History: earlier runs are in git history.

## Resource IDs

| Resource | ID |
|---|---|
| Lakebase Autoscaling project | `fe-bar-appeals-lakebase` (uid 401d8a7c-b2ea-4d86-b169-dd7dbf47a115), PG 17 |
| Branch | `production` (uid br-twilight-grass-d2896k36), READY, default |
| Endpoint | `primary` (READ_WRITE), ACTIVE, 0.5 CU min = max, suspend 300 s (scale-to-zero) |
| Endpoint host | `ep-icy-field-d2gk8ye7.database.us-east-1.cloud.databricks.com` (port 5432, sslmode=require) |
| Database | `appeals` (Postgres database `appeals`) |
| Dev login role | `<builder email>` (LAKEBASE_OAUTH_V1, OAuth token, no password) |
| UC catalog (Lakebase) | `fe_bar_appeals_lakebase` → database `appeals` |
| Synced table | `fe_bar_appeals_lakebase.fe_bar_appeals.worklist_serving` → Postgres `fe_bar_appeals.worklist_serving` (PK on the three UPPERCASE keys; quote them in SQL) |
| Sync pipeline | `0245f1ce-9b6c-49c9-88ae-1942576611d7` (refreshed in each job run) |
| Delta source | `appeals_hackathon_catalog.fe_bar_appeals.worklist_serving` (CDF on, PK on 3 keys): 500 rows |
| Delta copy of reviewer state | `appeals_hackathon_catalog.fe_bar_appeals.review_state_uc` |

## Worklist counts (Lakebase `fe_bar_appeals.worklist_serving`, 2026-11-26)

Query: `SELECT COUNT(*), ... FROM fe_bar_appeals_lakebase.fe_bar_appeals.worklist_serving`

| worklist_rows | WARRANTED | NOT WARRANTED | NEEDS REVIEW | no appeal yet | data sheets (PDF) | AT_RISK | PAST_DUE | OK |
|---|---|---|---|---|---|---|---|---|
| 500 | 72 | 66 | 42 | 320 | 450 | 67 | 50 | 383 |

- The 72 / 66 / 42 split equals `appeals_output` (evidence/08 run 3): the app worklist and the generator agree.
- 180 rows have an appeal, 72 have a letter, 450 have a data sheet. The 320 rows with no appeal yet are the 500 − 180 encounters. The 50 PAST_DUE encounters have no grounding and no data sheet, which is why data sheets are 450.
- Counts with `deadline_status` are computed against the UTC date of the refresh (2026-11-26 here). See the date note in EVIDENCE.md.

## Top 5 by priority (2026-11-26)

| facility_id | patient_control_number | encounter_nbr | priority_rank | recommendation | deadline_status | days_remaining | expected_reimbursement | letter |
|---|---|---|---|---|---|---|---|---|
| 101 | 770000001 | 50000001 | 1 | WARRANTED | AT_RISK | 8 | 24,850.00 (hero) | yes |
| 102 | 770000203 | 50000203 | 2 | WARRANTED | AT_RISK | 1 | 20,096.92 | yes |
| 101 | 770000394 | 50000394 | 3 | NEEDS REVIEW | AT_RISK | 0 | 18,585.01 | no |
| 101 | 770000231 | 50000231 | 4 | NOT WARRANTED | AT_RISK | 10 | 18,438.19 | no |
| 102 | 770000233 | 50000233 | 5 | WARRANTED | AT_RISK | 4 | 17,437.31 | yes |

The hero's `days_remaining` was 9 on the 2026-11-25 run and reads 8 on 2026-11-26.

## Hero review state (Postgres view `public.review_state`)

Query: `SELECT * FROM fe_bar_appeals_lakebase.public.review_state WHERE facility_id=101 AND patient_control_number=770000001 AND encounter_nbr=50000001`

| facility_id | patient_control_number | encounter_nbr | status | last_reviewer | last_action_at | submitted_at | deadline_met |
|---|---|---|---|---|---|---|---|
| 101 | 770000001 | 50000001 | SUBMIT | demo-reviewer (simulated) | 2026-11-24T10:11:38.777Z | 2026-11-24T10:11:38.777Z | true |

- The hero is WARRANTED with a letter. Review state SUBMIT is a simulated reviewer action (`demo-reviewer (simulated)`), not a real health-system decision.
- `public.review_actions` holds 14 append-only rows; the newest was written 2026-11-26T06:33:14Z.

## UC copy of reviewer state (`review_state_uc`)

Query: `SELECT * FROM appeals_hackathon_catalog.fe_bar_appeals.review_state_uc WHERE patient_control_number = 770000001`

| facility_id | patient_control_number | encounter_nbr | status | last_reviewer | last_action_at | submitted_at | deadline_met | copied_at |
|---|---|---|---|---|---|---|---|---|
| 101 | 770000394 | 50000394 | EDIT | demo-reviewer (simulated) | 2026-11-24T09:55:00.409Z | NULL | false | 2026-11-26T03:11:33.172Z |
| 101 | 770000001 | 50000001 | SUBMIT | demo-reviewer (simulated) | 2026-11-24T10:11:38.777Z | 2026-11-24T10:11:38.777Z | true | 2026-11-26T03:11:33.172Z |
| 102 | 770000203 | 50000203 | ROUTE_TO_REVIEW | demo-reviewer (simulated) | 2026-11-24T09:55:00.296Z | NULL | false | 2026-11-26T03:11:33.172Z |

The Postgres view and the Delta copy are readable from UC, so no fallback is needed.

## Status

- `appeals_output` is populated and synced: job task `lakebase_sync` runs inside `fe-bar-appeals-job` (evidence/08).
- App service principal role and grants are applied (`lakebase/app_grants.sql`).
- Postgres key columns are UPPERCASE (`"FACILITY_ID"`, `"PATIENT_CONTROL_NUMBER"`, `"ENCOUNTER_NBR"`); quote them in SQL.
- Reviewer actions are SIMULATED (`demo-reviewer (simulated)`). The rerun touches the data layer, not reviewer state, so the hero's SUBMIT is unchanged.
