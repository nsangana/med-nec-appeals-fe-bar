# Engineering lifecycle — design, build, test, validate, deploy

This build was run as an engineering lifecycle, not a one-shot AI generation. Each phase below links the
**text evidence** that proves it (everything here is committed output, readable without screenshots).
Synthetic data throughout; reviewer actions are simulated; payer submission is not implemented.
Detailed artifact index: `evidence/EVIDENCE.md`. How the builder steered each phase: `docs/PROMPT_LOG.md`, `docs/STEERING_LOG.md`.

## 1. Design
| What was designed | Evidence |
|---|---|
| Customer problem and requirements from a real discovery conversation (roles only): automated morning worklist, no manual prompting, deterministic data sheet beside every AI letter | `docs/CUSTOMER_CONTEXT.md` |
| Stakeholders and the KPIs each one owns (VP Revenue Cycle, CDAIO, CFO, Director of Denial Management) | `docs/STAKEHOLDERS.md` |
| Interface contract written **before** parallel build (tables, columns, owners, rules) | `docs/SPEC.md` (historical contract) |
| Architecture and decisions/trade-offs (declarative batch vs agent loop, deterministic data sheet, Lakebase for operational state, OBO vs app service principal, generation cap) | `README.md` §3–§4, `lakebase/AUTH.md` |
| Business case: hypothesis tested against public sources; Floor / Likely / Ceiling with labelled assumptions; measured cost | `docs/business_case/MODEL.md`, `SOURCES.md`, `COST_2B.md`, `DECK_NUMBERS.md` |
| Regulatory basis for appeal windows | `data/SOURCES.md` |

## 2. Build
| What was built | Evidence |
|---|---|
| Seeded synthetic generator → landing volume → Lakeflow SDP (Auto Loader, expectations) → gold worklist | `generator/`, `sdp/`, `evidence/01_lakeflow_pipeline.md` |
| Grounding (cached digests), deterministic data sheet, `ai_query` generation (WARRANTED / NOT WARRANTED / NEEDS REVIEW, incremental, capped) | `pipeline/20–30_*.sql`, `evidence/04_genai_generation.md` |
| Lakebase serving: synced worklist + append-only reviewer actions, review state back to UC | `lakebase/`, `evidence/03_lakebase.md` |
| Genie Agent + metric view; LangGraph chat agent on Model Serving | `genie/`, `agent/`, `evidence/07_genie.md`, `evidence/09_chatbot.md` |
| Databricks App: worklist from Lakebase, filters, case file with data sheet and edit preview, chat and Genie sidebar | `app/`, `evidence/06_app.md` |
| UC governance: PHI tags, column masks, least-privilege grants, lineage | `governance/`, `evidence/02_governance.md`, `evidence/13_column_masks.md` |
| Cost observability dashboard on `system.billing` | `dashboards/`, `evidence/15_cost_dashboard.md` |

## 3. Test
| Test | Evidence |
|---|---|
| Unit tests: generator determinism, schema, label mix, hero record, laterality and template rules | `evidence/01_generator_tests.txt` |
| Output-parsing tests (never-fabricate: unparseable → NEEDS REVIEW) + SQL/Python parity | `evidence/04_genai_parser_tests.txt` |
| Code review with severity-ranked findings and fixes; regression tests for each fix | `docs/CODE_REVIEW.md`, `evidence/12_code_review_tests.txt` |
| Static guards: balanced SQL quotes (regression for a real bug); no hard-coded catalog/schema in SQL; identifier validation in notebooks | `genai/test_sql_quotes.py`, `genai/test_parameterization.py` |
| App tests: worklist query builder, filters, diff/preview logic, review-action guard (typecheck + lint + vitest) | `app/server/*.test.ts`, `app/client/src/lib/*.test.ts`, `evidence/06_app.md` |
| Full current test run (all suites) | `evidence/18_test_results.md` |

## 4. Validate
| Validation | Evidence |
|---|---|
| Model accuracy against designed ground truth the model never saw: 97.2%, **0% unsafe**, per-class confusion matrix, every miss explained | `evidence/11_eval_180.md` |
| LLM-judge evaluation with MLflow (judge context mirrors the generation prompt; drift-tested): groundedness 98.3%, no fabricated evidence 96.7% | `evidence/14_mlflow_genai_eval.md` |
| Genie Agent benchmarks: 14/14 against expected SQL | `evidence/07_genie.md` |
| Governance validated: masks present after table rebuilds; member path verified; grants verified with `SHOW GRANTS` | `evidence/13_column_masks.md`, `evidence/02_governance.md` |
| Data quality: expectation drops/warnings per layer; row counts reconciled bronze → silver → gold | `evidence/01_lakeflow_pipeline.md` |
| Live-system checks after every change: app routes, chat endpoint, Genie, worklist filters re-queried against Lakebase Postgres | `evidence/06_app.md`, `evidence/09_chatbot.md`, `evidence/03_lakebase.md` |
| Cost validated two ways (billing measurement vs dashboard views) and cross-checked | `evidence/10_cost_per_appeal.md`, `evidence/15_cost_dashboard.md` |

