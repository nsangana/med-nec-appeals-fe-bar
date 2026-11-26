# Medical-necessity appeals on Databricks: FE Bar build

> **DRAFT.** Section 6 ("How I used AI") is a draft. The author must rewrite it in his own words before submission. Other sections are the build narrative and can be edited.

**About this repo.** This build extends my earlier appeals prototype. It is a fresh repository with a fresh git history. It builds in a new schema, `appeals_hackathon_catalog.fe_bar_appeals`, under new resource names (`fe-bar-appeals-*`). The earlier schema, job, endpoint and app were not modified and are not referenced here.

**Scope.** Synthetic data only. Public reference documents only. Every prototype metric is labelled "prototype, synthetic data". Stage names follow the FE Bar: Lakeflow, Unity Catalog, Lakebase, ML/GenAI, Genie Agent, Databricks App.

---

## 1. Business outcome

**$2M–$4M a year of earned revenue recovered at about 50 cents an appeal — paying back the pilot within a quarter, even at the floor.**

A large multi-state nonprofit health system (HQ Arizona) denies some medical-necessity claims (CARC CO50, CO55, CO57, CO150, CO186) after service. Many of those denials are legitimate and appealable, and they go unfiled or unwon because each appeal is rebuilt by hand from three sources. This build decides, per denial, whether the clinical record supports an appeal. If it does, it drafts a letter with dated citations for a person to approve. If the evidence is missing or conflicting, it routes the case to NEEDS REVIEW and drafts nothing. Payer submission is not implemented.

**Value tiers** (annual incremental recovery; `docs/business_case/DECK_NUMBERS.md` §1, §3, §6)

| Tier | Top-down, $M/yr | Bottom-up cross-check, $M/yr | What drives the tier |
|---|---|---|---|
| **Floor** | 2.17 | 1.16 | Sourced base rates only |
| **Likely** | 4.33 | 1.16 | Floor × 2.0 dollar weighting. **The 2.0× is an assumption, not sourced.** |
| **Ceiling** | 8.65 | 9.74 | Top of sourced rates. The bottom-up Ceiling also uses an unsourced 85% improved appeal rate (`docs/business_case/MODEL.md`). |

The headline range is Floor to Likely on the top-down method. The bottom-up method is lower and is shown, not hidden.

**Caveats that travel with the numbers**
- **Likely depends on the 2.0× multiplier.** At 1.5× the top-down Likely is $3.25M; at 3.0× it is $6.50M (DECK_NUMBERS §1).
- **Bottom-up does not converge with top-down in the Likely case.** Its Floor and Likely are both $1.16M. The gap comes from the $465 average denied amount.
- **Payback and ROI use placeholder costs.** One-time implementation is $216K (Floor) or $144K (Likely and Ceiling). Annual run cost is $90K or $60K. Both are assumptions to validate with the health system's RCM. At Floor, payback is 1.3 months top-down and 2.5 months bottom-up, and both include the one-time cost. The 20.2× top-down ROI is net benefit ÷ annual cost and excludes the one-time cost.
- **Cost per appeal is measured at prototype scale.** $0.11 variable and $0.51 fully loaded at 60 appeals per day, at list price, not the health system's contracted rates (`evidence/10_cost_per_appeal.md`).
- **The $12.8M reference figure is a placeholder, not a result.** At Floor rates it would need a 5.9× dollar multiplier. The model does not support it.
- **Capacity is context, not the headline.** About 1,832 admin hours a year, roughly 1.0 FTE, at Floor and Likely (DECK_NUMBERS §3).

**Patient impact** is limited to patient financial liability and billing experience. This build makes no clinical-outcome claims.

**Who it serves** (roles, per `docs/STAKEHOLDERS.md`): VP of Revenue Cycle (domain owner), Chief Data & AI Officer (technical stakeholder), CFO (executive sponsor), and Director of Denial Management (operational owner).

**Proposed next step.** A 90-day pilot on one payer and one denial code (BCBS of Arizona commercial, CO50), with baseline and pilot windows of equal length. Pilot cost is not in this build (`docs/deck/DECK.md`, slide 10).

