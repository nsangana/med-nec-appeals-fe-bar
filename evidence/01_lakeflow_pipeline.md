# 01 — Lakeflow SDP pipeline + synthetic caseload (REFRESHED 2026-11-25, clean data-layer rerun)

Workspace: https://fevm-appeals-hackathon.cloud.databricks.com (profile `fevm-appeals-hackathon`) · catalog/schema `appeals_hackathon_catalog.fe_bar_appeals`.
Everything below is real output from this workspace on 2026-11-25. The caseload is SYNTHETIC (seed 20261124, as_of **2026-11-25**).
The 2026-11-24 run is kept at the bottom as SUPERSEDED.

## Resource IDs

| Item | ID |
|---|---|
| Bundle | `med-nec-appeals-fe-bar` (target `default`, no `mode: development`) |
| Pipeline | `fe-bar-appeals-sdp`, id `4873b47b-47a7-4081-97c0-7cdf018c71a1`, serverless, channel CURRENT |
| Full refresh (COMPLETED) | update `7642a160-cd3a-4719-b1ce-8f01b833fdfa` (API_CALL) |
| Job SDP updates (incremental, 3) | `49faa9c8…` (run 1), `0d9b4523…` (run 2), `39f8431e…` (run 3); see evidence/08 |

## Full refresh timeline (event log, update `7642a160…`, UTC)

| Time (UTC) | State |
|---|---|
| 22:14:57.856 | create_update (API_CALL) |
| 22:15:00.376 | INITIALIZING |
| 22:15:05.346 | RESETTING (full refresh) |
| 22:15:06.794 | SETTING_UP_TABLES |
| 22:15:13.998 | RUNNING (8 flows defined, one `flow_definition` event each) |
| 22:15:42.364 | **COMPLETED** (about 45 s) |

Landing state at the start of the update: one batch file in each folder, `landing/claims/batch_2026-11-25_seed20261124_n500.json` (last modified 22:14:15Z) and `landing/clinical_notes/batch_2026-11-25_seed20261124_n500.json` (22:14:14Z).

## Expectation results (event log `flow_progress.data_quality`, update `7642a160…`)

| Flow (dataset) | Expectation | Action | Passed | Failed |
|---|---|---|---|---|
| silver_claim_lines | carc_in_scope | DROP ROW | 536 | 2 |
| silver_claim_lines | composite_key_not_null | DROP ROW | 536 | 2 |
| silver_claim_lines | dos_before_denial_date | DROP ROW | 536 | 2 |
| silver_claim_lines | expected_reimbursement_non_negative | WARN | 536 | 2 |
| silver_clinical_notes | note_date_present | DROP ROW | 1053 | 0 |
| silver_clinical_notes | note_text_present | DROP ROW | 1053 | 0 |
| silver_clinical_notes | composite_key_not_null | DROP ROW | 1053 | 0 |

Notes:
- Counts are per expectation over the rows evaluated (passed + failed = bronze rows, 538 for claims and 1,053 for notes).
- Bronze → silver: claims 538 → 532 (6 dropped). Each DROP expectation reports 2 failures; the same injected defect lines can fail more than one rule, so the per-expectation counts do not sum to 6.
- Clinical notes: 1,053 → 1,053, no drops. The notes batch is now 1,053 rows, not the 1,024 of the 2026-11-24 run.
- The WARN rule reports 2 negative EXPECTED_REIMBURSEMENT rows. They are kept, and `gold_denial_worklist.expected_reimbursement` counts only the positive part (`greatest(line, 0)`), so they add $0.

## Row counts per layer (after the full refresh; re-checked after job run 3)

| Layer | Object | Rows | Note |
|---|---|---|---|
| Bronze | bronze_claims | 538 | Auto Loader, all landed claim lines incl. the injected defect lines |
| Bronze | bronze_clinical_notes | 1,053 | |
| Silver | silver_claim_lines | 532 | 538 − 6 dropped |
| Silver | silver_clinical_notes | 1,053 | no drops |
| Gold | mednecessity_ai_agent (MV) | 532 | claim-line grain, latest-wins dedupe |
| Gold | medical_records (MV) | 1,053 | note grain |
| Gold | gold_denial_worklist (MV) | **500** | one row per encounter; 500 distinct (FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR) |
| Reference | mpfs_indicator_listing (MV) | 19,116 | |

## Worklist trigger tags and deadline status (gold_denial_worklist)

| deadline_status | worklist_tag | Rows |
|---|---|---|
| AT_RISK | AT_RISK | 75 |
| OK | NEW (denied yesterday) | 20 |
| OK | OPEN | 365 |
| PAST_DUE | PAST_DUE | 40 |

Label mix (eval_case_labels joined to gold on the composite key, 500 / 500 matched, as_of 2026-11-25, 33 scenarios):
WARRANTED 225, NOT WARRANTED 175, NEEDS REVIEW 100 (target 45 / 35 / 20 %).

## Hero claim (gold row, Elena Marquez; fictional)

