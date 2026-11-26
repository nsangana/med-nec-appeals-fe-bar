# 04 — GenAI generation evidence (REFRESHED 2026-11-26, regenerated run with the neutral prompt)

Mark: **REAL** = executed on `fevm-appeals-hackathon` (warehouse `559faf81d610a2a1` or serverless job) on 2026-11-26 UTC. Input data is **SYNTHETIC** (seed 20261124). Model = `databricks-claude-sonnet-4-6` via `ai_query`. All LLM output below is REAL model output, not hand-written. Samples are excerpts of stored rows (`appeals_output`, `data_sheet_facts`).

_Note: customer name redacted (letter headers show `[Health System]` or the generator's placeholder; no customer name appears in any generated letter or worksheet)._

## 1. Object counts (REAL, 2026-11-26)

| Object | Result |
|---|---|
| `denial_strategy` | 5 rows (CO50, CO55, CO57, CO150, CO186) |
| `med_nec_criteria` | 30 chunks (BCBS and CMS sources, as in the bootstrap; unchanged) |
| `mpfs_indicator_descriptors` | 83 rows |
| `encounter_grounding` | 450 rows, 450 distinct `input_hash` (500 gold encounters minus 50 PAST_DUE on 2026-11-26) |
| `encounter_digest_cache` | 450 rows |
| `data_sheet_facts` | 450 rows, 450 distinct `facts_hash` |
| `appeals_output` | **180 rows** (60 + 60 + 60 over the three regenerated batches) |

Grounded encounters are date-relative. The UTC date rolled from 2026-11-25 to 2026-11-26, so 10 more encounters became PAST_DUE (50 PAST_DUE in total). The worklist is recomputed each day; see section 2a.

## 2. Incrementality (REAL)

`30_generate_appeals` is a MERGE keyed on the encounter. Candidates are rows with no output or a changed `input_hash`, capped at 60 per run, ordered hero first, then `worklist_tag = 'NEW'`, then `priority_rank`.

| Batch | `generated_at` (UTC minute) | Rows written | WARRANTED / NOT WARRANTED / NEEDS REVIEW |
|---|---|---|---|
| 1 | 2026-11-26 02:40 | 60 | 22 / 21 / 17 |
| 2 | 2026-11-26 02:49 | 60 | 31 / 19 / 10 |
| 3 | 2026-11-26 03:05 | 60 | 19 / 26 / 15 |

After batch 3: 180 rows, 180 distinct keys. Totals: WARRANTED 72, NOT WARRANTED 66, NEEDS REVIEW 42. 270 encounters remain pending (450 − 180), so the next runs continue the queue.

### 2a. Date-relative worklist (what moves and why)

- `worklist_tag` (NEW, AT_RISK, PAST_DUE, OPEN) and `days_remaining` are computed against the current date when the worklist is refreshed. They are not frozen at generation time.
- Snapshot on 2026-11-26 UTC: AT_RISK 67, PAST_DUE 50, OPEN 383, NEW 0. NEW is empty today because nothing was denied on the run date.
- NEW repopulates when the daily job runs with that day's `as_of` (the designed 04:00 flow). The hero's 9 days left were measured on the 2026-11-25 run; on 2026-11-26 the hero reads 8 days.

## 3. Counts by recommendation (REAL, after batch 3)

| Recommendation | Rows | Letter PDF | Worksheet PDF | Data sheet PDF | Parse failures |
|---|---|---|---|---|---|
| WARRANTED | 72 | 72 | 72 | 72 | 0 |
| NOT WARRANTED | 66 | 0 | 66 | 66 | 0 |
| NEEDS REVIEW | 42 | 0 | 42 | 42 | 0 |
| **Total** | **180** | 72 | 180 | 180 | 0 |

Data sheet PDFs cover all 450 grounded encounters (`data_sheet_facts`), not only the 180 with an appeal.

## 4. Samples (REAL output, excerpts)

### 4a. WARRANTED: hero claim (`101 / 770000001 / 50000001`), letter excerpt

The letter is 5,828 characters. It cites the right-knee procedure (27447-RT). Excerpt (first 900 characters, verbatim):

```
[Health System Name] Desert Ridge Medical Center [Address Line 1] [City, AZ ZIP] [Phone] | [Fax] | [Website]  Date: [Appeal Submission Date]  BCBS of Arizona Appeals and Grievances Department [BCBSAZ Mailing Address] [City, AZ ZIP]  **RE:** - **Patient:** Elena Marquez - **Date of Birth:** March 14, 1962 - **Member ID:** BCBSAZ-PPO-4471 - **Date of Service:** May 15, 2026 - **Place of Service:** 22 (Outpatient Hospital) - **Claim Number:** 600000000 - **Denial Reason:** CO50 — Services not deemed medically necessary - **Procedure Code(s):** 27447-RT (Total Knee Arthroplasty, Right) - **Rendering Provider:** Desert Ridge Medical Center | NPI: [Provider NPI] | Tax ID: [Provider Tax ID]  ---  Dear BCBS of Arizona Appeals and Grievances Department,  Desert Ridge Medical Center submits this formal first-level appeal on behalf of patient Elena Marquez (DOB 03/14/1962, Member ID BCBSAZ-PPO-4471
```

The facility name in the letter header is generator-produced synthetic text; it is not the customer's name. The letter carries bracketed placeholders for the sender's address, phone and NPI, which the reviewer fills in before submission.

The AI reasoning worksheet is 9,221 characters. It opens with the determination:

```
AI REASONING WORKSHEET:
Determination and one-line rationale
WARRANTED — The clinical documentation clearly demonstrates failed conservative treatment (NSAIDs, supervised PT, corticosteroid injection), severe radiographic disease (Kellgren-Lawrence grade ...
```

Data sheet (`data_sheet_facts`, hero row, deterministic, no LLM; PDF `101_770000001_50000001_datasheet.pdf`). Days remaining are as of the 2026-11-25 run; they read 8 on 2026-11-26:

| Field | Value |
|---|---|
| Patient / DOB / sex | Elena Marquez / 1962-03-14 / F |
| Member ID / claim | BCBSAZ-PPO-4471 / 600000000 |
| Payer (criteria routing) | BCBS of Arizona (commercial), routed to the BCBS criteria set |
| DOS / POS | 2026-05-15 / 22 |
| HCPCS / modifier | 27447 / RT |
| Diagnoses | M17.11, M25.561, Z68.31 |
| Denial | CO50 (medical_necessity), $58,400 billed, $24,850 expected |
| Deadline | appeal_deadline 2026-12-04; 9 days remaining as of the 2026-11-25 run (8 on 2026-11-26); AT_RISK |

### 4b. NOT WARRANTED: encounter `103 / 770000005` (CPT 63650, Cigna, CO55)

No letter (by design). Worksheet opens:

```
AI REASONING WORKSHEET (abridged):
NOT WARRANTED: The sole clinical note explicitly documents that CPT 63650 was performed under an IRB-approved research protocol with no FDA labeling for the indication and no guideline support
```

### 4c. NEEDS REVIEW: encounter `103 / 770000012` (bariatric, Aetna, CO50)

No letter (by design). `needs_review_reason` (abridged, verbatim):

```
- BMI discrepancy unexplained: [2026-07-20 INTAKE] documents BMI 41 / 268 lb, while [2026-08-14 ANESTHESIA_PRE] documents BMI 36 / 245 lb — a 23 lb / 5-point BMI drop in 25 days with no clinical explanation in the record. ...
```

## 5. Guardrails in the generation path (REAL, tested)

- Determination normalised to exactly WARRANTED / NOT WARRANTED / NEEDS REVIEW. Anything else is a `PARSE_FAILURE:` routed to NEEDS REVIEW. Parse failures on the 180 rows: 0.
- Python parser and SQL parse chain agree on the sample responses (see `04_genai_parser_tests.txt`; SQL parity on the warehouse).
- Letters only for WARRANTED. NOT WARRANTED and NEEDS REVIEW store `appeal_letter = NULL`.
- Citations: the prompt requires dated bracket labels such as `[2026-03-14 PT_VISIT]`. Quote-level verification is in `11_eval_180.md`.

## 6. Honest gaps (2026-11-26)

- Quote verification is **moderate, not high**: strict verbatim 54.7%; normalised 85.3% (`11_eval_180.md`).
- Five evaluation misses, all WARRANTED cases routed to NEEDS REVIEW (none unsafe): three SCS trial charts with no procedure note on the billed date, and two bariatric cases (one missing the payer criteria document, one missing supervision documentation). See `11_eval_180.md`.
- No laterality misses remain after the generator fix (the 2026-11-24 TKA misses are gone).

## 7. Chatbot status

Superseded. The 2026-11-24 status in this file (endpoint NOT READY) is no longer true. The endpoint `fe-bar-appeals-chat` is READY (config v3) and the hero-claim invocation is in evidence/09_chatbot.md.

---

## SUPERSEDED: 2026-11-24 generation evidence (before the clean rerun)

Kept for audit only. These figures (120 rows at run 2, 48 / 38 / 34 split, 5,895-character hero letter, NOT WARRANTED sample 770000064, NEEDS REVIEW sample 770000462) came from the earlier data layer. Do not quote them.


Mark: **REAL** = executed on `fevm-appeals-hackathon` (warehouse `559faf81d610a2a1` or serverless job) in this session.
Input data is **SYNTHETIC** (seeded generator, seed 20261124). Model = `databricks-claude-sonnet-4-6` via `ai_query`. All LLM output below is REAL model output, not hand-written.

### 1. Bootstrap object counts (2026-11-24)

| Object | Result |
|---|---|
| `denial_strategy` | 5 rows (CO50, CO55, CO57, CO150, CO186) |
| `med_nec_criteria` (ai_parse_document, CDF on) | 30 chunks: BCBS 19 (`BCBS_Med_Nec_Criteria.pdf`), CMS 11 (`Definition_of_Med_Nec.pdf`) |
| VS Delta Sync index `med_nec_criteria_index` on `appeals-vs-endpoint` | created, `indexed_row_count` = 30, embedding `databricks-gte-large-en`, TRIGGERED |
| `mpfs_indicator_descriptors` (ai_parse_document -> ai_query from Noridian PDF) | 83 rows, 11 indicator groups (incl. `Status Code`, 12 rows) |
| UC functions (`fe_bar_appeals`) | `descriptor_lookup`, `get_appeal`, `get_encounter`, `mpfs_lookup` (all 4; `GRANT EXECUTE` to `account users`) |

Bootstrap ran as a serverless one-time job. The first attempt failed on a status-polling bug (after the criteria table and index were built); the fixed re-run skipped the built objects and completed. The UC functions were created on the second pass, after their source tables existed. A SQL UDF cannot be created while its source table is missing (verified: `42P01`).

### 2. Pipeline stages run (2026-11-24)

| Stage | Result |
|---|---|
| `20_encounter_grounding` | 460 rows (500 gold encounters minus 40 PAST_DUE), 460 distinct `input_hash`, 460 digests. Rebuilt 4 times with identical hashes (one earlier rebuild differed for 3 encounters; see FINDINGS). |
| `25_data_sheet_facts` | 460 rows, 460 distinct `facts_hash`. Re-run leaves it unchanged. |
| `30_generate_appeals` run 1 | 60 rows inserted, 0 updated |
| `30_generate_appeals` run 2 | 60 rows inserted, 0 updated |
| `40_render_pdfs` | 460 data sheets, 120 AI worksheets, 48 letters (one per WARRANTED row) |
| `60_evaluate` | see `05_eval_results.md` |

### 3. Incrementality proof (2026-11-24)

Generation is a MERGE keyed on the encounter. Candidates are rows with no output or a changed `input_hash`, capped at 60 per run, ordered hero first, then `worklist_tag = 'NEW'`, then `priority_rank`.

| Run | Timestamp (UTC) | Rows written | Rows updated | `priority_rank` range | NEW-tagged in batch |
|---|---|---|---|---|---|
| 1 | 2026-11-24 09:49 | 60 | 0 | 1 – 460 | 20 (all NEW encounters) |
| 2 | 2026-11-24 10:00 | 60 | 0 | 41 – 102 | 0 |

- `appeals_output` now holds **120 rows, 120 distinct keys, 2 distinct `generated_at` values**. The 60 run-1 rows keep their 09:49 timestamp, so they were not regenerated.
- Stale check after run 2: `0` output rows whose `input_hash` differs from current grounding. `340` encounters remain pending (460 − 120) for later runs.
- Hero claim (`101 / 770000001 / 50000001`, Elena Marquez, AT_RISK, 9 days) was in batch 1 at rank 1.

### 4. Counts by recommendation (2026-11-24)

| Recommendation | Rows | Letter PDF | Worksheet PDF | Data sheet PDF |
|---|---|---|---|---|
| WARRANTED | 48 | 48 | 48 | 48 |
| NOT WARRANTED | 38 | 0 | 38 | 38 |
| NEEDS REVIEW | 34 | 0 | 34 | 34 |
| **Total** | **120** | | | |

Parse failures: **0** (no output needed to be routed to NEEDS REVIEW by the parser). Model-call errors are not written (`failOnError => false`); none occurred in these runs.

### 5. Samples (2026-11-24)

_Note: customer name redacted (letter headers show `[Health System]`)._

### 5a. WARRANTED — hero claim (`770000001`), letter excerpt
Full letter 5,895 chars; full worksheet 8,612 chars. PDFs: `appeal_pdfs/101_770000001_50000001_letter.pdf`, `..._cheatsheet.pdf`, `..._datasheet.pdf`.

```
**[HEALTH SYSTEM]** ... **Patient:** Elena Marquez | **DOB:** March 14, 1962 | **Sex:** F
**Member ID:** BCBSAZ-PPO-4471 ... **Procedure Code:** 27447-RT (Total Knee Arthroplasty, Right)
Dear BCBS of Arizona Appeals Department,
[Health System], on behalf of patient Elena Marquez, formally appeals the denial of Claim 600000000 ...
```

Worksheet opens with the determination (heading "AI REASONING WORKSHEET"):

```
Determination and one-line rationale
WARRANTED — ...documented failure of multiple conservative treatments with dates and outcomes,
Kellgren-Lawrence grade 4 imaging confirmation, severe functional limitation, and explicit surgical
rationale from the treating orthopedic surgeon.
```

### 5b. NOT WARRANTED — encounter `770000064` (CPT 22612, Aetna)
Letter: none (by design). Worksheet opens: "NOT WARRANTED: the documented clinical evidence clearly fails the CMS medical necessity criteria for lumbar spinal fusion (CPT 22612) ... the treating orthopedic surgeon explicitly stated fusion was not indicated."

### 5c. NEEDS REVIEW — encounter `770000462` (spinal cord stimulation, CO55)
Letter: none (by design). `needs_review_reason` lists the specific gaps, each tied to a dated note:
- FDA device approval/clearance pathway undocumented (consent form `[2026-10-04 PAIN_MGMT]` gives no PMA/510(k))
- Protocol number in consent form conflicts with "standard care" assertion
- Evidence citations "to be attached" but not present
- No treating-physician letter of medical necessity
- No documented failed conservative treatment with dates and outcomes
- No imaging reports; no functional-limitation measures
- Procedure note date (2026-10-04) differs from claim DOS (2026-11-13)

### 6. Guardrails (2026-11-24)

- Determination normalised to exactly WARRANTED / NOT WARRANTED / NEEDS REVIEW. Anything else is a `PARSE_FAILURE:` routed to NEEDS REVIEW.
- Python parser and SQL parse chain agree on 13 sample responses (see `04_genai_parser_tests.txt`: 14 pytest cases pass; SQL parity run on the warehouse).
- Letters only for WARRANTED. NOT WARRANTED and NEEDS REVIEW store `appeal_letter = NULL`.
- Citations: prompt requires dated bracket labels such as `[2026-03-14 PT_VISIT]`. Quote-level verification is reported in `05_eval_results.md`.

### 7. Honest gaps (2026-11-24)

- Quote verification is **moderate, not high**. Strict verbatim match is 55%; a normalised match (punctuation, ellipses) is 87%. Remaining misses are paraphrased criteria, prompt echoes, and list numbering. See `05_eval_results.md`.
- Two of the four eval misses are genuine laterality conflicts in the synthetic data (claim billed LT, every note documents RT). The model's NEEDS REVIEW is defensible; this is a data-quality finding, not a generation bug. Details in `05_eval_results.md`.
- Gold was refreshed by Agent A during the session (NEW tag count changed 23 → 20, OPEN 362 → 365). This is an upstream change, not a grounding error.

### 8. Chatbot status (2026-11-24; superseded by section 7 above)

- UC model `appeals_hackathon_catalog.fe_bar_appeals.appeals_chat_agent` version 1 logged and aliased `prod`. The serverless build environment imports the agent and resolves its packages.
- Endpoint `fe-bar-appeals-chat` exists but is **NOT READY**: `config_update = UPDATE_FAILED`, served entity `DEPLOYMENT_FAILED` with "credentials required by the served entities failed to generate". This is the OAuth passthrough for the four UC functions and the VS index. The build succeeded; the credential step did not.
- The first deploy attempt failed on `log_model(name=...)`, an argument the serverless MLflow does not accept. The second failed on `ResponsesAgent`, which needs MLflow 3.1+. The third passed the MLflow pin and reached the endpoint-credential stage.
- Next step (not done in this session): check the endpoint owner's access to the UC functions and index, or deploy with service-principal auth, then re-deploy. C should not wire a live chat until the state is READY.