## 5. Deploy
| Deployment | Evidence |
|---|---|
| Infrastructure as code: one bundle with variables and targets; 17 live resources bound; `bundle plan` verified no-op before and after deploy | `databricks.yml`, `resources/`, `targets/`, `evidence/16_bundle_deploy.md` |
| Lakeflow Job (DAG as code) run end to end; incremental generation proven (60 → 120 → 180, no re-generation) | `evidence/08_job_run.md` |
| Reproducibility: clean data-layer reset and rerun; **from-scratch smoke deploy into an isolated schema, full job run, verified, destroyed**; live re-verified with no data change | `evidence/08_job_run.md`, `evidence/17_bundle_clean_run.md` |
| One-command runbook for components outside the bundle (app, roles, grants) with dry-run | `scripts/deploy_all.sh`, `README.md` "Running it" |
| Release hygiene: anonymization, secret scanning on every commit, no credentials in history, current-only evidence | `docs/deck/NAMING_CHECK.md`, `docs/READINESS.md` |

## 6. Improve — enhancements driven by testing
The build was improved in loops: test it → find a defect or gap → fix the root cause → re-verify.

### 6a. Found by the builder testing the live build
| What I found while testing | Root cause | Enhancement | Evidence |
|---|---|---|---|
| NEEDS REVIEW reasons overflowed the worklist column (account 770000462) | Full multi-bullet reason rendered in a narrow cell | One-line summary ("8 open items · …") in the cell; full list in the case file | `evidence/06_app.md` |
| Chat returned 403 "no permission to query the endpoint" | Endpoint not bound to the app (no CAN_QUERY) | Serving-endpoint resource bound; then the endpoint itself failed to load because UC functions were re-created mid-deploy → bootstrap made idempotent (`CREATE FUNCTION IF NOT EXISTS`) | `evidence/09_chatbot.md`, `evidence/06_app.md` |
| Genie tab "Invalid scope, required scopes: genie" (persisted after a scope fix) | Deprecated scope; running apps keep old scopes; the forwarded user token never carried the new scope | Scope corrected + redeploy; Genie routed through the app service principal with least-privilege SELECT (trade-off documented) | `evidence/06_app.md`, `lakebase/AUTH.md` |
| The generate-appeals task failed after anonymizing the prompt | An apostrophe inside a SQL string literal | Wording fixed; static balanced-quote test added and proven to fail on the original bug | `genai/test_sql_quotes.py`, `evidence/12_code_review_tests.txt` |
| Case-file pop-up was a narrow, unscrollable window | Base dialog width cap overrode ours; auto-growing letter editor; nested PDF scroll traps | Wide, height-capped dialog with fixed header/footer, documents as tabs, fixed-height editor | `evidence/06_app.md` |
| Editing a letter had no visible effect (PDF unchanged) | Edits were stored (audit) but never shown | Formatted edited-letter preview, word-level "show changes" vs the AI draft, downloadable final letter, "Approve version N" — no new permissions | `evidence/06_app.md` |
| Assistant/Genie panel needed scrolling to type — and the first fix didn't solve it | Panel was viewport-height but started below the fold | Rebuilt as a full-height sidebar pinned to the viewport; question box always visible | `evidence/06_app.md` |
| Needed to work the list by outcome and dollars | No filters | Recommendation chips with counts, ≥ $10K toggle, expected-$ sort, server-side so filters span all rows; verified against Lakebase | `evidence/06_app.md` |
| "Would you present this deck to an exec?" / "Is it flowing?" | Text-heavy slides, disjointed story, source mismatch between slides | Rebuilt on the Databricks template; exec architecture slide; one hero claim threaded through a 12-slide story (overview plus detailed architecture) | `docs/deck/DECK.md` |
| "Did we test the bundle?" / "Why haven't we used variables?" | Bundle proven only against live; task code hard-coded the schema | Full parameterization (bundle variables + targets + code reads catalog/schema) and a from-scratch smoke run | `evidence/16_bundle_deploy.md`, `evidence/17_bundle_clean_run.md` |
| "Is the repo clean — no stale data?" | Superseded runs and stale numbers accumulated | Evidence pruned to current-only; docs refreshed; history kept in git | `evidence/EVIDENCE.md` |

### 6b. Found by automated tests, evals and checks
| Signal | Root cause | Enhancement | Evidence |
|---|---|---|---|
| Eval misses: knee replacements billed LT with notes documenting RT | Synthetic-data laterality defect | Generator fixed + test; accuracy 95.6% → 97.2% on regeneration | `evidence/11_eval_180.md`, `evidence/01_generator_tests.txt` |
| Eval misses: thin spinal-cord-stimulator charts | Template lacked imaging and device approval details | Template enriched + test | `evidence/11_eval_180.md` |
| LLM-judge groundedness 83.3% | Judge didn't see the claim details the model saw | Judge context mirrors the generation prompt (drift test); 98.3% | `evidence/14_mlflow_genai_eval.md` |
| App worklist 503 (Postgres 42703) | Synced table lacked a column the UI used | Column carried into the sync (`MERGE WITH SCHEMA EVOLUTION`) | `evidence/03_lakebase.md` |
| Grounding re-summarised every encounter on each run | No cache | Digest cache keyed on notes hash; only changed notes summarised | `evidence/08_job_run.md` |
| Eval double-count across batches | Label join not scoped to the latest batch | Join fixed; scratch-schema proof | `docs/CODE_REVIEW.md` |
| SDP full refresh failed on an empty landing folder | Auto Loader schema inference needs files | Documented ordering (generator before pipeline) | `evidence/01_lakeflow_pipeline.md` |
| A broad EXECUTE grant to all account users | Carried over from an earlier bootstrap | Revoked; least privilege verified | `evidence/02_governance.md` |