| FACILITY_ID | PATIENT_CONTROL_NUMBER | ENCOUNTER_NBR | patient_name | payer_name | payer_type | denial_code | hcpcs_codes | dos | denial_date | appeal_limit_days | appeal_deadline | days_remaining | deadline_status | total_charges | expected_reimbursement | priority_score | priority_rank | worklist_tag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 101 | 770000001 | 50000001 | Elena Marquez | BCBS of Arizona | COMMERCIAL | CO50 | 27447 | 2026-05-15 | 2026-06-07 | 180 | 2026-12-04 | **9** | AT_RISK | 58400.0 | 24850.0 | 49700.0 | **1** | AT_RISK |

days_remaining = 9 and AT_RISK, as specified. The hero is rank 1 by priority_score (2.0 × $24,850). The generator caps every non-hero encounter's expected dollars below $24,850, which keeps the hero at rank 1. The hero DOS is now 2026-05-15 (it was 2026-05-14 in the 2026-11-24 data).

## Finding: full refresh on an empty landing folder fails (CF_EMPTY_DIR_FOR_SCHEMA_INFERENCE)

Before the batch was landed, the orchestrator cleared the landing volume and then ran a full refresh while the folders were still empty. Three updates failed:

| Update | Start (UTC) | Trigger | Outcome |
|---|---|---|---|
| `541e3b60-d114-4f53-961d-79178f44d677` | 22:12:45 | API_CALL (full refresh) | FAILED 22:13:12 — `[CF_EMPTY_DIR_FOR_SCHEMA_INFERENCE] Cannot infer schema when the input path /Volumes/.../landing/claims/ is empty` (flows bronze_claims and 1 other) |
| `e541e788-7bab-4f3c-854d-a4753db13dda` | 22:13:15 | RETRY_ON_FAILURE | FAILED 22:13:38 — same error on `/landing/clinical_notes/` (bronze_clinical_notes) |
| `6e4d3cc8-e67e-4ec1-a982-655a0688b2e7` | 22:13:40 | RETRY_ON_FAILURE | CANCELED 22:13:56 |

Cause: Auto Loader cannot infer a schema from an empty input directory, so the streaming tables fail at analysis time. The fix is to land at least one file before the full refresh, which is what the successful update did (`7642a160…` at 22:14:57, after the batch was written at 22:14:15).

Effect on the job: none. The job's `generate_raw_data` task writes the landing batch before the `sdp_pipeline` task, and all three job runs passed. The failure only matters for a manual full refresh on an empty landing folder. Documented here as a finding; no code change was needed for the job.

## Column comments

Checked 2026-11-25 in `information_schema.columns`: 0 of 125 columns are missing a comment across `silver_claim_lines` (44), `silver_clinical_notes` (11), `mednecessity_ai_agent` (42), `medical_records` (9) and `gold_denial_worklist` (19).

## Deviations from SPEC (logged in docs/FINDINGS.md)

- `gold_denial_worklist` has the extra column `worklist_tag` (ADDENDUM 1).
- Clinical notes: 1,053 in the 2026-11-25 batch (1,024 in the 2026-11-24 batch). The SPEC's "~1,600" is not met; it is not a blocker.
- Labels: `eval_case_labels` has 500 rows as specified.

---

## SUPERSEDED: 2026-11-24 pipeline run (update `484a0992-3c06-4575-95ad-ebc1350bca72`, before the clean rerun)

Kept for audit only. Do not quote these figures (for example bronze notes 1,024, hero DOS 2026-05-14, label mix from that batch).


Workspace: https://fevm-appeals-hackathon.cloud.databricks.com (profile `fevm-appeals-hackathon`)
Catalog/schema: `appeals_hackathon_catalog.fe_bar_appeals`. Everything below is real output from this workspace.
The caseload is SYNTHETIC (seed 20261124, as_of 2026-11-24).

## Resource IDs

| Item | ID |
|---|---|
| Bundle | `med-nec-appeals-fe-bar` (target `default`, no `mode: development`) |
| Pipeline | `fe-bar-appeals-sdp`, id `4873b47b-47a7-4081-97c0-7cdf018c71a1`, serverless, channel CURRENT |
| Final update (FULL REFRESH, COMPLETED) | `484a0992-3c06-4575-95ad-ebc1350bca72` |
| Generator run (notebook task, serverless, `runs/submit`) | run_id `311595001702232` — SUCCESS (final batch) |

Superseded runs (kept for audit, not used for results): generator `1028752329320223` (old code, cancelled after success, its
landed batch was replaced), generator `37700291960340` (pre-`worklist_tag` bounding fix). Failed pipeline updates before the
final one: `29104b…`, `76f9b2…`, `aad585…`, `14552d…`, `c00603…`, `850408…`, all `ParseException` "Column without datatype"
(streaming-table column list needed types; fixed in `sdp/02_silver.sql` and `sdp/03_gold.sql`).

