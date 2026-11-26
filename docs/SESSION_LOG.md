# Session log: FE Bar build, medical-necessity appeals

Conversation ID: `e2e3204c-874a-4e35-bf06-2aa699e64087` (Claude Code). Workspace `fevm-appeals-hackathon`, schema `appeals_hackathon_catalog.fe_bar_appeals`. All times UTC, 2026.

This log covers this build only. It was written after the work ran, from `docs/FINDINGS.md` and the evidence files. "Builder" means the person submitting the build. Decisions were approved at checkpoints.

The 2026-11-24 rows below are kept as history. Where a later row gives a different figure (the clean data-layer rerun, then the regenerated eval), the later row is current. §4 and §5 are the state at the end of the build; the final-state section at the end of this log supersedes any earlier figure.

---

## 1. Timeline

| Date (UTC) | Phase | What happened | Evidence |
|---|---|---|---|
| 11-24 | 1. Plan | Traceability matrix, P0/P1/P2 plan, target architecture, synthetic data spec, name map. Checkpoint 1: builder decisions in §2. | Plan kept outside the repo |
| 11-24 | 3. Build setup | Repo seeded from the earlier prototype (pipeline, agent, docs, app without build output). Shared `docs/SPEC.md` and append-only `docs/FINDINGS.md` created. | `docs/FINDINGS.md` |
| 11-24 | 3. Synthetic data | Seeded generator (seed `20261124`, 500 encounters, as-of 2026-11-24). Eval labels written to Delta only. 32 unit tests pass (local). | `evidence/01_generator_tests.txt` |
| 11-24 ~09:39 | 3. Lakeflow | SDP `fe-bar-appeals-sdp` full refresh completed. 6 defect lines dropped, 2 warned. Gold worklist: 500 rows. | `evidence/01_lakeflow_pipeline.md` |
| 11-24 | 3. Bootstrap | Criteria parsed (30 chunks), VS index built, descriptors extracted (83 rows), UC functions created. SQL functions that need later tables were deferred and created on a second pass. | `evidence/04_genai_generation.md` §1 |
| 11-24 09:14–10:00 | 3. Lakebase | Autoscaling project and database created. Synced worklist online (500 rows). Review state in UC. | `evidence/03_lakebase.md` |
| 11-24 09:49, 10:00 | 3. Generation | Two batches of 60 (hero first, then NEW, then priority). 0 rows rewritten across the two runs. Parser tests and SQL parity pass. | `evidence/04_genai_generation.md` §3 |
| 11-24 10:05–10:12 | 3. App | `fe-bar-appeals-app` deployed (AppKit). Review-action round trip returns 201, validation returns 400. NEEDS REVIEW cell layout fixed. | `evidence/06_app.md` |
| 11-24 10:19–10:21 | 3. Genie and governance | Genie Agent space created with a metric view over five objects. 14 of 14 benchmarks pass (120-row state). PHI tags applied. | `evidence/07_genie.md`, `evidence/02_governance.md` |
| 11-24 ~10:37 | 3. Job | End-to-end run `1038287240919742`: 10 of 10 tasks SUCCESS. 180 appeals, split superseded by the 11-25 rerun. | `evidence/08_job_run.md` |
| 11-24 10:45 | 3. Eval | 180-encounter eval on the pre-rerun data layer; superseded by the 11-25 run (see the final-state section). | `evidence/11_eval_180.md` |
| 11-24 (after job) | 3. Chat | `fe-bar-appeals-chat` READY (config v3) after the function re-creation fix. Hero question answered with dated evidence. | `evidence/09_chatbot.md` |
| 11-24 | 2. Business case | Model, sources and Checkpoint 2a cost estimate (partial billing). | `docs/business_case/` |
| 11-25 | 2. Cost | Checkpoint 2b measured from `system.billing` at list price: $0.107 variable, $0.51 fully loaded at 60 per day. | `evidence/10_cost_per_appeal.md` |
| 11-25 | 4. Narrative | README, `evidence/EVIDENCE.md` and this log drafted. Deck fixes pending. | This repo |
| 11-25 22:12–22:15 | 3. Pipeline | Clean data-layer rerun. Full refresh on the emptied landing folder failed three times (`CF_EMPTY_DIR_FOR_SCHEMA_INFERENCE`); the batch was landed (22:14:15) and full refresh `7642a160…` COMPLETED at 22:15:42. | `evidence/01_lakeflow_pipeline.md` |
| 11-25 22:16–22:44 | 3. Job | Three full job runs, all SUCCESS, 10 of 10 tasks each: `317191832078218`, `107638099811940`, `813247927527653`. Appeals 60 → 120 → 180 with no re-generation. Grounding summarised 460 encounters once (run 1). | `evidence/08_job_run.md` |
| 11-25 22:42 | 3. Eval | 180 encounters: 97.2% accuracy (175 of 180), 0.0% unsafe, 0 parse failures. Five misses, all routed to NEEDS REVIEW. | `evidence/11_eval_180.md` |
| 11-25 22:52 | 3. Genie | Benchmarks re-run on the 180-row state: 14 of 14 pass. | `evidence/07_genie.md` |
| 11-25 | 4. Refresh | Evidence, business-case numbers, deck and docs refreshed to the rerun. No PDF export. | This repo |
| — | 5. Readiness | Clean data-layer rerun done. Still open: secrets and name scan, private repo creation, attestation walk-through. | — |

