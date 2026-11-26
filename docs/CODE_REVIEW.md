# Code review: FE Bar appeals build

Scope: generator/, sdp/, pipeline/*.py|*.sql, genai/, agent/, lakebase/, governance/, genie/, tools/, resources/,
app/server, app/client/src (node_modules and dist skipped). Reviewed 2026-11-25. Evidence: `evidence/12_code_review_tests.txt`.

Counts: **High 6** (5 fixed, 1 flagged for the orchestrator), **Medium 6** (3 fixed, 3 left with reasons),
**Low 7** (5 real, left with reasons; 2 are good-practice notes), **Info 4**.

| # | Sev | File:line | Issue | Fix | Status |
|---|---|---|---|---|---|
| 1 | High | pipeline/40_render_pdfs.py:67 (used at 150, 154) | LLM and clinical-note text was converted to HTML with raw tags allowed, then rendered by xhtml2pdf, which fetches `<img>`/`<link>` resources. Prompt-injected notes could read local files or make outbound fetches from the job. | `md_html` HTML-escapes the text before `markdown.markdown`. Verified: raw `<img>`/`<link>` become text; bold and tables still render. Side effect: a leading `>` no longer makes a blockquote. | Fixed, verified |
| 2 | High | app/server/server.ts:256 (review-actions) | The UI does not gate EDIT/APPROVE/SUBMIT. The server accepted them for NOT WARRANTED, NEEDS REVIEW and NOT GENERATED cases, so a letter-less case could be "submitted". Breaks the never-fabricate rule. | Server looks up the case (CASE_SQL) and returns 409 unless the recommendation is WARRANTED for EDIT/APPROVE/SUBMIT. ROUTE_TO_REVIEW and REJECT stay open. Helper `reviewActionAllowed` in worklist.ts. | Fixed, 2 unit tests (24 app tests pass). Needs app redeploy (orchestrator). |
| 3 | High | pipeline/20_encounter_grounding.sql (was whole file) | `CREATE OR REPLACE` plus `ai_summarize` over every grounded encounter on every run (about 460 LLM calls per run). | Digests cached in `encounter_digest_cache` keyed by `notes_hash` (sha2 of the dated notes). Only `encounter_digest_pending` (new or changed notes) reaches `ai_summarize`. Pruning is guarded. `input_hash` expression and `notes_full` are unchanged. | Fixed. Proven on a scratch copy (see evidence section 5). |
| 4 | High | generator/core.py (`_build_encounter`, TKA templates) | Laterality defect. For lateralized TKA, the modifier and ICD-10 (M17.11/M17.12, M25.561/562) were random (LT 30%), but the note text always said "right knee" and "27447-RT". Accounts 770000219 and 770000306 (LT) had right-knee notes. | `_NoteCtx` carries `side` and `mod`. All TKA templates use them. Hero stays RT (text unchanged). | Fixed. Tests: `test_tka_modifier_matches_side_documented_in_notes`, `test_tka_warranted_ortho_note_cites_modifier`, `test_hero_tka_note_is_right_knee_rt`. Needs data regeneration (the note text of LT encounters changed). |
| 5 | High | pipeline/60_evaluate.py:42-53 | `eval_case_labels` holds one batch per (seed, as_of). The join took every batch, so a rerun with a new `as_of` double-counted every encounter (360 rows instead of 180 in a scratch test). | Join only the latest label per encounter (QUALIFY row_number by as_of_date, generator_seed desc). | Fixed. Verified: old join 360, new join 180, against production appeals_output. |
| 6 | High | (repo hygiene) docs/e2e3204…jsonl | Session transcript with discovery-call context was in the repo tree, and the handoff says not to commit it. | Already absent from docs/ at review time. | Confirmed gone. Keep it out of the repo before the first commit. |
| 7 | Medium | agent/agent.py `_to_lc` | Client-supplied `system` role messages were forwarded to the LLM, so a caller could override instructions. | `system` messages are dropped. Instructions come only from SYSTEM_PROMPT. Unused SystemMessage import removed. | Fixed (not unit-tested: module imports Databricks/LangGraph; inspected). |
| 8 | Medium | pipeline/60_evaluate.py:33; agent/build_and_deploy.py:38, 60 | Real user email in MLflow experiment paths and the agent workspace path (committed code and comments). | `/Shared/fe-bar-appeals-eval`, `/Shared/fe-bar-appeals-chat`. agent_file from env `FEBAR_AGENT_FILE` with a Shared default. | Fixed. Note: experiment paths change, so old runs stay under the old path. |
| 9 | Medium | app/server/server.ts:31 (chatSchema) | Chat endpoint had no size or turn limits; each request is a paid LLM call. | Max 20 messages, 4,000 chars per message, context fields bounded. | Fixed (zod; typecheck and tests pass). |
| 10 | Medium | app/server/server.ts (Genie plugin subclass) and worklist/case routes | Genie runs as the app service principal, and the worklist and case routes read Lakebase as the SP. Every app user sees all encounters and PHI. Documented as a decision (2026-11-24), but it is not per-user authorization. | Left. | Open decision for Naveen. Prototype with a reviewer group only. |
| 11 | Medium | sdp/02_silver.sql:54 (warn-kept negative lines) → sdp/03_gold.sql:125 | Lines with negative EXPECTED_REIMBURSEMENT are warned but kept. Gold `sum(EXPECTED_REIMBURSEMENT)` and the $ metrics include them, so dollars are understated (injected defect rows). | Left: documented demo design. | Decide whether gold should exclude warn-kept lines before the deck quotes $ figures. |
| 12 | Medium | pipeline/30_generate_appeals.sql (prompt) | Clinical notes are untrusted text in the prompt. The parser checks format only; a prompt injection can flip the determination (WARRANTED with letter). The eval unsafe_rate measures this, but nothing blocks it. | Left: known risk. | Mention in README limitations. |
| 13 | Low | pipeline/50_lakebase_sync.py:102 | `CREATE OR REPLACE TABLE review_state_uc` runs every job. Grant check: the app SP SELECT grant survived the 10:47 replace (same UC table id, grant still present). | Left. Works on this UC behaviour; INSERT OVERWRITE would be safer. | Left, verified. |
| 14 | Low | pipeline/00_bootstrap.py:24-25; 40, 50, 60 | Catalog/schema hard-coded instead of job parameters. No injection (constants), but a bundle with another schema would write to this one. | Left. | Document. |
| 15 | Low | pipeline/10_generate_raw_data.py | Identifiers validated (`[A-Za-z0-9_]+`), labels deleted with bound params. | None needed. | Info, good. |
| 16 | Low | generator/writer.py:20 | Manifest temp file lands in `_manifests/` (not `_staging/`) on crash. Not an Auto Loader source, so harmless. | Left. | Low. |
| 17 | Low | tools/run_sql.py `split_sql` | `/* */` block comments are not handled, so an apostrophe inside one breaks statement splitting. | Left (no current file has one). | Low. |
| 18 | Low | lakebase/create_synced_table.sh | Temp JSON in /tmp is left behind if the create fails (no secret inside). | Left. | Low. |
| 19 | Low | app/client/src/components/*.tsx | LLM text rendered as React text nodes, no dangerouslySetInnerHTML. PDF iframes use server-issued URLs. | None needed. | Info, good. |
| 20 | Info | lakebase/setup_lakebase.sh | Token passed via `PGPASSWORD` env, never printed or written. | None. | Info, good. |
| 21 | Info | repo scan | No `dapi` tokens or passwords in code. `app/.env` (profile and endpoint names only) is gitignored. Old names appear only in docs and in a test that asserts their absence. | None. | Info. |
| 22 | Info | pipeline/30, genai/appeal_parser.py | Python parser and SQL parse rules are the same; 14 parser tests. | None. | Info. |
| 23 | Info | genie/00_cost_assumptions.sql | MERGE with no WHEN MATCHED, so a rerun never overwrites the measured cost. | None. | Info, good. |

## Changes made (files)
- `generator/core.py`: TKA laterality via `_NoteCtx(side, mod)`; SCS WARRANTED template (dated lumbar MRI, named PMA-approved device, labeled indication).
- `generator/tests/test_generator.py`: 5 new tests (laterality x3, SCS template and batch chart x2).
- `pipeline/20_encounter_grounding.sql`: incremental digest cache (encounter_notes_current, encounter_digest_cache, encounter_digest_pending, MERGE, guarded prune).
- `pipeline/40_render_pdfs.py`: escape LLM markdown before conversion.
- `pipeline/60_evaluate.py`: latest-label join; Shared experiment path.
- `agent/agent.py`: drop client system messages; remove unused import.
- `agent/build_and_deploy.py`: no personal paths (env override, Shared experiment).
- `app/server/worklist.ts`, `app/server/server.ts`: review-action guard; chat limits.
- `app/server/worklist.test.ts`: guard tests.

## Open items for the orchestrator
- Rerun must regenerate data (TKA LT note text changed; SCS WARRANTED chart changed). Use a new run with the same seed; labels remain valid.
- First run after deploy summarises every encounter once (cache is new). Later runs summarise only changed notes.
- Redeploy the app (server.ts changed). Pass an explicit `as_of_date` when rerunning so the label batch is intentional.
- Decide items 10, 11 and 12 before the deck quotes $ or claims per-user access control.