**What the prototype proves (synthetic data only).** On 180 generated encounters, the determination matches the designed label 97.2% of the time (175 of 180). It made no unsafe WARRANTED call (0.0%). All five misses went to NEEDS REVIEW, which is the safe direction (`evidence/11_eval_180.md`). The end-to-end job ran three times in a row, 10 of 10 tasks each time, growing the worklist from 60 to 120 to 180 appeals without regenerating finished ones (`evidence/08_job_run.md`). The eval measures agreement with designed labels. It does not measure payer overturn rates.

---

## 2. The integrated data journey

One hero claim runs through all six stages. The claim is **Elena Marquez** (fictional): keys `101 / 770000001 / 50000001`, BCBS of Arizona commercial, CPT 27447-RT (total knee arthroplasty), CARC CO50, charges $58,400, expected reimbursement $24,850. Denied 2026-06-07. Appeal deadline 2026-12-04, which is 9 days after the 2026-11-25 run date. The designed determination is WARRANTED.

**Stage 1: Lakeflow (ingest and transform).**
- The generator is a job task (`pipeline/10_generate_raw_data.py`). It writes JSON lines to the UC volume `landing` (`claims/`, `clinical_notes/`).
- The eval labels go to the Delta table `eval_case_labels` only. They never reach the landing area, the pipeline or the model.
- The SDP pipeline `fe-bar-appeals-sdp` (`sdp/01`–`04`) runs Auto Loader into `bronze_claims` (538 lines) and `bronze_clinical_notes` (1,053 notes). A full refresh on an empty landing folder fails, so the generator must land a batch first (`evidence/01_lakeflow_pipeline.md`).
- Silver expectations drop 6 defect lines (2 invalid CARC `CO97`, 2 dates of service after denial, 2 null keys). They warn on 2 negative reimbursements.
- Gold `gold_denial_worklist` has one row per encounter: 500 rows. It is ranked by expected dollars × deadline risk. The hero is rank 1, `AT_RISK`, 9 days remaining.
- Source: `evidence/01_lakeflow_pipeline.md`.

**Stage 2: Unity Catalog (governance).**
- All objects are in `appeals_hackathon_catalog.fe_bar_appeals`. Gold and silver tables have column comments.
- PHI tags are on patient name, date of birth, MRN, member ID and claim ID. Base tables carry `synthetic=true`.
- Lineage is read from `system.access.table_lineage`. It shows bronze → silver → gold → grounding → `appeals_output` → `worklist_serving`.
- Reviewer grants are written (`governance/02_reviewer_grants.sql`) but not yet applied. They need an account-level group.
- Source: `evidence/02_governance.md`.

**Stage 3: ML/GenAI (determination and letter).**
- `encounter_grounding` builds one digest per encounter. It injects the payer-routed criteria passages (`med_nec_criteria`, routed by `denial_strategy`), the MPFS coding context, and the dated notes. The Vector Search index `med_nec_criteria_index` serves the chat agent, not the batch.
- `data_sheet_facts` is built by plain SQL with no LLM. It has one row per grounded encounter, which is 450 at the last count. Each one renders a rule-built data sheet.
- `appeals_output` gets one `ai_query` call per encounter (`databricks-claude-sonnet-4-6`). It writes with MERGE, capped at 60 per run, hero first, then `NEW`, then priority rank.
- The output is exactly one of WARRANTED, NOT WARRANTED or NEEDS REVIEW. Any unparseable response becomes NEEDS REVIEW with a `PARSE_FAILURE` reason.
- The hero is WARRANTED. Its letter quotes dated notes (`evidence/04_genai_generation.md` §5a).
- Evaluation joins `eval_case_labels` in `pipeline/60_evaluate.py` only and writes `eval_results` and `eval_summary`.

**Stage 4: Lakebase (operational serving and review).**
- `worklist_serving` (Delta, change data feed on) is synced to a Lakebase Autoscaling database as the synced table `fe_bar_appeals.worklist_serving`. It has 500 rows. The app reads it at low latency.
- Reviewer actions are inserted into `public.review_actions`. The table is append-only, so the app cannot update or delete events. The actions are EDIT, APPROVE, REJECT, ROUTE_TO_REVIEW and SUBMIT.
- `public.review_state` gives the latest status per encounter. For the hero, that is APPROVE then SUBMIT (simulated), with `deadline_met = t`.
- Source: `evidence/03_lakebase.md`.