---

## 2. Builder decisions

- **Ingest:** generator as a job task → UC volume `landing` → Auto Loader SDP. Not generation inside the pipeline.
- **Scale:** 500 denied encounters, seed `20261124`. At most 60 LLM calls per run.
- **Lakebase:** Autoscaling project, 0.5 CU, 300-second suspend.
- **Appeal windows:** 180 days commercial, 65 days Medicare Advantage, 60 days Medicaid (AHCCCS only), from public sources. Labelled as assumptions.
- **Source files:** only the public PDFs and spreadsheet. Not the earlier prototype's curated CSV or parquet.
- **Personas:** VP of Revenue Cycle (domain owner), CDAIO (technical), CFO (executive sponsor), Director of Denial Management (operational). The $12.8M figure is a placeholder to validate.
- **Access:** workspace group `fe-bar-appeals-reviewers`. Genie CAN_RUN and app CAN_USE granted to it, with approval.
- **Genie tab:** runs as the app SP. Approved 11-24 after the `genie` OBO scope did not take effect.
- **Deck framing:** three value tiers (Floor, Likely, Ceiling). Drop the earlier unsourced upside figure. Show $12.8M as a hypothesis tested and revised.
- **Schedule:** the daily job is PAUSED, to control cost.
- **Open:** the headline wording (see §5).

---

## 3. Issues hit and how they were fixed

| # | Issue | Fix |
|---|---|---|
| 1 | A SQL function cannot be created while its source table is missing (`42P01`). | Bootstrap defers `get_appeal`, `get_encounter` and `mpfs_lookup`. They are created on the re-run after grounding and generation. |
| 2 | First bootstrap run failed on a status-polling bug, after the criteria table and index were built. | Fixed. The re-run skipped built objects and completed. |
| 3 | Six failed SDP updates with `ParseException: Column without datatype`. | Typed the streaming table columns in `sdp/02_silver.sql` and `sdp/03_gold.sql`. |
| 4 | Lakebase synced table keeps uppercase column names. | Quote them in Postgres SQL. |
| 5 | Worklist returned 503 (Postgres `42703`): `data_sheet_pdf_path` missing in the synced table. | `pipeline/50_lakebase_sync.py` now left-joins the data-sheet path and MERGEs with schema evolution. Synced table took the new column. |
| 6 | Workspace-local group cannot receive UC grants (`PRINCIPAL_DOES_NOT_EXIST`). | Kept the workspace group for app and Genie ACLs. UC grants wait for an account-level group. |
| 7 | Chat endpoint stuck in `UPDATE_FAILED`: credential generation failed. Then ResponsesAgent needed an MLflow pin. | Pinned `mlflow[databricks]==3.1.0`. Redeployed. |
| 8 | After the job, chat failed: the job re-created UC functions mid-deploy, which invalidated the endpoint's passthrough (`no EXECUTE on get_appeal`). | Function creation is now `CREATE FUNCTION IF NOT EXISTS`. The bootstrap no longer grants EXECUTE to account users. Endpoint READY. Known issue recorded in `evidence/08_job_run.md`. |
| 9 | App chat returned 404, then 403. | Bound the `serving-endpoint` resource (CAN_QUERY) and wired it through `app/app.yaml`. |
| 10 | Genie tab returned Forbidden: `required scopes: genie`. `dashboards.genie` alone was not enough. Running apps keep old scopes until redeploy. | Added `genie` and redeployed. The forwarded token still lacked it, so the Genie tab moved to the app SP. Grants on five objects applied. |
| 11 | NEEDS REVIEW reasons (up to 8 items) overflowed the worklist table. | Worklist cell shows a one-line summary. The case file lists every item as text. |
| 12 | Tag policy allows only `u-nnpi`, `cui` or `pii` for `data_classification`. | Used `synthetic=true` as the key. Policy not changed. |
| 13 | A `USE SCHEMA` grant to the app SP appeared unexplained. | Confirmed: it comes from the app's volume binding (parent grants), not a manual grant. |
| 14 | Three encounters changed input hash after an upstream refresh (NEW count 23 to 20). | Not a grounding error. Four later rebuilds gave identical hashes. |
| 15 | Web-search tool auth error, so reference-file URLs could not be confirmed. | `data/SOURCES.md` still says TODO for the four URLs. |
| 16 | Google Sheets connector returned `invalid_grant`. | Used the gcloud CLI path for the business-case sheet and the deck. |
| 17 | CLI token expiry. | Re-login with `DATABRICKS_AUTH_STORAGE=plaintext`. |
| 18 | Permission check blocked unapproved grants and sharing. | Asked before each grant. Approved grants are listed in §2. |
| 19 | Full refresh on an empty landing folder failed (`CF_EMPTY_DIR_FOR_SCHEMA_INFERENCE`: Auto Loader cannot infer a schema from an empty directory). | Land a batch before any manual full refresh. The job is not affected, because `generate_raw_data` runs first. |
| 20 | Three of the four WARRANTED eval misses in the rerun are SCS charts whose billed DOS has no matching procedure note. | Open item for the generator. Not regenerated in this refresh. Documented in `evidence/11_eval_180.md`. |

