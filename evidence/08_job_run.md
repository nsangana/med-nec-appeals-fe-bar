# Evidence 08 — Lakeflow Job end-to-end runs (`fe-bar-appeals-job`, job id 211997391364769)

REFRESHED 2026-11-26 (UTC). Workspace fevm-appeals-hackathon (synthetic data). Three full job runs after the anonymization regeneration (neutral generation prompt), all with seed `20261124`, all SUCCESS. Times are UTC. A fourth run (`263358598052015`) ran only the MLflow judge task (`genai_evaluate`, see evidence/14).

History: earlier runs are in git history.

## Runs

| # | run_id | start (UTC) | end (UTC) | duration | result |
|---|---|---|---|---|---|
| 1 | 226702601398182 | 02:38:32 | 02:47:54 | 9m 21s | SUCCESS |
| 2 | 514812180001706 | 02:48:07 | 02:55:55 | 7m 48s | SUCCESS |
| 3 | 32756035496628 | 03:03:23 | 03:11:42 | 8m 18s | SUCCESS |
| judge | 263358598052015 | 04:23:14 | 04:25:01 | 1m 47s | SUCCESS (`genai_evaluate` only; the other 10 tasks DISABLED) |

Query for the task tables: `databricks jobs get-run <run_id> -o json` (the `tasks[]` array). Durations are `end_time - start_time` per task.

## Task tables (execution duration in seconds)

| Task | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| generate_raw_data | SUCCESS 18 | SUCCESS 17 | SUCCESS 29 |
| bootstrap | SUCCESS 22 | SUCCESS 21 | SUCCESS 37 |
| data_sheet_facts | SUCCESS 6 | SUCCESS 6 | SUCCESS 7 |
| sdp_pipeline | SUCCESS 62 | SUCCESS 73 | SUCCESS 62 |
| register_tools | SUCCESS 34 | SUCCESS 33 | SUCCESS 66 |
| lakebase_sync | SUCCESS 75 | SUCCESS 75 | SUCCESS 78 |
| evaluate | SUCCESS 31 | SUCCESS 29 | SUCCESS 45 |
| generate_appeals | SUCCESS 260 | SUCCESS 230 | SUCCESS 246 |
| grounding | SUCCESS 12 | SUCCESS 13 | SUCCESS 12 |
| render_pdfs | SUCCESS 128 | SUCCESS 55 | SUCCESS 66 |

All 30 task executions in the three runs are SUCCESS. The judge run is `263358598052015` (task `genai_evaluate` SUCCESS, 106 s).

## Incrementality: 60 → 120 → 180, no re-generation

`appeals_output` is a MERGE keyed on the encounter, with a generator cap of 60 per run. Batch counts are from evidence/04 §2 (same runs).

| After run | Rows in appeals_output | Written in this run (generated_at, UTC) | WARRANTED / NOT WARRANTED / NEEDS REVIEW in this run |
|---|---|---|---|
| 1 | 60 | 60 at 02:40 | 22 / 21 / 17 |
| 2 | 120 | 60 at 02:49 | 31 / 19 / 10 |
| 3 | 180 | 60 at 03:05 | 19 / 26 / 15 |

Cumulative after run 3 (re-queried 2026-11-26): WARRANTED 72, NOT WARRANTED 66, NEEDS REVIEW 42 (= 180).

Generator (`generate_raw_data`): the landing folder holds the claims batch for seed `20261124`. `eval_case_labels` has 500 rows.

## Row counts after run 3 (re-queried 2026-11-26)

| Object | Rows |
|---|---|
| bronze_claims | 538 |
| bronze_clinical_notes | 1,053 |
| silver_claim_lines | 532 |
| silver_clinical_notes | 1,053 |
| gold_denial_worklist | 500 |
| encounter_grounding | 450 |
| encounter_digest_cache | 450 |
| data_sheet_facts | 450 |
| appeals_output | 180 |
| eval_case_labels | 500 |
| eval_summary (table, 3 rows; current run is the 180-row one) | 3 |
| genai_eval_summary (table, 2 rows; current run is `a91c3794…`) | 2 |
| worklist_serving (Delta, via synced table) | 500 |
| review_state_uc | 3 |

Grounding is 450 rows, not 500, because 50 encounters are PAST_DUE on the 2026-11-26 date and have no grounding.

## Recommendation and worklist mix (re-queried 2026-11-26)

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

NEW = 0 on this date. Worklist tags and `days_remaining` are computed against the current date at refresh. The daily job with that day's `as_of` repopulates NEW.

## Latest deterministic eval (from run 3, see evidence/11)

| run_ts | encounters_evaluated | accuracy | unsafe_rate | quote_verified_rate (strict) | quote_verified_rate_normalised | parse_failures |
|---|---|---|---|---|---|---|
| 2026-11-26T03:09:43.482Z | 180 | 0.9722 | 0.0 | 0.5472 | 0.8532 | 0 |

## Known issues found by these runs

- None blocking. An intermediate regeneration attempt failed on a SQL quoting bug introduced by the prompt edit. It was fixed and is guarded by `genai/test_sql_quotes.py`.
- The empty-directory failure of the full refresh (evidence/01) is a pre-run condition, not a job-task failure, because `generate_raw_data` runs first in the job.
- Worklist and `days_remaining` values move with the UTC date. The three runs ran on 2026-11-26 UTC.
