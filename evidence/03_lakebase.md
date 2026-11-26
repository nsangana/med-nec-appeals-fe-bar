# Evidence 03: Lakebase serving layer (Agent C)

REFRESHED 2026-11-25 (clean data-layer rerun). Worklist counts and hero review state re-read below; resource IDs unchanged.
Read path: UC catalog `fe_bar_appeals_lakebase` (warehouse `559faf81d610a2a1`); the sync is refreshed by the job task `lakebase_sync` in each of the three job runs (evidence/08).

## Worklist counts (refreshed 2026-11-25, Lakebase `fe_bar_appeals.worklist_serving`)

Query: `SELECT COUNT(*), ... FROM fe_bar_appeals_lakebase.fe_bar_appeals.worklist_serving`

| worklist_rows | WARRANTED | NOT WARRANTED | NEEDS REVIEW | no appeal yet | data sheets (PDF) | AT_RISK | PAST_DUE | OK |
|---|---|---|---|---|---|---|---|---|
| 500 | 73 | 64 | 43 | 320 | 460 | 75 | 40 | 385 |

- The 73 / 64 / 43 split equals `appeals_output` (evidence/04, evidence/08 run 3): the app worklist and the generator agree.
- 320 rows have no appeal yet (500 − 180). The 40 PAST_DUE encounters have no grounding and no data sheet, which is why data sheets are 460.

## Top 5 by priority (refreshed 2026-11-25)

| facility_id | patient_control_number | encounter_nbr | priority_rank | recommendation | deadline_status | days_remaining | expected_reimbursement | letter |
|---|---|---|---|---|---|---|---|---|
| 101 | 770000001 | 50000001 | 1 | WARRANTED | AT_RISK | 9 | 24,850.00 (hero) | yes |
| 102 | 770000203 | 50000203 | 2 | WARRANTED | AT_RISK | 2 | 20,096.92 | yes |
| 101 | 770000394 | 50000394 | 3 | NEEDS REVIEW | AT_RISK | 1 | 18,585.01 | no |
| 101 | 770000231 | 50000231 | 4 | NOT WARRANTED | AT_RISK | 11 | 18,438.19 | no |
| 102 | 770000233 | 50000233 | 5 | WARRANTED | AT_RISK | 5 | 17,437.31 | yes |

## Hero review state (refreshed 2026-11-25)

Query: `SELECT * FROM fe_bar_appeals_lakebase.public.review_state WHERE facility_id=101 AND patient_control_number=770000001 AND encounter_nbr=50000001`

| facility_id | patient_control_number | encounter_nbr | status | last_reviewer | last_action_at | submitted_at | deadline_met |
|---|---|---|---|---|---|---|---|
| 101 | 770000001 | 50000001 | SUBMIT | demo-reviewer (simulated) | 2026-11-24T10:11:38.777Z | 2026-11-24T10:11:38.777Z | true |

- The hero is WARRANTED with a letter (review state SUBMIT, simulated reviewer action; the reviewer action is simulated, not a real health-system decision).
- `public.review_actions` holds 7 append-only rows; the newest was written 2026-11-24T10:11:38Z. No new reviewer action was recorded in the 2026-11-25 rerun, which is expected: the rerun touches the data layer, not reviewer state.

## Synced table

- `fe_bar_appeals_lakebase.fe_bar_appeals.worklist_serving` → Postgres `fe_bar_appeals.worklist_serving` (PK on the three UPPERCASE keys; quote them in SQL). Sync pipeline `0245f1ce-9b6c-49c9-88ae-1942576611d7`, refreshed in each job run.
- Delta source `appeals_hackathon_catalog.fe_bar_appeals.worklist_serving`: 500 rows.

---

## SUPERSEDED: 2026-11-24 Lakebase state (before the clean rerun)

The worklist counts, top-5 list and hero review state below are from 2026-11-24 and are kept for audit. Do not quote them.

Date: 2026-11-24. Workspace profile `fevm-appeals-hackathon`. Warehouse `559faf81d610a2a1`. No secrets or tokens recorded.
Simulated reviewer actions are labelled `demo-reviewer (simulated)`.

## Resource IDs (unchanged by the rerun)
| Resource | ID |
|---|---|
| Lakebase Autoscaling project | `fe-bar-appeals-lakebase` (uid 401d8a7c-b2ea-4d86-b169-dd7dbf47a115), PG 17 |
| Branch | `production` (uid br-twilight-grass-d2896k36), READY, default |
| Endpoint | `primary` (READ_WRITE), ACTIVE, 0.5 CU min = max, suspend 300 s (scale-to-zero) |
| Endpoint host | `ep-icy-field-d2gk8ye7.database.us-east-1.cloud.databricks.com` (port 5432, sslmode=require) |
| Database | `appeals` (Postgres database `appeals`) |
| Dev login role | `<builder email>` (LAKEBASE_OAUTH_V1, OAuth token, no password) |
| UC catalog (Lakebase) | `fe_bar_appeals_lakebase` → database `appeals` (create-catalog OK) |
| Synced table | `fe_bar_appeals_lakebase.fe_bar_appeals.worklist_serving` → Postgres `fe_bar_appeals.worklist_serving` |
| Sync pipeline | `0245f1ce-9b6c-49c9-88ae-1942576611d7` (TRIGGERED) |
| Last refresh update | `52f6faea-20af-4131-8245-ea8129a4339d` (COMPLETED) |
| Delta source | `appeals_hackathon_catalog.fe_bar_appeals.worklist_serving` (CDF on, PK on 3 keys) |
| Delta copy of reviewer state | `appeals_hackathon_catalog.fe_bar_appeals.review_state_uc` |