---

## 4. Known gaps (state at the end of the build)

- Reviewer UC grants not applied (needs an account-level group). Column masks are applied on 7 PHI columns; the non-member path is verified at logic level only.
- Grounding is incremental through the digest cache (`encounter_digest_cache`). Run 1 summarised 460 encounters; runs 2 and 3 summarised none.
- Genie benchmarks re-run 2026-11-25 on the 180-row state: 14 of 14 pass.
- The app was checked by API calls, unit tests and a build. No recorded browser visual test.
- MLflow GenAI judge: done on 60 rows (`genai_evaluate`). The full 180 is not run (estimate about $7.2, above the $5 cap). Chat-agent tracing: no traces found yet.
- The hero's full letter and data sheet are PDFs, not text in the repo.

---

## 5. Open items (end of build)

1. Headline wording: resolved 2026-11-25. Naveen chose the payback wording (`docs/business_case/DECK_NUMBERS.md` §7).
2. Deck v2: done and exported to `docs/deck/` (PDF, 18 pages). Slide speaker notes are on all main-story slides.
3. Public reference URLs: resolved. `data/SOURCES.md` has no TODO markers left.
4. Customer naming: decided 2026-11-25 (anonymized). The customer-name token still appears in two older EMU commits; see the final-state section.
5. Revoke or keep the EXECUTE grants to account users from an earlier bootstrap run.
6. Create the account-level reviewer group. Then apply `governance/02_reviewer_grants.sql` (`lakebase/APP_GRANTS.md`).
7. Grounding incremental: done (digest cache, 2026-11-25).
8. Chat endpoint scale-to-zero: about $13.5 per day idle with it off. Decide for the demo.
9. Genie benchmarks re-run on the current state: done (2026-11-25, 14 of 14).
10. Code review pass and `evidence/12_code_review_tests.txt`: done (2026-11-25 pass, tests recorded).
11. Commit a text dump of the hero's data sheet and letter.
12. Done: column masks on PHI columns, MLflow GenAI judge (60 rows). Not done: row filters; chat-agent tracing.
13. Readiness: the clean data-layer rerun is done. Publication is done (private repo with full history; public mirror as a clean snapshot). Still open: README §6 in Naveen's words, and the attestation walk-through.
14. Generator: the five WARRANTED misses in the current eval are three SCS trial charts and two bariatric cases. One bariatric case's payer criteria document is not in the corpus (a genuine criteria gap). Not regenerated.

