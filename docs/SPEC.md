# FE Bar build — shared SPEC (source of truth for every build agent)

> **Historical record.** Build-time working log / contract kept as process evidence;
> intermediate states and values are historical;
> the current state is in README.md and evidence/EVIDENCE.md.

Plan of record: `<local plan of record>` (Phase 3, P0). This file fixes the **interfaces** so agents can
build in parallel. If you must change an interface, append it to `docs/FINDINGS.md` FIRST, then change it.

## Hard rules (non-negotiable)
- Workspace: `--profile fevm-appeals-hackathon`, always `export DATABRICKS_AUTH_STORAGE=plaintext`.
  Host https://fevm-appeals-hackathon.cloud.databricks.com. Warehouse `559faf81d610a2a1`. VS endpoint `appeals-vs-endpoint`.
- Build ONLY in `appeals_hackathon_catalog.fe_bar_appeals` and resources named `fe-bar-appeals-*`.
  **Never modify / drop / overwrite anything in `appeals_hackathon_catalog.appeals_agent`**, the `<prior-prototype app>` app,
  `appeals-generation-pipeline` job, or `appeals-chat-agent-endpoint`. Reading `appeals_agent` code for reference is fine.
- **Never edit `<prior-prototype repo>`** (read-only source). Work in `<repo>`.
- **No git commit/push, no `gh repo create`.** (Naveen approves later.)
- Synthetic data only, from the seeded generator. No real people's names, no internal Databricks account data.
  Refer to the health system executives by role only.
- Parameterized SQL (named markers `:x` / `IDENTIFIER()`), never string-interpolated values. Hard-coded FQ object names are fine.
- Evidence must be **text** in `evidence/` (md/json/txt): row counts, run outputs, query results. Mark simulated vs real.
- Use the Databricks AI Dev Kit skills (Skill tool: `databricks-pipelines`, `databricks-jobs`, `databricks-lakebase`,
  `databricks-genie`, `databricks-apps`, `databricks-unity-catalog`, `databricks-ai-functions`, `databricks-dabs`)
  and check docs before using a feature. Don't go down rabbit holes: if something is blocked >20 min, log it in
  FINDINGS.md with the error and take the documented fallback.
- Helper: `tools/run_sql.py "<sql>" --param k=v` or `-f file.sql` (prints markdown tables — paste into evidence).

## Defaults chosen (Naveen to confirm at checkpoint — keep them parameterized/easy to change)
| Decision | Default |
|---|---|
| Ingest pattern | Generator job task lands raw JSON files in UC volume `landing` → SDP pipeline ingests with Auto Loader (option A) |
| Volume | 500 denied encounters (~1,600 clinical notes), seed `20261124` |
| LLM cap | ≤ 60 encounters generated per job run (highest priority first, incremental) |
| Lakebase | **Autoscaling** (Postgres projects API; `databricks postgres ...`) |
| Sponsor persona | CFO (exec sponsor) + Revenue Cycle leader (domain owner) |
| Generation model | `databricks-claude-sonnet-4-6` via `ai_query` (validated in prior build) |

## Hero claim (fixed — generator MUST produce exactly this; demo + deck follow it)
- Keys: `FACILITY_ID=101`, `PATIENT_CONTROL_NUMBER=770000001`, `ENCOUNTER_NBR=50000001`
- Patient (fictional): **Elena Marquez**, F, DOB 1962-03-14. Payer **BCBS of Arizona** (commercial PPO) → BCBS criteria.
- CPT **27447** (total knee arthroplasty), MOD `RT`, dx **M17.11** (primary OA right knee) + M25.561, Z68.31.
- CARC **CO50**. TOTAL_CHARGES $58,400.00, EXPECTED_REIMBURSEMENT **$24,850.00**.
- Denial date = as_of_date − 171 days; commercial appeal limit 180 days → **9 days remaining** (AT_RISK).
- Notes document: 7+ months knee pain; NSAIDs (dated) ; 12 PT sessions (dated) with documented failure; corticosteroid
  injection (dated) with only 3 weeks relief; X-ray Kellgren-Lawrence grade 4, bone-on-bone medial compartment;
  can't walk >1 block, KOOS/WOMAC score; ortho surgeon rationale. → `expected_determination = WARRANTED`.

## Objects & contracts (catalog.schema = `appeals_hackathon_catalog.fe_bar_appeals`)
### Volumes (already created)
- `landing` — `/Volumes/.../landing/claims/` (JSON lines, claim-line grain), `/landing/clinical_notes/` (JSON lines, note grain).
  Each generator run writes files named `batch_<as_of>_<run_ts>.json`.