**Stage 5: back to Unity Catalog.** The review state is copied into the Delta table `review_state_uc`, using the UC catalog `fe_bar_appeals_lakebase`. Genie and the metric view can then query it (3 rows; simulated). Source: `evidence/03_lakebase.md`, `evidence/08_job_run.md`.

**Stage 6: Genie Agent (natural-language access).**
- The Genie Agent space "FE Bar – Medical Necessity Appeals" (`01f1e7ec913217158b231c3e2f18fa20`) uses five objects: the metric view `appeals_metrics`, `appeals_output`, `eval_summary`, `gold_denial_worklist` and `review_state_uc`.
- `appeals_metrics` defines appealable revenue, revenue at deadline risk, revenue lost to deadline, warranted rate, NEEDS REVIEW rate, approval rate and cost per appeal.
- 14 of 14 benchmark questions passed, grouped by stakeholder role. One of them is "What is the status of the claim for Elena Marquez?" The 2026-11-25 re-run on the 180-row state passes all 14 (`evidence/07_genie.md`).

**Stage 7: Databricks App (business surface).** `fe-bar-appeals-app` (AppKit). The worklist is sorted with NEW first, then priority, and carries NEW, AT_RISK and PAST_DUE tags. The case file opens the letter, the data sheet and the AI worksheet together. Reviewers can take actions, ask the chat agent (`fe-bar-appeals-chat`, a LangGraph `ResponsesAgent` over UC functions and the VS index), and use the Genie tab (`evidence/06_app.md`, `evidence/09_chatbot.md`).

**Demo path for the hero.** Worklist (rank 1, AT_RISK, 9 days) → case file → letter and data sheet → Approve → Submit (simulated) → Genie question on the claim's status → chat question on the evidence.

---

## 3. Architecture

### 3.1 Data flow

```
  generator (job task, seed 20261124)                 public references (4 files)
          │                                                     │
          ▼                                                     ▼
  UC volume  landing/{claims,clinical_notes}        UC volume  raw_references
          │ Auto Loader                                         │ ai_parse_document / read_files
          ▼                                                     ▼
  SDP fe-bar-appeals-sdp                              med_nec_criteria, denial_strategy,
  bronze_claims · bronze_clinical_notes               mpfs_indicator_listing, mpfs_indicator_descriptors
          │ expectations (drop / warn)                          │      │
          ▼                                                     │      └─► VS index med_nec_criteria_index
  silver_claim_lines · silver_clinical_notes                    │          (serves the chat agent)
          │                                                     │
          ▼                                                     │
  gold: gold_denial_worklist (500) · mednecessity_ai_agent · medical_records
          │                                                     │
          ├──────────────► encounter_grounding (ai_summarize)  ◄┘
          │                 data_sheet_facts (SQL, no LLM)
          │                 appeals_output  (ai_query, ≤60/run, MERGE on input_hash)
          │                       │
          │                       ├──► UC volume appeal_pdfs  (letter, AI worksheet, data sheet)
          │                       ▼
          │                 worklist_serving (Delta, CDF)
          │                       │ synced table
          │                       ▼
          │              Lakebase Autoscaling  fe_bar_appeals.worklist_serving
          │                       ▲                       │
          │                       │ reads                 ▼
          │              ┌────────┴───────────┐   public.review_actions (append-only)
          │              │ App fe-bar-appeals │   public.review_state (view)
          │              │ -app (AppKit)      │          │ copy by job task
          │              └────────┬───────────┘          ▼
          │                       │ chat          review_state_uc (Delta, UC)
          │                       ▼                       │
          │       fe-bar-appeals-chat (ResponsesAgent)    │
          │                                               ▼
          └────────────────────────────────►  appeals_metrics (metric view)
                                              + gold + appeals_output + eval_summary
                                                          │
                                                          ▼
                                          Genie Agent "FE Bar – Medical Necessity Appeals"

  eval: pipeline/60_evaluate.py joins eval_case_labels (never sent to the model)
        → eval_results, eval_summary

  genai eval: pipeline/65_genai_evaluate.py replays stored outputs as MLflow traces
        → LLM judge (databricks-claude-sonnet-4-6): groundedness, no fabricated evidence,
          quote checks, label match → genai_eval_results, genai_eval_summary

  governance: column masks mask_phi / mask_phi_ts on appeals_output, data_sheet_facts, encounter_grounding
```