## 2026-11-25 — Anonymization (Naveen chose anonymize; decision record in docs/deck/NAMING_CHECK.md)
- Repo text: the customer name, product names and logo removed from README, docs, business case, evidence and data/SOURCES.md. Customer name becomes "a large multi-state nonprofit health system (HQ Arizona)" on first mention, then "the health system". Public payer and regulatory facts kept (BCBS of Arizona / AZ Blue, AHCCCS, CMS, Medicare Advantage, CARC).
- Customer-identifying links (own financial pages and filings, trade-press articles naming it, tax-filing identifiers) withheld from committed files; figures kept with generic sources. Full links kept in the private Sheet (see docs/business_case/SOURCES.md note).
- Bundle and repo renamed to med-nec-appeals-fe-bar in text. Local paths written as <repo>. Personal workspace path and builder email replaced with <builder>.
- Evidence samples: letter headers show [Health System] with a "customer name redacted" note.
- Deck: copy created in personal My Drive (original untouched): https://docs.google.com/presentation/d/1oPXZ7xKcxyqLRRHgfWh-xtSI6TNiSQffcUgJuf0i9RU/edit . Customer name, logo and grey band removed from all 17 slides and speaker notes; restyled to Barlow with Databricks navy #1B3037 and red #FF3621 subtitles. Validation: 0 errors, 23 element_overlap warnings (cover title/subtitle spacing fixed).
- Business-case numbers unchanged by the anonymization. The deck, DECK_NUMBERS.md, README and DECK.md were refreshed to the regenerated numbers afterwards (see the final-state section).

---

## Final state (end of build)

What changed after the 2026-11-25 rerun, in order. Figures here are current; earlier rows are history.

**Hardening.**
- Grounding uses a digest cache (`encounter_digest_cache`, keyed by `notes_hash`). Only new or changed notes reach `ai_summarize`. Pruning is guarded.
- Column masks (`mask_phi`, `mask_phi_ts`) on 7 PHI columns: `appeals_output.patient_name`, `data_sheet_facts` (name, member ID, DOB), `encounter_grounding` (name, member ID, DOB). Members of the workspace group and the app SP see real values. Others see `***MASKED***` (NULL for DOB). Retention through the grounding rebuild was verified.
- MLflow GenAI evaluation (`pipeline/65_genai_evaluate.py`) on 60 stored generations with the claude-sonnet-4-6 judge. Groundedness was 83.3% before the judge's context was fixed to include claim identifiers, and is 98.3% after. Judge run: groundedness 98.3%, no fabricated evidence 96.7%, label match 95.0%. The job refuses a run whose estimated judge cost exceeds `genai_cost_cap_usd` ($5).
- Job has 11 tasks. `genai_evaluate` runs after `evaluate`.
- Code review fixes recorded in `docs/CODE_REVIEW.md`.

**Eval on 180 (regenerated, neutral prompt).** 72 WARRANTED / 66 NOT WARRANTED / 42 NEEDS REVIEW. Accuracy 97.2% (175 of 180). Unsafe 0%. The five misses all went to NEEDS REVIEW. Quotes: 54.7% strict and 85.3% normalised. Source: `evidence/11_eval_180.md`.

**Deck v2.** Title "Automate the Appeal. Recover the Revenue." Main story of 11 slides (cover to the ask) plus seven appendix slides, on the Databricks template. Flow: stakes, scorecards, problem with the hero denial, workflow with the hero thread, platform, demo, proof, pilot, ask. Architecture slide built from `docs/deck/ARCH_SLIDE_SPEC.json`. PDF at `docs/deck/FE_Bar_Medical_Necessity_Appeals_POV.pdf` (18 pages). Text map in `docs/deck/DECK.md`.

**App UX.**
- Full-height assistant sidebar (chat agent and Genie tab in one instance).
- Recommendation chips with counts (WARRANTED, NOT WARRANTED, NEEDS REVIEW).
- "≥ $10K expected" toggle and an expected-$ sort.
- Edited-letter preview with "Show changes" and a PDF download in the browser.

**Filters.** Worklist search, recommendation chips, the ≥ $10K toggle and sort are server-side query parameters (`min_expected`, `recommendation`, `sort`). Covered by `app/server/worklist.test.ts` and `app/client/src/lib/worklistQuery.test.ts`.

**Tests.** Python 79 (`generator/tests`, `genai/`). App 73 (Vitest).

**Grants.** Postgres grants applied, serving endpoint CAN_QUERY, Genie space CAN_RUN, SP SELECT on the 5 Genie objects. Only the reviewer UC grants are pending (account-level group). See `lakebase/APP_GRANTS.md`.

**Publication.** Private EMU repo `naveen-sangana_data/med-nec-appeals-fe-bar` with full history. Public mirror `nsangana/med-nec-appeals-fe-bar` is a clean snapshot of the final tree. The customer-name token appears in two older EMU commits in the private history; the snapshot and the working tree do not contain it.
