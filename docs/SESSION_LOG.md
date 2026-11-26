# Session log: FE Bar build, medical-necessity appeals

Conversation ID: `e2e3204c-874a-4e35-bf06-2aa699e64087` (Claude Code). Workspace `fevm-appeals-hackathon`, schema `appeals_hackathon_catalog.fe_bar_appeals`. All times UTC, 2026.

This log covers this build only. It was written after the work ran, from `docs/FINDINGS.md` and the evidence files. "Builder" means the person submitting the build. Decisions were approved at checkpoints.

The 2026-11-24 rows below are kept as history. Where a 2026-11-25 row gives a different figure (the clean data-layer rerun), the 2026-11-25 row is current.

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
| 11-24 ~10:37 | 3. Job | End-to-end run `1038287240919742`: 10 of 10 tasks SUCCESS. Appeals 180 (70 / 64 / 46). | `evidence/08_job_run.md` |
| 11-24 10:45 | 3. Eval | 180 encounters: 95.6% accuracy, 0.0% unsafe, 0 parse failures. | `evidence/11_eval_180.md` |
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

## 4. Known gaps at the time of writing

- Reviewer UC grants not applied (needs account-level group). No column masks or row filters.
- Grounding is now incremental through the digest cache (`encounter_digest_cache`). Run 1 summarised 460 encounters; runs 2 and 3 summarised none.
- Genie benchmarks re-run 2026-11-25 on the 180-row state: 14 of 14 pass.
- App not checked in a browser (SSO). Checks were API calls and the build.
- MLflow tracing, `mlflow.genai.evaluate`, and groundedness scorer are not implemented.
- The hero's full letter and data sheet are PDFs, not text in the repo.

---

## 5. Open items

1. Headline wording: resolved 2026-11-25. Naveen chose the payback wording (`docs/business_case/DECK_NUMBERS.md` §7). The 20× wording is retired.
2. Deck: ROI wording, speaker notes, Appendix B citation (`[[TBD]]`), PDF export, commit `docs/deck/DECK.md`.
3. Public reference URLs: resolved. `data/SOURCES.md` has no TODO markers left.
4. Check the FE Bar FAQ for whether a real customer name and branding are allowed in the repo and deck. Not checked yet. Otherwise anonymise.
5. Revoke or keep the EXECUTE grants to account users from an earlier bootstrap run.
6. Create the account-level reviewer group. Then apply `governance/02_reviewer_grants.sql`.
7. Grounding incremental: done (digest cache, 2026-11-25).
8. Chat endpoint scale-to-zero: about $13.5 per day idle with it off. Decide for the demo.
9. Genie benchmarks re-run on the current state: done (2026-11-25, 14 of 14).
10. Code review pass and `evidence/12_code_review_tests.txt`: done (2026-11-25 pass, tests recorded).
11. Commit a text dump of the hero's data sheet and letter.
12. P1 items if time allows: column mask or row filter for a reviewer, MLflow tracing, `mlflow.genai.evaluate` with groundedness scorer.
13. Readiness: the clean data-layer rerun is done (2026-11-25). Still open: secrets and name scan, private repo creation, attestation walk-through. Commit only after approval.
14. Generator: investigate the SCS DOS gap (three WARRANTED misses have a billed DOS with no matching procedure note). Not regenerated in this refresh.

## 2026-11-25 — Anonymization (Naveen chose anonymize; decision record in docs/deck/NAMING_CHECK.md)
- Repo text: the customer name, product names and logo removed from README, docs, business case, evidence and data/SOURCES.md. Customer name becomes "a large multi-state nonprofit health system (HQ Arizona)" on first mention, then "the health system". Public payer and regulatory facts kept (BCBS of Arizona / AZ Blue, AHCCCS, CMS, Medicare Advantage, CARC).
- Customer-identifying links (own financial pages and filings, trade-press articles naming it, tax-filing identifiers) withheld from committed files; figures kept with generic sources. Full links kept in the private Sheet (see docs/business_case/SOURCES.md note).
- Bundle and repo renamed to med-nec-appeals-fe-bar in text. Local paths written as <repo>. Personal workspace path and builder email replaced with <builder>.
- Evidence samples: letter headers show [Health System] with a "customer name redacted" note.
- Deck: copy created in personal My Drive (original untouched): https://docs.google.com/presentation/d/1oPXZ7xKcxyqLRRHgfWh-xtSI6TNiSQffcUgJuf0i9RU/edit . Customer name, logo and grey band removed from all 17 slides and speaker notes; restyled to Barlow with Databricks navy #1B3037 and red #FF3621 subtitles. Validation: 0 errors, 23 element_overlap warnings (cover title/subtitle spacing fixed).
- Pending: the regenerated prototype numbers from the orchestrator. Then update the deck, DECK_NUMBERS.md, README, EVIDENCE and DECK.md, re-validate, and export the PDF to ~/fe_bar/FE_Bar_Medical_Necessity_Appeals_POV.pdf and docs/deck/FE_Bar_Medical_Necessity_Appeals_POV.pdf.
- Business-case numbers unchanged by the anonymization.
