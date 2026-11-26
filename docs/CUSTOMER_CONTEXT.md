# Customer context and requirements: FE Bar appeals build

Internal analysis for build agents A (data + SDP), B (GenAI / PDF / eval / chatbot), C (Lakebase + app),
and the orchestrator (job / narrative). Roles only; synthetic data only.

Sources: **[T]** discovery call transcript (`~/fe_bar/discovery_call_transcript.txt`), **[R]** earlier prototype
README, **[S]** `docs/SPEC.md`, **[F]** `docs/FINDINGS.md`, **[P]** prototype `pipeline/02_generate_appeals.sql` and
`pipeline/03_render_pdfs.py`.

Roles used: "RCM executive sponsor", "RCM appeals analyst", "analytics team", "SA".

---

## 1. Current-state workflow and pain

- **Three places, one answer.** Denials, medical records and payer contracts each live in a different place. Someone
  has to visit all three to assess one appeal [T].
- **Manual prompting.** The RCM appeals analyst pastes claim facts, criteria and notes into a prompt-based
  workspace, one account at a time, and the model drafts the letter [T][P].
- **Selection is manual.** Which accounts to appeal is decided by hand; the analytics team is building a denial
  table (claim fields, denial code, account) and a notes pull keyed by account [T].
- **Validation is the real cost.** A reviewer cannot judge a letter without re-doing the lookup. The sponsor's
  concern: checking an appeal can take as long as writing it from scratch [T].
- **Contracts are missing.** Payer contracts are not accessible; the workspace holds only short contract blurbs in
  prompts [T]. Criteria references cover BCBS and the CMS definition of medical necessity only; other payers go by
  the CMS definition [T].
- **Scope today:** medical-necessity denials, CARC CO50 / CO55 / CO57 / CO150 / CO186 [R].

## 2. Desired future state (paraphrased from the sponsor)

- An automated morning run (roughly 03:00-06:00) picks up yesterday's medical-necessity denials. No typed prompts [T].
- Worklist items arrive tagged, so the reviewer can see what is new [T].
- Each account gets an appeal letter and a **deterministic data sheet** in one place. The letter is allowed to be
  probabilistic; the sheet must be reproducible and let a reviewer cross-check at a glance [T].
- One app worklist lists the denied claims with PDFs attached. Not a dashboard, not SharePoint [T].
- A chatbot answers follow-up questions about a chosen appeal, including text the user pastes in [T].
- Data stays in the customer's governed environment, and the model provider does not learn from it [T].

## 3. Requirements and status vs SPEC

Status key: **Covered** = SPEC has an interface for it; **Partial** = some of it is in SPEC; **Gap** = not in SPEC.