### Synced table status (2026-11-24)
- `detailed_state`: `SYNCED_TABLE_ONLINE_NO_PENDING_UPDATE`
- `unity_catalog_provisioning_state`: ACTIVE. Initial sync: 500 / 500 rows.
- Postgres key columns are UPPERCASE (`"FACILITY_ID"`, `"PATIENT_CONTROL_NUMBER"`, `"ENCOUNTER_NBR"`); quote them in SQL.
- Refresh path: `start_update` on pipeline `0245f1ce…`, then poll to COMPLETED (implemented in `pipeline/50_lakebase_sync.py` §2).

### Lakebase query results (2026-11-24)

### Worklist row count (Postgres `fe_bar_appeals.worklist_serving`)
| worklist_rows |
|---|
| 500 |

Deadline status mix: AT_RISK 75, OK 385, PAST_DUE 40.

### Top 5 by priority (Postgres)
| fid | pcn | enc | priority_rank | deadline_status | days_remaining | expected_reimbursement |
|---|---|---|---|---|---|---|
| 101 | 770000001 | 50000001 | 1 | AT_RISK | 9 | 24850 (hero) |
| 102 | 770000203 | 50000203 | 2 | AT_RISK | 2 | 20096.92 |
| 101 | 770000394 | 50000394 | 3 | AT_RISK | 1 | 18585.01 |
| 101 | 770000231 | 50000231 | 4 | AT_RISK | 11 | 18438.19 |
| 102 | 770000233 | 50000233 | 5 | AT_RISK | 5 | 17437.31 |

### review_state (Postgres view)
| facility_id | pcn | enc | status | last_reviewer | last_action_at | submitted_at | deadline_met |
|---|---|---|---|---|---|---|---|
| 101 | 770000001 | 50000001 | SUBMIT | demo-reviewer (simulated) | 2026-11-24 09:14:31 UTC | 2026-11-24 09:14:31 UTC | t |
| 102 | 770000203 | 50000203 | ROUTE_TO_REVIEW | demo-reviewer (simulated) | 2026-11-24 09:55:00 UTC | (null) | f |
| 101 | 770000394 | 50000394 | EDIT | demo-reviewer (simulated) | 2026-11-24 09:55:00 UTC | (null) | f |

Hero claim (Elena Marquez, keys 101 / 770000001 / 50000001): APPROVE then SUBMIT (simulated), 9 days remaining at
refresh, `deadline_met = t`.

### UC copy (2026-11-24)
- `SELECT COUNT(*) FROM appeals_hackathon_catalog.fe_bar_appeals.review_state_uc` → **3** rows.
- Warehouse query against `fe_bar_appeals_lakebase.public.review_state` succeeded, so UC registration works and no
  fallback is needed. The Delta copy is still written by the job task for the Genie / governance path.

### Deviations and gaps (2026-11-24)
> **Status update 2026-11-25 (orchestrator):** the three gaps below are RESOLVED — appeals_output is populated and synced (job task `lakebase_sync` runs inside `fe-bar-appeals-job`, see evidence/08); the app SP role exists via the app's postgres resource and its grants are applied (`lakebase/app_grants.sql`).

- `appeals_output` had 0 rows when the synced table was built, so `recommendation`, `cheat_sheet`, `appeal_letter`
  and PDF paths are NULL in the worklist until B's output lands. Re-run `pipeline/50_lakebase_sync.py` to refresh.
- The notebook was run section by section with the same SQL and SDK calls (not as a Databricks job). The full job
  run is pending the orchestrator's `lakebase_sync` task.
- App service principal role and grants: pending (app not created). See `lakebase/AUTH.md`.

printf '\n\n## Lakebase after the regeneration (2026-11-26 UTC) — CURRENT\n\n'

tools/run_sql.py "SELECT count(*) worklist_rows, count(recommendation) with_appeal, count(appeal_letter) letters, count(data_sheet_pdf_path) data_sheets FROM fe_bar_appeals_lakebase.fe_bar_appeals.worklist_serving"

tools/run_sql.py "SELECT * FROM appeals_hackathon_catalog.fe_bar_appeals.review_state_uc WHERE patient_control_number = 770000001"


## Lakebase after the regeneration (2026-11-26 UTC) — CURRENT

| worklist_rows | with_appeal | letters | data_sheets |
|---|---|---|---|
| 500 | 180 | 72 | 450 |

| facility_id | patient_control_number | encounter_nbr | status | last_reviewer | last_action_at | submitted_at | deadline_met | copied_at |
|---|---|---|---|---|---|---|---|---|
| 101 | 770000001 | 50000001 | SUBMIT | demo-reviewer (simulated) | 2026-11-24T10:11:38.777Z | 2026-11-24T10:11:38.777Z | true | 2026-11-26T03:11:33.172Z |