### 3.2 Job DAG (`fe-bar-appeals-job`, defined in `resources/fe_bar_appeals.job.yml`)

```
 bootstrap ───────────────────────────────────────────────┐
 generate_raw_data ─► sdp_pipeline ─► grounding ◄─────────┘ (also needs bootstrap)
                                         │
                       ┌─────────────────┼──────────────────────────┐
                       ▼                 ▼                          │
                data_sheet_facts   generate_appeals ─┬─► register_tools (bootstrap re-run)
                       │                 │           ├─► evaluate ─► genai_evaluate
                       └────────┬────────┘           │
                                ▼                    │
                           render_pdfs ◄─────────────┘ (after generate_appeals)
                                │
                                ▼
                           lakebase_sync
```

- The job has 11 tasks. `genai_evaluate` (`pipeline/65_genai_evaluate.py`) runs after `evaluate`. The three 10-task runs in `evidence/08_job_run.md` predate it.
- The job is a Databricks Asset Bundle. Python tasks run on serverless compute. SQL tasks run on the shared SQL warehouse.
- Retries: 1 to 2 per task. The generation MERGE is incremental, so a retry does not re-bill finished rows.
- The schedule is a daily cron at 04:00 America/Phoenix, **PAUSED** to control cost.
- The job runs the repo's own code. The older UI-built job in the earlier prototype is not used.

### 3.3 Auth model

| Path | Identity | Why |
|---|---|---|
| Worklist read, review actions | **App service principal**, through a Lakebase Postgres role | Lakebase is not governed by UC OBO. The SP is granted SELECT on the worklist, and SELECT and INSERT on `review_actions`. It has no UPDATE or DELETE, so reviewer events are append-only. |
| Appeal letter, data sheet, PDFs (UC volume), reads from UC | **Signed-in user (OBO)** | The app forwards the user's token. Reads are governed by each reviewer's UC grants, so column tags and least-privilege grants apply per user. |
| Chat | **Signed-in user (OBO)** calling the endpoint | The endpoint's service principal needs EXECUTE on the UC functions and SELECT on the VS index. Never `CREATE OR REPLACE` those functions behind a live endpoint: it breaks the passthrough. |
| Genie tab | **App service principal** (CAN_RUN on the space, SELECT on its five objects) | The forwarded user token never carried the `genie` scope, even after a scope change and redeploy. The Genie tab therefore runs as the SP. Trade-off: Genie answers reflect the app's access, not each reviewer's grants. |
| Job tasks | The identity that deploys the bundle (no `run_as` set) | Simplest for a demo. Production would use a service principal. |

**Column masks (governance).** `mask_phi` and `mask_phi_ts` (`governance/05_column_masks.sql`) are attached to `appeals_output.patient_name`, `data_sheet_facts` (name, member ID, DOB text) and `encounter_grounding` (name, member ID, DOB). Members of the workspace group `fe-bar-appeals-reviewers`, and the app service principal, see real values. Everyone else sees `***MASKED***`, or NULL for DOB. The job and the chat endpoint run as the group member, so they keep real values. Lakebase copies, appeal PDFs and SDP-managed tables are not masked (`evidence/13_column_masks.md`).

---

## 4. Decisions and trade-offs

**Declarative `ai_query` batch, not an agent loop, for generation.** Each encounter gets one fixed call. The control flow is deterministic and the cost is bounded: 60 calls per run. The outputs are reproducible and easy to evaluate. The trade-off is no dynamic tool choice and no follow-up turns. The one place that needs those is the chat agent, which is a LangGraph `ResponsesAgent` over UC functions (`evidence/04_genai_generation.md`, `evidence/09_chatbot.md`, `evidence/10_cost_per_appeal.md`).

**Deterministic data sheet, not an LLM worksheet, as the trust artifact.** `data_sheet_facts` is built by SQL from the source rows. It covers every grounded encounter, has no cap, and makes no LLM call. The reviewer checks the letter against it. The LLM worksheet is kept as a separate PDF labelled "AI reasoning (model-generated)" and is produced only in the capped batch. The trade-off is that the rules must be maintained by hand (`SPEC.md` ADDENDUM 1).