| ID | Requirement | Source | Priority | Status vs SPEC |
|---|---|---|---|---|
| R01 | Scheduled nightly run with no manual prompts | T | P0 | Partial: job DAG defined [S], no schedule set |
| R02 | Worklist = denials received yesterday, with medical-necessity flag | T | P0 | Partial: `gold_denial_worklist` ranks all encounters; no received-date or daily selection |
| R03 | Worklist tags on items (e.g. NEW, AT_RISK, PAST_DUE) | T | P1 | Partial: `deadline_status` only; no NEW tag |
| R04 | Explicit medical-necessity denial flag on each row | T, R | P1 | Partial: filtered by CARC in SDP; no column |
| R05 | Denial joined to medical records by account / encounter | T, R | P0 | Covered: composite key, `medical_records` MV [S] |
| R06 | Payer to criteria routing (BCBS AZ commercial to BCBS; else CMS) | T, R | P0 | Covered: `denial_strategy` + grounding [S] |
| R07 | Appeal letter per account as PDF | T | P0 | Covered: `40_render_pdfs` [S] |
| R08 | Deterministic, non-LLM data sheet per account | T | P0 | Gap: only LLM-written `cheat_sheet` exists [S][P] |
| R09 | Sheet content: claim/denial fields, criteria used, dated verbatim note excerpts, MPFS context | T | P0 | Gap |
| R10 | Letter quotes dated record excerpts and criteria | T | P0 | Partial: prompt says "cite"; no verbatim check [P] |
| R11 | Letter and sheet viewable together per account | T | P1 | Partial: two PDFs, two buttons [R] |
| R12 | Output is an app worklist with PDFs (not dashboard / SharePoint) | T, R | P0 | Covered: Lakebase + `fe-bar-appeals-app` [S][F] |
| R13 | Chatbot for follow-up questions about an appeal | T | P1 | Partial: chatbot repointed [S]; paste-in not specified |
| R14 | Data stays in governed environment; no model training on it | T | P0 | Covered by platform (UC, VPC); the no-training statement needs a doc citation |
| R15 | Reviewer access governed, least privilege | R | P1 | Covered: `governance/`, OBO app [S][R] |
| R16 | Payer contracts as governed input; contract language in letter | T | P2 | Gap (inputs not available) |
| R17 | Record coverage: labs, imaging, diagnoses, history, provider comments | T | P1 | Partial: notes carry `event_tag` [S]; coverage unverified |
| R18 | MPFS indicator context, coding-only | T | P2 | Partial: `mpfs_lookup` + `mpfs_context` [S][P]; role unconfirmed |
| R19 | Every column described in reference tables | T | P2 | Gap: no column comments in SPEC |
| R20 | Scale: 50+ accounts, varied appeal types | T | P1 | Covered: 500 encounters, scenario mix, 60/run cap [S] |
| R21 | "Agentic" behaviour | T | P1 | Partial: see G10 |
| R22 | Determinations checked against ground truth | derived | P1 | Covered: `eval_results`, `unsafe_rate` [S] |
| R23 | Appeal deadline and days remaining | S | P1 | Covered: `appeal_deadline`, `days_remaining` [S] |
| R24 | Sheet produced even when NOT WARRANTED or NEEDS REVIEW | derived from R08 | P0 | Gap: prototype renders only WARRANTED letters [R][P] |

## 4. Gaps and recommended minimal changes

**G1. Deterministic data sheet (R08, R09, R24).** Owner: **A** builds the facts table, **B** renders it.
- A: add `pipeline/25_data_sheet_facts.sql` writing `data_sheet_facts` (one row per encounter, no LLM). Columns:
  claim and denial fields; the payer-routed criteria set and section IDs (from `denial_strategy`, by rule); excerpts
  selected by rule (`event_tag` allow-list, `note_date <= denial_date`, sorted by date) and copied verbatim from
  `medical_records.plain_text` with `event_id`; MPFS descriptors for the CPT; a few rule-derived facts (first
  conservative-care date, PT session count, months of documented symptoms).
- B: render `data_sheet_facts` to `*_datasheet.pdf` with a fixed template. Run it for every encounter, including
  NOT WARRANTED and NEEDS REVIEW, and do not put it under the 60-per-run LLM cap.
- Optional: keep the LLM reasoning worksheet as a separate page titled "AI reasoning worksheet (model-generated,
  not verified)". Drop it if it dilutes the story.

**G2. Letter quotes must verify (R10).** Owner: **B**.
- Pass the selected excerpts (with `event_id`) and criteria passages into the prompt. Require each quote verbatim,
  with date and author role.
- Post-check in the genai parser (no extra model call): each quoted span must be a substring of an input excerpt or
  criteria passage. Failures set `needs_review_reason = 'UNVERIFIED_QUOTE'`. Add a unit test.

**G3. Worklist tags and received date (R02, R03, R04).** Owner: **A** (gold columns), **B** (ordering), **C** (chips).
- A: add to `gold_denial_worklist`: `denial_received_date DATE` (default `DENIAL_DATE` until analytics confirms the
  feed), `is_med_nec_denial BOOLEAN` (CARC in the set), `worklist_tag STRING` in {NEW, AT_RISK, PAST_DUE, OPEN}, with
  NEW = received on run date minus 1.
