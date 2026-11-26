# Evidence 08 — Lakeflow Job end-to-end runs (`fe-bar-appeals-job`, job id 211997391364769)

REFRESHED 2026-11-25 after the clean data-layer rerun. Workspace fevm-appeals-hackathon (synthetic data).
Three full job runs, all with `as_of_date=2026-11-25`, seed `20261124`, all SUCCESS. Times below are UTC; the handoff's local times (PST, UTC-8) are in brackets.

| # | run_id | start (UTC) | end (UTC) | duration | result |
|---|---|---|---|---|---|
| 1 | 317191832078218 | 22:16:13 [14:16] | 22:27:28 [14:27] | 11m 15s | SUCCESS |
| 2 | 107638099811940 | 22:27:45 [14:27] | 22:36:24 [14:36] | 8m 39s | SUCCESS |
| 3 | 813247927527653 | 22:36:39 [14:36] | 22:44:22 [14:44] | 7m 43s | SUCCESS |

Local-time labels follow the handoff (14:27 / 14:36 / 14:44 Pacific). Query for the task tables: `databricks jobs get-run <run_id> -o json` (the `tasks[]` array), durations from `end_time - start_time` per task.

## Task tables (`jobs get-run`, execution duration in seconds)

| Task | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| bootstrap | SUCCESS 32 | SUCCESS 29 | SUCCESS 19 |
| generate_raw_data | SUCCESS 24 | SUCCESS 15 | SUCCESS 15 |
| sdp_pipeline | SUCCESS 63 | SUCCESS 62 | SUCCESS 62 |
| grounding | SUCCESS 110 | SUCCESS 12 | SUCCESS 11 |
| data_sheet_facts | SUCCESS 8 | SUCCESS 6 | SUCCESS 6 |
| generate_appeals | SUCCESS 248 | SUCCESS 245 | SUCCESS 230 |
| evaluate | SUCCESS 25 | SUCCESS 30 | SUCCESS 29 |
| register_tools | SUCCESS 30 | SUCCESS 34 | SUCCESS 32 |
| render_pdfs | SUCCESS 124 | SUCCESS 57 | SUCCESS 55 |
| lakebase_sync | SUCCESS 91 | SUCCESS 112 | SUCCESS 74 |

All 30 task executions are SUCCESS. Run 1 is the first run after the full refresh, so it carries the one-time grounding summaries (110 s). Runs 2 and 3 take about 11–12 s there, because nothing needs summarising.

## Incrementality: 60 → 120 → 180, no re-generation

`appeals_output` (MERGE keyed on the encounter; generator cap 60 per run):

| After run | Rows in appeals_output | Written in this run (generated_at, UTC) | WARRANTED / NOT WARRANTED / NEEDS REVIEW in this run |
|---|---|---|---|
| 1 | 60 | 60 at 22:19 | 24 / 22 / 14 |
| 2 | 120 | 60 at 22:29 | 26 / 16 / 18 |
| 3 | 180 | 60 at 22:38 | 23 / 26 / 11 |

Cumulative after run 3: WARRANTED 73, NOT WARRANTED 64, NEEDS REVIEW 43 (= 180). No row carries a second `generated_at` value, so the rows written in runs 1 and 2 were not regenerated in runs 2 and 3.

Generator (`generate_raw_data`): the landing folder holds one claims batch, `batch_2026-11-25_seed20261124_n500.json`, with `last_modified` 2026-11-25T22:14:15Z. That timestamp is unchanged after runs 2 and 3, so the generator skipped re-landing (idempotent per batch name). `eval_case_labels` stays at 500 rows.

## Grounding-cache proof (`encounter_digest_cache`)

| Run | Digests written | Evidence |
|---|---|---|
| 1 | 460 | all 460 `digested_at` values = 2026-11-25T22:17:56Z (min = max) |
| 2 | 0 | no `digested_at` moved; `encounter_digest_pending` empty after run 3 |
| 3 | 0 | same |

The cache keeps one row per encounter with `notes_hash` and `clinical_digest`. A digest is recomputed only when the notes hash changes, so ai_summarize runs once per encounter (460 calls in run 1, none after). The job task output is SQL (no notebook exit value), so this proof comes from the table timestamps, not from a log line.

## Row counts after run 3

| Object | Rows |
|---|---|
| bronze_claims | 538 |
| bronze_clinical_notes | 1,053 |
| silver_claim_lines | 532 |
| silver_clinical_notes | 1,053 |
| gold_denial_worklist | 500 |
| encounter_grounding | 460 |
| encounter_digest_cache | 460 |
| data_sheet_facts | 460 |
| appeals_output | 180 |
| eval_case_labels | 500 |
| eval_summary (rows) | 3 (one per run, 60 / 120 / 180) |
| worklist_serving (Lakebase, via synced table) | 500 |

## Latest eval (from run 3, see evidence/11)

| run_ts | encounters_evaluated | accuracy | unsafe_rate | quote_verified_rate | quote_verified_rate_normalised | parse_failures |
|---|---|---|---|---|---|---|
| 2026-11-25T22:42:27.948Z | 180 | 0.9722 | 0.0 | 0.5309 | 0.8712 | 0 |

## Pipeline updates started by the job (SDP `fe-bar-appeals-sdp`, incremental)