**Generator as a job task → landing volume → Auto Loader, not generation inside the pipeline.** The ingest step is visible in the job run and the raw files can be inspected. The trade-off: Auto Loader ignores files rewritten at the same path, so re-landing a batch needs a full refresh of the pipeline (`docs/FINDINGS.md`).

**Ground truth kept out of the data path.** Designed labels are written only to `eval_case_labels`. The model never sees them. The trade-off is that accuracy measures agreement with designed cases, not payer outcomes.

**Lakebase Autoscaling, not Provisioned, for serving.** The project runs at 0.5 CU with a 300-second suspend (`evidence/03_lakebase.md`). Reviewer actions are an append-only native table, which keeps the audit trail. The worklist is a synced copy, so it refreshes on the job's `lakebase_sync` step rather than live. Postgres keys are uppercase and must be quoted. The trade-off is that the copy can lag the Delta table until the next run.

**Incremental generation with a 60-per-run cap.** A MERGE keys on an `input_hash`. The candidates are rows with no output or a changed hash. The order is hero, then `NEW`, then priority rank. The run log shows 60 rows written and 0 updated in each of three runs, so no finished letter is regenerated (`evidence/04_genai_generation.md` §2). The trade-off is backlog: 450 encounters are grounded and 180 are generated so far. The grounding step is incremental: a digest cache (`encounter_digest_cache`) means each encounter is summarised once, and later runs only re-summarise changed notes (`evidence/08_job_run.md`).

**Genie through the app service principal.** The OBO token did not carry the `genie` scope, so the Genie tab runs as the app SP. The trade-off is that Genie shows the app's access, not per-reviewer grants. The worklist and review actions already run as the SP. PDFs and chat stay on OBO. I approved this on 2026-11-24.

**Public appeal windows, labelled as assumptions.** Commercial 180 days (29 CFR 2560.503-1), Medicare Advantage 65 days (Medicare.gov, 42 CFR 422.582), and Medicaid 60 days (A.R.S. §36-2903.01, AHCCCS only). These are member-appeal floors used as proxies. Provider-contract windows vary and are often shorter. The Medicaid alternative of 12 months is not modelled (`data/SOURCES.md`, `docs/SPEC.md` ADDENDUM 2).

**Workspace group, not account group, for the reviewer persona.** `fe-bar-appeals-reviewers` is a workspace group. It holds the app CAN_USE permission and the Genie CAN_RUN permission. UC grants need an account-level group, which does not exist yet, so the reviewer grant set is written but not applied. The trade-off is that reviewers' UC reads depend on grants that are not yet set up for the group (`docs/FINDINGS.md`).

**Column masks through the workspace group, with an app SP exemption.** Masks test `is_member('fe-bar-appeals-reviewers')` and `session_user()` against the app SP id, and return the real value for either. Other principals see `***MASKED***` (NULL for DOB). `is_member` checks workspace-local groups, which is why the workspace group is used. The trade-off: the group name and SP id are hard-coded in the function, and the non-member branch is verified at logic level only (`evidence/13_column_masks.md` §5). The Databricks docs say `IS_ACCOUNT_GROUP_MEMBER` and `SESSION_USER` run as the invoker. They do not name `is_member`, so that behaviour is unconfirmed. Masks on `encounter_grounding` survive the stage-20 rebuild (verified 2026-11-26: grounding task re-run, masks still listed in `information_schema.column_masks`).

**LLM judge with the generator's context, and a cost cap.** The MLflow evaluation (`genai_evaluate`) scores stored generations with `databricks-claude-sonnet-4-6`. Its groundedness context is rebuilt from the generator's own prompt blocks and is drift-tested against `pipeline/30_generate_appeals.sql` (`genai/eval_logic.py`). An earlier context that omitted claim identifiers marked correct letters as ungrounded (83.3% before the fix, 98.3% after). The job refuses any run whose estimated judge cost exceeds `genai_cost_cap_usd`, which defaults to $5. The 180-row run is estimated at about $7.2, so only 60 rows were judged. The trade-off: the judge and the generator are the same model family (`evidence/14_mlflow_genai_eval.md`).