- `raw_references` — public PDFs + MPFS xlsx (already copied): `BCBS_Med_Nec_Criteria.pdf`, `Definition_of_Med_Nec.pdf`,
  `2025_MPFS_Indicator_Listing.xlsx`, `MPFS_Indicator_Descriptors_-_JE_Part_B_-_Noridian.pdf`.
- `appeal_pdfs` — rendered PDFs.

### Generator output (owner: Agent A — data)
Claim-line record = ALL existing `mednecessity_ai_agent` columns (see `pipeline/00_setup.py` §8, same names/types) **plus**:
`DENIAL_DATE DATE, PAYER_TYPE STRING ('COMMERCIAL'|'MEDICARE_ADVANTAGE'|'MEDICAID'), APPEAL_LIMIT_DAYS INT,
EXPECTED_REIMBURSEMENT DOUBLE (line-level contracted/allowed $), SOURCE_BATCH STRING`.
Clinical-note record = composite key + `event_id BIGINT, event_tag STRING, note_date DATE, author_role STRING, plain_text STRING`.
Labels (eval ground truth, **written straight to Delta, never into landing/pipeline/grounding**):
`eval_case_labels(FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR, expected_determination STRING
 ('WARRANTED'|'NOT WARRANTED'|'NEEDS REVIEW'), scenario STRING, is_hero BOOLEAN, generator_seed INT, as_of_date DATE)`.
Mix: ~45% WARRANTED, ~35% NOT WARRANTED, ~20% NEEDS REVIEW; ~8% past deadline, ~15% ≤14 days remaining.
Payer appeal limits: COMMERCIAL 180, MEDICARE_ADVANTAGE 65, MEDICAID 60 days from DENIAL_DATE.

### SDP pipeline `fe-bar-appeals-sdp` (owner: Agent A) — target schema `fe_bar_appeals`
- `bronze_claims`, `bronze_clinical_notes` — streaming tables, Auto Loader (`cloudFiles` JSON) + `_ingested_at`, `_source_file`.
- `silver_claim_lines`, `silver_clinical_notes` — typed + expectations (log results): CARC in
  (CO50,CO55,CO57,CO150,CO186) [drop], non-null composite key [drop], DOS < DENIAL_DATE [drop], EXPECTED_REIMBURSEMENT ≥ 0 [warn].
- **`mednecessity_ai_agent`** (MV) — claim-line grain, legacy column names + new columns (compat for grounding/UC funcs).
- **`medical_records`** (MV) — note grain: composite key + PATIENT_NAME + event_id, event_tag, note_date, author_role, plain_text.
- **`gold_denial_worklist`** (MV) — ONE row per encounter:
  `FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR, patient_name, payer_name, payer_type, denial_code, hcpcs_codes,
   dos DATE, denial_date DATE, appeal_limit_days INT, appeal_deadline DATE, days_remaining INT,
   deadline_status ('PAST_DUE'|'AT_RISK' (≤14d)|'OK'), total_charges DOUBLE, expected_reimbursement DOUBLE,
   priority_score DOUBLE, priority_rank INT`
  `days_remaining = datediff(appeal_deadline, current_date())`; `priority_score = expected_reimbursement × (2.0 if AT_RISK,
   1.5 if ≤30d, 1.0 otherwise; 0 if PAST_DUE)`; `priority_rank` = row_number by priority_score desc.
- `mpfs_indicator_listing` (MV) — from the xlsx via `read_files(format=>'excel')` (logic from `00_setup.py` §2; table name has NO `2025_` prefix).