- B: in `30_generate_appeals`, order the 60-per-run cap by NEW first, then `priority_rank`. Otherwise yesterday's
  denials can fall outside the cap during a backlog.
- Answer to the open question: SPEC's priority and deadline ranking does **not** cover the daily trigger. The
  incremental MERGE already processes anything new, so only the tag and received date are needed. No separate trigger.

**G4. Nightly schedule (R01).** Owner: **orchestrator**. Add a cron to the job resource, set between 03:00 and 06:00
in the customer's local timezone. Confirm the timezone first.

**G5. Payer contracts (R16).** Owner: **none for build**; orchestrator narrative. Future state (P2). Do not generate a
synthetic contract excerpt: it would invent contract terms. Instead, print a fixed line on each sheet: "Contract
terms: not reviewed in this build" (a deterministic fact, and honest to the reviewer).

**G6. MPFS context (R18).** Owner: **A** (listing), **B** (sheet block). Show MPFS indicators as a "coding context,
not a denial basis" block only. The MUE question is unresolved: MUE limits are a separate CMS dataset, so do not
claim MUE coverage from the MPFS indicator listing alone. Ask the customer which fields they mean.

**G7. Record coverage (R17).** Owner: **A**. Confirm the generator produces lab, imaging, history and provider-comment
events, and that the `event_tag` allow-list in G1 matches them.

**G8. Column descriptions (R19).** Owner: **A**. Add `COMMENT ON` for gold and reference tables in bootstrap or SDP.
Cheap; do it.

**G9. App surface (R11, R13).** Owner: **C**. One "case file" action per row opening letter and sheet together, plus
the worklist tag chips and NEW-first sort. The chatbot takes an encounter key; accept pasted text as free input only.

**G10. Narrative and SPEC fixes.** Owner: **orchestrator**.
- SPEC sponsor persona says CFO; the transcript says RCM executive sponsor. Align SPEC and deck to the role
  "RCM executive sponsor" and confirm.
- Appeal windows in SPEC (COMMERCIAL 180, MEDICARE_ADVANTAGE 65, MEDICAID 60 days) are assumptions. Medicaid is
  state-specific. Confirm with the customer before the deck quotes them.

## 5. Answers to the six review points

- **(a) Deterministic sheet:** yes, as G1. Smallest design: a rule-built facts table plus a fixed-template PDF. The LLM
  worksheet is optional and labelled.
- **(b) Letters must quote:** yes, as G2. Verbatim check in the parser, failures routed to review.
- **(c) Worklist trigger:** SPEC covers priority and deadlines, not the daily tag. Add `denial_received_date`,
  `is_med_nec_denial` and `worklist_tag` (G3). The trigger itself is the nightly run (G4).
- **(d) Payer contracts:** P2 future state. No synthetic contract excerpt (default: no; avoids scope creep). Print
  "not reviewed in this build" on each sheet.
- **(e) MPFS role:** coding context only (G6). Open question for the customer.
- **(f) Agentic vs batch:** use the honest framing in section 6.

## 6. Narrative hooks for the README and deck

- The data sheet is the trust artifact. The letter is generated by a model; the sheet is rule-built from the same
  source rows, so the reviewer checks the letter against it.
- The worklist needs no prompts. A nightly job assembles yesterday's medical-necessity denials, tags them, and
  produces a letter and sheet for each by morning.
- Grounded, not asserted. Each quoted excerpt is checked against its source note; anything unverifiable goes to
  review.
- Governed in place. Data stays in the customer's Unity Catalog, reviewers see what their grants allow, and the model
  provider does not train on it.
- Agentic where it matters: the chatbot is a tool-using agent over governed functions. The nightly run is a workflow
  with one LLM step per encounter, and a human signs off. Do not claim the model decides or sends appeals alone.
- Scope honesty: contracts and payer-specific criteria are future state. This build covers CO50 / CO55 / CO57 /
  CO150 / CO186 under BCBS and CMS criteria.