**No payer contracts.** Contract terms are not in the data and are not invented. Each data sheet prints "Payer contract terms: not reviewed (not available in this build)" (`pipeline/25_data_sheet_facts.sql`). Contracts are future state.

**New job and new schema, old resources untouched.** The earlier prototype's job, endpoint, app and schema are not changed. The trade-off is duplicated setup for anyone who wants to run both.

---

## 5. Evidence index

Full index with stage mapping and real-or-simulated labels: **[evidence/EVIDENCE.md](evidence/EVIDENCE.md)**.

| What | Where | Key result |
|---|---|---|
| Pipeline update and expectations | `evidence/01_lakeflow_pipeline.md` | 6 of 538 defect lines dropped; 500 gold encounters |
| Governance | `evidence/02_governance.md` | PHI tags; lineage bronze → gold → appeals_output → worklist_serving |
| Lakebase | `evidence/03_lakebase.md` | 500-row synced worklist; append-only reviewer events |
| Generation | `evidence/04_genai_generation.md` | 60 per run, 0 rewrites; sample WARRANTED, NOT WARRANTED, NEEDS REVIEW outputs |
| End-to-end job | `evidence/08_job_run.md` | 3 of 3 full runs SUCCESS (10 of 10 tasks each); 180 appeals: 72 WARRANTED, 66 NOT WARRANTED, 42 NEEDS REVIEW |
| Eval, 180 encounters | `evidence/11_eval_180.md` | 97.2% accuracy (175 of 180); 0.0% unsafe; 0 parse failures |
| App API responses | `evidence/06_app.md` | Worklist, case file and review round trip return 200 or 201 |
| Genie Agent | `evidence/07_genie.md` | 14 of 14 benchmark questions (180-row state, 2026-11-25) |
| Chat agent | `evidence/09_chatbot.md` | Hero question answered with dated evidence |
| Cost per appeal | `evidence/10_cost_per_appeal.md` | $0.107 variable; $0.51 fully loaded at 60 per day (list price) |
| Column masks | `evidence/13_column_masks.md` | Member reads real PHI; no masked values in the reviewer view. Non-member path is logic-only |
| GenAI eval (MLflow judge) | `evidence/14_mlflow_genai_eval.md` | 60 rows: groundedness 98.3%, no fabricated evidence 96.7%, determination match 95.0%; quotes 89.7% normalised / 58.7% strict |
| Python tests | `generator/tests`, `genai/` | 79 passed (local run, 2026-11-25) |

Business-case numbers are in `docs/business_case/DECK_NUMBERS.md`.

---

## 6. How I used AI

**Steering evidence:** [`docs/STEERING_LOG.md`](docs/STEERING_LOG.md) records each direction and course correction the builder gave the AI (solution, business case, deck) and what changed as a result.

> **DRAFT. Builder to edit in his or her own words.** The FE Bar attestation requires that the work, decisions and narrative are mine. This section is a starting point to rewrite, not a statement to submit as written.

**Tools.** I used Claude Code as the orchestrator, with coordinated sub-agents. The build uses `databricks-claude-sonnet-4-6` through `ai_query` for appeal generation and for the chat agent.

**Coordination pattern.** I planned first and approved the plan before any code was written. Then I ran one shared specification, `docs/SPEC.md`, covering interfaces, the hero claim and defaults. Sub-agents wrote to one append-only log, `docs/FINDINGS.md`, which recorded interface changes, blockers and resource IDs. The work split into five tracks: data and SDP, GenAI, Lakebase, the app, and governance with Genie. Each track wrote its evidence as text under `evidence/`.

**Databricks AI Dev Kit skills.** The plan named `databricks-pipelines`, `databricks-jobs`, `databricks-lakebase`, `databricks-genie`, `databricks-apps`, `databricks-unity-catalog`, `databricks-ai-functions` and `databricks-dabs`. The rule was to check current docs before using any feature. [TODO builder: confirm which skills were actually invoked.]

**Key patterns.**
- Every number on a slide or in this README traces to a file. A figure that is not in `DECK_NUMBERS.md` or an evidence file does not appear.
- Measured numbers are labelled "prototype, synthetic data". Projected numbers are labelled as model outputs or assumptions.
- The hero claim is fixed in the spec, so the generator, the pipeline, the app and the demo all follow one case.
- Evidence is text, not screenshots.
- Anything that grants access, shares a resource or changes a shared object needed my approval first. I approved each one explicitly.
- Added in this pass: the MLflow GenAI evaluation (`genai_evaluate`) and column masks on PHI columns.