### Bootstrap (owner: Agent B — one-time, idempotent) `pipeline/00_bootstrap.py`
`denial_strategy`, `med_nec_criteria` (ai_parse_document of the 2 criteria PDFs, CDF on), VS index
`appeals_hackathon_catalog.fe_bar_appeals.med_nec_criteria_index` on `appeals-vs-endpoint`, `mpfs_indicator_descriptors`
(ai_parse_document→ai_query extraction from the public PDF — there is NO curated CSV in this build),
UC functions `get_appeal`, `get_encounter`, `mpfs_lookup`, `descriptor_lookup` (in `fe_bar_appeals`; fix `descriptor_lookup` to
not concatenate: use `ILIKE concat('%', p_term, '%')` is fine since it's a bound param). Skip expensive steps if the table already exists.

### GenAI (owner: Agent B)
- `encounter_grounding` — from `gold_denial_worklist` (excluding PAST_DUE) ⋈ `mednecessity_ai_agent` ⋈ `medical_records`
  ⋈ criteria/MPFS/denial_strategy; keeps every column the old grounding had + `expected_reimbursement, appeal_deadline,
  days_remaining, deadline_status, priority_rank, input_hash` (sha2 over the grounding inputs).
- **`appeals_output`** (Delta, CDF on, MERGE — incremental: only encounters with no row or a changed `input_hash`; ≤ 60 per run,
  by priority_rank). Columns: all old columns + `recommendation` ∈ {'WARRANTED','NOT WARRANTED','NEEDS REVIEW'},
  `needs_review_reason STRING`, `expected_reimbursement, appeal_deadline, days_remaining, deadline_status, priority_rank,
  input_hash, model_name, generated_at, letter_pdf_path, cheat_sheet_pdf_path`. Render task fills PDF paths via UPDATE/MERGE
  (no CREATE OR REPLACE that drops them).
- `eval_results` (per encounter: expected vs predicted, correct, run_id) + `eval_summary` (accuracy, per-class P/R,
  unsafe_rate = predicted WARRANTED where expected ≠ WARRANTED). Never feed `eval_case_labels` to the model.
- Chatbot: adapt `agent/` to the new schema's UC functions + new VS index; endpoint name `fe-bar-appeals-chat`.

### Lakebase + App (owner: Agent C)
- Lakebase Autoscaling project `fe-bar-appeals-lakebase`, database `appeals`.
- Delta source for sync: **`worklist_serving`** (Delta table, CDF on) = `gold_denial_worklist` LEFT JOIN `appeals_output`
  (recommendation, needs_review_reason, cheat_sheet, appeal_letter, pdf paths, generated_at). Refreshed by job task
  `pipeline/50_lakebase_sync.py` (MERGE), synced to Lakebase as synced table (Postgres schema/table name decided by C → FINDINGS).
- Native Postgres table `review_actions` (append-only events: id, keys, action ∈ {EDIT, APPROVE, REJECT, ROUTE_TO_REVIEW,
  SUBMIT}, edited_letter, reviewer, note, created_at) + a `review_state` view (latest status per encounter, submitted_at,
  deadline_met). Review state must reach UC for Genie: UC-registered Lakebase catalog if Genie can query it, else job task
  copies into Delta `review_state_uc`. Verify Genie can query whichever you pick.
- App `fe-bar-appeals-app` (copy of `app/`, AppKit): worklist from Lakebase, reviewer actions → Lakebase, keep OBO SQL/files
  for PDFs + chat, Genie embed via AppKit `genie` plugin (space id from Agent D via FINDINGS).

### Genie Agent + UC governance (owner: Agent D — starts after gold + appeals_output exist)
- Metric view `appeals_metrics` (appealable $, $ at deadline risk, approval rate, NEEDS REVIEW rate, cost per appeal);
  Genie space "FE Bar – Medical Necessity Appeals" over gold + appeals_output + review state; instructions; benchmarks.
- PHI tags on patient columns; one reviewer-group grant set (least privilege); lineage query from `system.access.table_lineage`.

### Job `fe-bar-appeals-job` (owner: orchestrator — DAB at repo root `databricks.yml` + `resources/`)
Tasks: `bootstrap` → `generate_raw_data` → `sdp_pipeline` → `grounding` → `generate_appeals` → `render_pdfs` →
`lakebase_sync` → `evaluate`. Each agent's task file must run standalone as a job task (notebook `.py` with
`# Databricks notebook source` header, or `.sql` file for warehouse SQL tasks). Serverless for Python tasks.

## Repo layout (`<repo>`)
```
databricks.yml, resources/           job + pipeline as code (orchestrator; A adds pipeline resource)
generator/                            seeded synthetic generator + tests (A)
sdp/                                  Lakeflow SDP source (A)
pipeline/00_bootstrap.py              (B)   10_generate_raw_data.py (A)   20_encounter_grounding.sql (B)
pipeline/30_generate_appeals.sql (B)  40_render_pdfs.py (B)   50_lakebase_sync.py (C)   60_evaluate.py (B)
genai/                                output parser + tests (B)
agent/                                chatbot (B)
lakebase/                             DDL + setup (C)
app/                                  fe-bar-appeals-app (C)
genie/, governance/                   (D)
evidence/<stage>_*.md                 everyone; orchestrator writes EVIDENCE.md index
data/SOURCES.md                       public reference URLs (A)
docs/SPEC.md, docs/FINDINGS.md        shared
```
Old copied files `pipeline/00_setup.py, 01_*, 02_*, 03_*` are reference only — the owning agent replaces/removes them.

