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
- No laterality misses remain after the generator fix.

## 7. Chatbot status

The endpoint `fe-bar-appeals-chat` is READY. The current model version and the hero-claim invocation are in evidence/09_chatbot.md.

History: earlier runs are in git history.