**Decisions I made (not delegated to AI).**
1. Ingest through a generator task, a landing volume and Auto Loader. 500 denials. At most 60 LLM calls per run. Lakebase Autoscaling.
2. Appeal windows from public regulations (180 / 65 / 60 days), with the caveats recorded.
3. Public PDFs and spreadsheets only. Not the earlier prototype's curated CSV or parquet.
4. Personas: VP of Revenue Cycle, CDAIO, CFO and Director of Denial Management. The $12.8M figure is a placeholder to validate, not a result.
5. Reviewer workspace group, Genie CAN_RUN, app CAN_USE.
6. The Genie tab runs as the app SP, after the OBO scope failed. Grants on five objects to the SP.
7. Deck framing: three tiers. Drop the earlier, unsourced upside figure. Show $12.8M as a hypothesis tested and revised.
8. Headline wording. Chosen by Naveen on 2026-11-25: "$2M–$4M a year of earned revenue recovered at about 50 cents an appeal, paying back the pilot within a quarter, even at the floor." The earlier "20×" wording is retired because it excludes the one-time pilot cost (`docs/business_case/DECK_NUMBERS.md` §7).

**Session.** The conversation ID is `e2e3204c-874a-4e35-bf06-2aa699e64087`. The build log, including the timeline, decisions and issues hit, is [docs/SESSION_LOG.md](docs/SESSION_LOG.md). [TODO builder: confirm the submission did not use the internal Solution Builder output, which the attestation requires.]

---

## 7. Limitations and what is simulated

**Simulated**
- All patients, claims, notes, member IDs, facilities and eval labels come from `generator/` (seed `20261124`). They are fictional. Payer names are routing labels.
- Reviewer actions are recorded as `demo-reviewer (simulated)`. The hero's APPROVE and SUBMIT are simulated. SUBMIT is an app status, not a payer submission.
- `review_state_uc` and the approval-rate measure in Genie use simulated actions.
- The data sheet's "payer contract terms not reviewed" line is a fixed statement, not a review.

**Not implemented**
- Payer submission. Payer contracts. Prior-authorization appeals. Multi-payer expansion (P2 future state).
- Row filters. Column masks cover only the PHI columns listed in `evidence/13_column_masks.md`.
- Reviewer UC grants (written, not applied; needs an account-level group).
- The full 180-row LLM-judge run. The judge scored 60 rows; the 180-row estimate (about $7.2) is above the $5 cap.
- Chat-agent tracing. `fe-bar-appeals-chat` has tracing enabled, but no traces were found in either experiment (`evidence/14_mlflow_genai_eval.md` §8b).
- A live nightly schedule. The job is paused.
- A browser visual test of the app. Checks were API calls and a build.

**Limits of the numbers**
- Accuracy is agreement with designed labels on synthetic cases. It is not a payer win rate and not a clinical outcome.
- The quote check is a metric only. On 180 rows, 85.3% of quoted spans match after normalising punctuation and 54.7% match verbatim (`evidence/11_eval_180.md`). On the 60-row judge run the figures are 89.7% and 58.7% (`evidence/14_mlflow_genai_eval.md`). The strict gap comes from PDF-extraction artefacts in the criteria text and from genuine paraphrase. Quotes are a weak proxy for groundedness, so the two are reported together.
- The LLM judge covers 60 of 180 rows. Groundedness is 98.3%, no fabricated evidence 96.7%, and determination match 95.0%. Single verdicts can flip between runs (`evidence/14_mlflow_genai_eval.md` §5, §9). Read a sample before relying on a rate.
- Column masks: the non-member path is verified at logic level only. Lakebase copies, appeal PDFs and SDP-managed tables are unmasked. The chat tool `get_encounter` reads `encounter_grounding` and has not been re-tested for non-members.
- Financial figures are model outputs on public benchmarks and labelled assumptions. The one-time and run costs are placeholders. The 2.0× dollar weighting behind Likely is unsourced.
- Cost figures are list price, this workspace's usage only. Warehouse and pipeline shares are allocations.
- The appeal windows rest on public regulations, with the caveats above. The BCBS criteria file is a secondary summary; its underlying AZ Blue sources are cited in `data/SOURCES.md`.
- The hero's letter is in the repo only as an excerpt. The full letter and data-sheet PDFs are not committed.