| Job run | SDP update | Start (UTC) | Result |
|---|---|---|---|
| 1 | 49faa9c8-c13f-4145-8d46-619512f0673e | 22:16:43 | COMPLETED 22:17:41 |
| 2 | 0d9b4523-1b2f-4ce9-94ac-d49672bb28a5 | 22:28:06 | COMPLETED 22:28:57 |
| 3 | 39f8431e-d4c2-425e-96ac-5865c09549a6 | 22:37:00 | COMPLETED 22:37:54 |

These are not full refreshes. The full refresh that preceded them is in evidence/01.

## Known issues found by these runs

- None blocking. The empty-directory failure of the full refresh (evidence/01) is a pre-run condition, not a job-task failure, because `generate_raw_data` runs first in the job.

---

## SUPERSEDED: 2026-11-24 job run (job run `1038287240919742`, before the clean rerun)

Kept for audit only. These figures came from the earlier data layer and the 2026-11-24 landing. Do not quote them.


Real run on workspace fevm-appeals-hackathon (synthetic data). Job id 211997391364769, run id 1038287240919742, triggered by `databricks bundle run` on 2026-11-24.

| Task | Result | Duration (s) |
|---|---|---|
| bootstrap | SUCCESS | 66 |
| generate_raw_data | SUCCESS | 33 |
| sdp_pipeline | SUCCESS | 73 |
| grounding | SUCCESS | 131 |
| data_sheet_facts | SUCCESS | 6 |
| generate_appeals | SUCCESS | 231 |
| evaluate | SUCCESS | 31 |
| register_tools | SUCCESS | 41 |
| render_pdfs | SUCCESS | 59 |
| lakebase_sync | SUCCESS | 90 |

Overall: SUCCESS | start 1795516646640 | end 1795517265609 (epoch ms)

### Row counts after the 2026-11-24 run

| t | n |
|---|---|
| worklist_serving (Lakebase) | 500 |
| bronze_claims | 538 |
| silver_claim_lines | 532 |
| gold_denial_worklist | 500 |
| encounter_grounding | 460 |
| data_sheet_facts | 460 |
| appeals_output | 180 |
| worklist_serving (Delta) | 500 |
| review_state_uc | 3 |

### Appeals by recommendation (2026-11-24) (cumulative, 3 incremental batches)

| recommendation | n | letters |
|---|---|---|
| NEEDS REVIEW | 46 | 0 |
| NOT WARRANTED | 64 | 0 |
| WARRANTED | 70 | 70 |

### Latest eval summary (2026-11-24)

| run_ts | encounters_evaluated | accuracy | unsafe_rate | quote_verified_rate | quote_verified_rate_normalised | parse_failures |
|---|---|---|---|---|---|---|
| 2026-11-24T10:45:35.994Z | 180 | 0.9556 | 0.0 | 0.5594 | 0.8752 | 0 |
| 2026-11-24T10:06:51.238Z | 120 | 0.9667 | 0.0 | 0.5529 | 0.8736 | 0 |

### Known issue found on 2026-11-24 (fixed)

- bootstrap/register_tools re-created the UC functions with CREATE OR REPLACE, invalidating the chat endpoint's auth passthrough mid-deploy. 00_bootstrap.py now uses CREATE FUNCTION IF NOT EXISTS (deployed after this run).

printf '\n\n## Regeneration after anonymization (2026-11-25 local / 2026-11-26 UTC) — CURRENT\n\nThe generation prompt was neutralized (no customer name; `[Health System Name]` letterhead placeholder). appeals_output, eval tables and PDFs were reset, then three full runs regenerated all appeals (an intermediate attempt failed on a SQL quoting bug introduced by the prompt edit, fixed and guarded by `genai/test_sql_quotes.py`).\n\n| Run | Result |\n|---|---|\n'

for r in 226702601398182 514812180001706 32756035496628

for r in 226702601398182 514812180001706 32756035496628

for r in 226702601398182 514812180001706 32756035496628

printf '\nAfter the 3 runs:\n\n'

tools/run_sql.py "SELECT recommendation, count(*) n, count(letter_pdf_path) letters FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_output GROUP BY 1 ORDER BY 1"

tools/run_sql.py "SELECT worklist_tag, count(*) n FROM appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist GROUP BY 1 ORDER BY 1"

printf 'Worklist tags and days_remaining are computed against the current date at refresh; the UTC date rolled to 2026-11-26 during these runs (NEW = 0, 10 more PAST_DUE, 450 grounded). The daily job with that day'"'"'s as_of repopulates NEW.\n'


## Regeneration after anonymization (2026-11-25 local / 2026-11-26 UTC) — CURRENT

The generation prompt was neutralized (no customer name; `[Health System Name]` letterhead placeholder). appeals_output, eval tables and PDFs were reset, then three full runs regenerated all appeals (an intermediate attempt failed on a SQL quoting bug introduced by the prompt edit, fixed and guarded by `genai/test_sql_quotes.py`).

| Run | Result |
|---|---|
| 226702601398182 | SUCCESS (10 tasks) |
| 514812180001706 | SUCCESS (10 tasks) |
| 32756035496628 | SUCCESS (10 tasks) |

After the 3 runs:

| recommendation | n | letters |
|---|---|---|
| NEEDS REVIEW | 42 | 0 |
| NOT WARRANTED | 66 | 0 |
| WARRANTED | 72 | 72 |

| worklist_tag | n |
|---|---|
| AT_RISK | 67 |
| OPEN | 383 |
| PAST_DUE | 50 |

Worklist tags and days_remaining are computed against the current date at refresh; the UTC date rolled to 2026-11-26 during these runs (NEW = 0, 10 more PAST_DUE, 450 grounded). The daily job with that day's as_of repopulates NEW.