## ADDENDUM 1 (2026-11-24) — customer-context deltas (see `docs/CUSTOMER_CONTEXT.md`)
Minimal, accepted changes only. Everything else in CUSTOMER_CONTEXT.md is narrative / future state.
1. **Deterministic data sheet (owner B).** Table `data_sheet_facts` built by plain SQL (NO ai_* calls) for every encounter in
   `encounter_grounding`: claim + denial fields, payer→criteria routing + reason, the criteria passages applied, verbatim
   dated note excerpts, MPFS coding context, deadline/$ facts, and the line "Payer contract terms: not reviewed (not available in
   this build)". Rendered as `<key>_datasheet.pdf` for every grounded encounter (not limited by the 60 LLM cap). Column
   `data_sheet_pdf_path` on `worklist_serving`/`appeals_output` as appropriate. The LLM worksheet stays, labelled "AI reasoning".
2. **Quote check (owner B, metric only).** `60_evaluate.py` measures the share of quoted spans in letters/worksheets that are
   verbatim substrings of the grounding inputs (`quote_verified_rate`). It is reported, not used to change determinations.
3. **Worklist trigger tags (owner A).** Gold gets `worklist_tag` ∈ {'NEW' (denial_date ≥ as_of − 1 day, i.e. "denied yesterday"),
   'AT_RISK', 'PAST_DUE', 'OPEN'} (precedence PAST_DUE > NEW > AT_RISK > OPEN). The generator makes ~20 encounters denied yesterday.
   B orders the LLM cap NEW first, then priority_rank (the hero claim must still be in batch 1).
4. **Column comments (owner A)** on gold/silver tables (Genie + governance depend on them).
5. Schedule: the job gets a PAUSED daily cron at 04:00 America/Phoenix (orchestrator).
6. Sponsor persona is OPEN: discovery call = RCM executive sponsor; prompt assumed CFO. Appeal windows 180/65/60 are
   ASSUMPTIONS (Medicaid is state-specific) — label them so in docs.

## ADDENDUM 2 (2026-11-24) — appeal windows: decided from public sources (no health-system-specific numbers exist)
The health system operates across multiple states (HQ Arizona). Modelled windows, counted from DENIAL_DATE (proxy for the notice date):
| PAYER_TYPE | Days | Public basis (retrieved 2026-11-24) | Caveat |
|---|---|---|---|
| COMMERCIAL | 180 | 29 CFR 2560.503-1(h)(3)(i): group health plans must allow "at least 180 days following receipt of a notification of an adverse benefit determination" (https://www.law.cornell.edu/cfr/text/29/2560.503-1); ACA 45 CFR 147.136 adopts it | Member-appeal floor used as a proxy; provider contract appeal windows vary and are often shorter (assumption to validate with RCM) |
| MEDICARE_ADVANTAGE | 65 | Medicare.gov: "must file an appeal within 65 days from the date on the initial denial notice" (https://www.medicare.gov/providers-services/claims-appeals-complaints/appeals/medicare-health-plans); 42 CFR 422.582 | Some online copies of 422.582 still say 60 days (pre-2019 text); contracted-provider disputes follow the plan contract |
| MEDICAID (AHCCCS, AZ) | 60 | A.R.S. §36-2903.01(B)(4): claim grievance "within sixty days after the date of the denial of a timely claim submission" (or 12 months from DOS / eligibility posting, whichever is later) (https://www.azleg.gov/ars/36/02903-01.htm) | Modelled conservatively as 60 days from denial (the 12-month alternative isn't modelled); other states' Medicaid windows are out of scope; only AHCCCS is generated |

## ADDENDUM 3 (2026-11-24) — stakeholders + reviewer group (decided by Naveen)
- Personas resolved: VP of Revenue Cycle, CDAIO, CFO, Director of Denial Management — see `docs/STAKEHOLDERS.md` (KPIs per role;
  $12.8M is a reference placeholder only).
- Reviewer group `fe-bar-appeals-reviewers` created as a **workspace-level** group (Naveen is a member). UC GRANTs require an
  account-level group, so `governance/02_reviewer_grants.sql` stays pending; the workspace group can hold workspace ACLs
  (app CAN_USE, Genie space CAN_RUN) once Naveen approves those.