### Pipeline update state (2026-11-24) (event log, `event_log('4873b47b-…')`, update 484a09)

| Time (UTC) | State |
|---|---|
| 09:39:07 | create_update (API_CALL) |
| 09:39:09 | WAITING_FOR_RESOURCES |
| 09:39:18 | INITIALIZING |
| 09:39:31 | RESETTING (full refresh) |
| 09:39:32 | SETTING_UP_TABLES |
| 09:39:39 | RUNNING |
| 09:40:04 | **COMPLETED** |

### Expectation results (2026-11-24) (event log `flow_progress.data_quality`, update 484a09…)

Counts are per expectation over the rows evaluated in this update.

| Flow (dataset) | Expectation | Action | Passed | Failed |
|---|---|---|---|---|
| silver_claim_lines | carc_in_scope | DROP ROW | 536 | 2 |
| silver_claim_lines | composite_key_not_null | DROP ROW | 536 | 2 |
| silver_claim_lines | dos_before_denial_date | DROP ROW | 536 | 2 |
| silver_claim_lines | expected_reimbursement_non_negative | WARN | 536 | 2 |
| silver_clinical_notes | composite_key_not_null | DROP ROW | 1024 | 0 |
| silver_clinical_notes | note_date_present | DROP ROW | 1024 | 0 |
| silver_clinical_notes | note_text_present | DROP ROW | 1024 | 0 |

The 6 DROP failures (2 bad CARC `CO97`, 2 DOS after denial, 2 null composite key) are the deliberately injected defect
lines (`manifest.defects` in the landing `_manifests` folder). They are 1.1% of 538 landed lines. The 2 WARN rows are
negative EXPECTED_REIMBURSEMENT defects, kept as warnings. They reduce the expected dollars of their encounters, so that
is a known effect on the priority score of 2 encounters, and it is deliberate.

### Row counts per layer (2026-11-24) (final, after full refresh)

| Layer | Object | Rows | Note |
|---|---|---|---|
| Bronze | bronze_claims | 538 | Auto Loader, all landed claim lines incl. 8 defect lines |
| Bronze | bronze_clinical_notes | 1024 | |
| Silver | silver_claim_lines | 532 | 538 − 6 dropped (defects) |
| Silver | silver_clinical_notes | 1024 | no drops |
| Gold | mednecessity_ai_agent (MV) | 532 | claim-line grain, latest-wins dedupe, no duplicates |
| Gold | medical_records (MV) | 1024 | note grain |
| Gold | gold_denial_worklist (MV) | **500** | one row per encounter; 500 distinct (FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR) |
| Reference | mpfs_indicator_listing (MV) | 19116 | matches the legacy 2025 MPFS load count |

### Worklist trigger tags (2026-11-24) and deadline status (gold_denial_worklist)

| deadline_status | worklist_tag | Rows |
|---|---|---|
| AT_RISK | AT_RISK | 75 |
| OK | NEW (denied yesterday) | 20 |
| OK | OPEN | 365 |
| PAST_DUE | PAST_DUE | 40 |

Label mix (eval_case_labels joined to gold on the composite key, 500/500 matched):
WARRANTED 225, NOT WARRANTED 175, NEEDS REVIEW 100 (target 45/35/20 %). `eval_case_labels` has 500 rows for seed
20261124 / as_of 2026-11-24, and 33 distinct scenarios.

### Hero claim (2026-11-24) (gold row, Elena Marquez)

| FACILITY_ID | PATIENT_CONTROL_NUMBER | ENCOUNTER_NBR | patient_name | payer_name | payer_type | denial_code | hcpcs_codes | dos | denial_date | appeal_limit_days | appeal_deadline | days_remaining | deadline_status | total_charges | expected_reimbursement | priority_score | priority_rank | worklist_tag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 101 | 770000001 | 50000001 | Elena Marquez | BCBS of Arizona | COMMERCIAL | CO50 | 27447 | 2026-05-14 | 2026-06-06 | 180 | 2026-12-03 | **9** | AT_RISK | 58400.0 | 24850.0 | 49700.0 | **1** | AT_RISK |

days_remaining = 9 and AT_RISK, as specified. The hero is rank 1 by priority_score (2.0 × $24,850). The non-hero cap in the
generator (every non-hero encounter's expected dollars < $24,850) keeps it there.

### Column comments (2026-11-24)

All columns of `silver_claim_lines` (44), `silver_clinical_notes` (11), `mednecessity_ai_agent` (42), `medical_records` (9)
and `gold_denial_worklist` (19) have comments, checked in `information_schema.columns`. Table comments are set on every
bronze/silver/gold object.

### Deviations from SPEC (2026-11-24) (logged in docs/FINDINGS.md)

- `gold_denial_worklist` has the extra column `worklist_tag` (ADDENDUM 1).
- Clinical notes: 1,024 notes (about 2 per encounter). The SPEC text said "~1,600"; the template set gives 1,024. Not a
  blocker for any stage.
- Labels: the `eval_case_labels` count is 500 as specified.