---

## Running it

**Prerequisites.** A Unity Catalog workspace with serverless compute, a SQL warehouse, a Vector Search endpoint named `appeals-vs-endpoint`, and Lakebase Autoscaling. Databricks CLI with a profile for the workspace.

1. **Point the bundle at your workspace.** `databricks.yml` hard-codes the build workspace host and the warehouse ID. Change `targets.default.workspace.host`, `variables.warehouse_id` and the catalog and schema variables.
2. **Upload the four public reference files** into the volume `raw_references`. The bootstrap creates the schema and volume, but it reads the files, so the first run fails until they are in place. Run the bootstrap task once to create the volume, upload the files, then re-run the job.
3. **Lakebase.** `lakebase/setup_lakebase.sh` creates the project, the `appeals` database and the DDL. It is idempotent. Grant the app's SP the statements in `lakebase/app_grants.sql` after the app exists.
4. **Deploy and run the job.**
   ```
   databricks bundle deploy --profile <your-profile>
   databricks bundle run fe_bar_appeals_job --profile <your-profile>
   ```
   Use `--only <task>` to run a single task. The bootstrap task is idempotent and skips the expensive `ai_parse_document` steps once their tables have rows.
5. **Governance.** `tools/run_sql.py -f governance/01_phi_tags.sql` applies PHI tags. The reviewer grants in `governance/02_reviewer_grants.sql` need an account-level group first.
6. **Genie Agent.** `python3 genie/build_space.py` writes `genie/genie_space.json`. Create the space from that serialized JSON through the Genie API. `python3 genie/run_benchmarks.py --space <space-id>` runs the 14 benchmarks and writes `evidence/07_genie.md`.
7. **Chat agent.** `agent/build_and_deploy.py` is a Databricks notebook. It logs the UC model `appeals_chat_agent` and deploys the endpoint `fe-bar-appeals-chat`.
8. **App.** `app/` is an AppKit project. Create `fe-bar-appeals-app`, bind its resources (warehouse, the PDF volume, the Lakebase database, the chat endpoint and the Genie space), and deploy. The deploy steps and the resource list are in `evidence/06_app.md`.
9. **Tests.** `python3 -m pytest generator/tests` and `python3 -m pytest genai/` run the generator and parser tests. In `app/`, `npm run test` runs the Vitest suite.

A clean data-layer rerun was done on 2026-11-25: landing volume, PDFs and job-owned tables were reset and regenerated; schema, grants and resources were kept. The full refresh and the three job runs are in `evidence/01_lakeflow_pipeline.md` and `evidence/08_job_run.md`. The rerun itself changed no code and no grants. The code-review fixes and the app redeploy landed before it.

---

## Repo layout

```
databricks.yml, resources/      bundle, Lakeflow job (fe_bar_appeals.job.yml) and SDP pipeline
generator/                      seeded synthetic generator, writer, unit tests
sdp/                            Lakeflow SDP source: bronze, silver, gold, reference MVs
pipeline/                       job tasks: bootstrap, raw data, grounding, data sheet, generation,
                                PDFs, Lakebase sync, evaluation
genai/                          output parser and its tests
agent/                          chat agent (LangGraph ResponsesAgent) build and deploy
lakebase/                       setup script, DDL, grants, synced-table helper, auth notes
governance/                     PHI tags, reviewer grants, lineage query, app SP grants
genie/                          metric view, Genie space builder, benchmarks and runner
app/                            Databricks App (AppKit): server, client, tests
tools/                          run_sql.py helper (parameterised SQL)
data/SOURCES.md                 public references and appeal-window sources
docs/                           SPEC, FINDINGS, STAKEHOLDERS, CUSTOMER_CONTEXT, SESSION_LOG,
                                business_case/ (model, sources, cost checkpoints, DECK_NUMBERS),
                                deck/DECK.md (text version of the deck)
evidence/                       execution evidence as text, indexed in evidence/EVIDENCE.md
```
