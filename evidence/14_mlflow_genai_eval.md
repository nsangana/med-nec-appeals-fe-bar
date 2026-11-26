# 14 — MLflow 3 GenAI evaluation (groundedness, no fabricated evidence, quote checks, label match)

Source: job task `genai_evaluate` (`pipeline/65_genai_evaluate.py`), run alone with
`databricks bundle run fe_bar_appeals_job --only genai_evaluate --profile fevm-appeals-hackathon`.
Synthetic data only. Labels are the generator's designed cases. Results tables:
`appeals_hackathon_catalog.fe_bar_appeals.genai_eval_summary` and `genai_eval_results`.

## 1. Run identity

| Item | Value |
|---|---|
| **Current run** | job run `263358598052015` (SUCCESS, about 2 min, judge calls only); Delta run `b33ad37c-6321-44c3-adb6-1723546928a8`; MLflow experiment `/Shared/fe-bar-appeals-eval` (id `3809195264341261`), MLflow run `a91c379499cd4368aed42cff7824517b` |
| Superseded: MLflow run `b5609faba6534b5a9d6aa772f3c85e18` (Delta `21d98aa5-…`, job run `127892055268570`) | **Superseded.** Reason: the groundedness context left out the CLAIM-block identifiers (patient name, member ID, claim number and similar) that the generator saw, so correctly grounded letters were marked ungrounded. The context was rebuilt from the generator's own prompt blocks and the same 60 rows were rerun. Kept in the experiment and the Delta tables as a record. |
| Superseded: job run `348496743623928` (MLflow `ca079c25…`) | First attempt, aggregation bug (NULL pass rates). Its Delta rows were deleted; the MLflow run stays as a record. |
| Judge model | `databricks:/databricks-claude-sonnet-4-6` (Databricks-hosted) |
| Rows evaluated | 60 (the 60 most recent `appeals_output` rows by `generated_at`, batch 3). `appeals_output` has 180 rows. 0 excluded for a grounding change. |
| Traces | 60 (one per row), state OK, 2 spans each (root replay + RETRIEVER), 0 scorer errors |

## 2. What the run does

Each row is replayed as a trace: `appeal_generation_replay` (root) → `grounding_retrieval` (RETRIEVER span). The replay
returns the **stored** determination, letter and worksheet; no generation call is made.

**Retrieval context (the groundedness judge's grounding).** Built by `genai/eval_logic.generation_blocks`, which renders the
same fields, order and wording as the CLAIM, criteria, MPFS, dated-notes, digest and denial blocks in
`pipeline/30_generate_appeals.sql`. A unit test checks every fixed literal against that SQL file, so the two cannot drift.
Seven chunks: claim (includes patient name, DOB, sex, payer, member ID, claim number, DOS, POS, CPT/HCPCS, modifiers, ICD-10,
charges, provider), denial line, criteria, dated notes, clinical digest, MPFS context, and the generator's placeholder rule.

Labels (`eval_case_labels`) are passed as `expectations` and read only by `determination_matches_label`. They never reach
generation.

## 3. Scorers

| Scorer | Type | Definition |
|---|---|---|
| `groundedness` | Built-in `RetrievalGroundedness` (judge: Sonnet 4.6) | Built-in definition: facts in the response are implied by the information in the retrieval step. Value `yes` = pass. The built-in prompt cannot be edited; the placeholder rule is therefore given to the judge inside the retrieval context (chunk `generation_rules`). |
| `no_fabricated_evidence` | `Guidelines` (judge: Sonnet 4.6) | Text below. Value `yes` = pass. |
| `quote_verified_normalised` / `quote_verified_strict` | Deterministic `@scorer` | Quoted spans (>= 20 chars, double quotes, one line) in letter + worksheet, checked against the grounding. Normalised ignores punctuation/case and splits on ellipses; strict is verbatim after whitespace normalisation. Same logic as `60_evaluate.py`. |
| `determination_matches_label` | Deterministic `@scorer` | Predicted determination equals `expected_determination`. Eval only. |

No-fabrication guideline (verbatim):

> The response must not contain any date, test or lab result, score, measurement, procedure, device, medication, treatment, or clinical event that is absent from the retrieved context (the dated clinical notes, the clinical digest, the criteria and the claim facts). Every dated clinical fact cited in brackets, for example [2026-03-14 PT_VISIT], must match a dated note in the context. Identifiers copied from the claim facts are in the context and are not violations. Stating that a fact is unknown, missing or needs review is compliant. Bracketed placeholders such as [Provider NPI], [Health System Name] and [Member ID] are instructed template fields the generator was told to use when a value is not supplied; they are allowed and are not claims. Fail the response if any invented or mismatched evidence appears.

## 4. Results (60 rows, run `b33ad37c…`)

Quote metrics (per quote, the comparable figures; 661 quoted spans in these 60 rows):

| Metric | 60 rows (this run) | 180 rows (`11_eval_180.md`) |
|---|---|---|
| Quote verified, **normalised** | **89.7%** (593 / 661) | 85.3% |
| Quote verified, **strict** | **58.7%** (388 / 661) | 54.7% |

Per-scorer pass rates (rows):

| Scorer | Pass | Scored | Pass rate |
|---|---|---|---|
| `groundedness` | 59 | 60 | **98.3%** |
| `no_fabricated_evidence` | 58 | 60 | **96.7%** |
| `determination_matches_label` | 57 | 60 | **95.0%** |

Detail (not a headline): rows where every quoted span verifies. Strict 0 of 60 (one unverified span fails the whole row).
Normalised 23 of 60 (38.3%). A single paraphrase fails a row, so these row-level figures understate how well quotes match.

Change against the superseded run (same 60 rows):

| Scorer | Superseded `b5609fab…` | Current `a91c379…` |
|---|---|---|
| groundedness | 83.3% (50/60) | 98.3% (59/60) |
| no_fabricated_evidence | 98.3% (59/60) | 96.7% (58/60) |
| determination_matches_label | 95.0% | 95.0% |
| quote per-quote normalised / strict | 89.7% / 58.7% | 89.7% / 58.7% (unchanged; quote logic not changed) |

The groundedness change is the context fix. The small no-fabrication change is one judge verdict (section 5).

Determination mismatches (3, all WARRANTED → NEEDS REVIEW, the same date-of-service conflicts as the `11_eval_180.md`
section 4 list): PCNs 770000081, 770000204, 770000378. No unsafe call (WARRANTED where not expected).

## 5. Remaining judge fails (current run)

Groundedness: **one** row.

- **PCN 770000483** (expected NEEDS REVIEW, predicted NEEDS REVIEW), trace `tr-474c2a4e5c5a005a8c34e72791dec566`.
  Verdict rationale (end of the judge's text): the core claim facts, denial and notes are supported, but several worksheet
  statements rely on external clinical knowledge not in the document: a troponin threshold interpretation, the NSTEMI definition,
  the CPT 99223 medical-decision-making or 75-minute requirement, and risk-stratification scores. The judge fails the row on
  those. This is a genuine grounding gap in the worksheet's reasoning, and the row is still correctly NEEDS REVIEW.

No-fabrication: **two** rows.

- **PCN 770000472** (expected NEEDS REVIEW), trace `tr-668ec55dccc81dfb9f2a5c6ff985e08e`. Judge: the worksheet's
  "≥75 minutes" threshold for 99223 is an invented coding fact not in the context. The listed scores (HEART, TIMI) are named
  as absent. Genuine, same class as the groundedness finding above.
- **PCN 770000162** (expected NOT WARRANTED, predicted NOT WARRANTED), trace `tr-e7f45230788b96fa82b1fff8d1b9397f`. The judge
  works through each cited fact, concludes "the response complies with the guideline", and then returns **no**. The verdict
  contradicts the judge's own reasoning. Judge noise; reported, not overridden.

Determination mismatches (3): PCNs 770000081, 770000204, 770000378 (see section 4).

## 6. Example rows (current run)

**(a) Pass.** PCN 770000003 (WARRANTED, expected WARRANTED), trace `tr-73f4d5d75321369e0685229ff9461c2a`. groundedness yes,
no_fabricated_evidence yes, determination yes. Quotes 18/18 normalised, 11/18 strict. The claim chunk now carries the patient name,
so the identifier flag that appeared earlier no longer fires.

**(b) Judge-flagged.** PCN 770000483 (NEEDS REVIEW, expected NEEDS REVIEW), trace `tr-474c2a4e5c5a005a8c34e72791dec566`,
groundedness **no** (external clinical and CPT knowledge in the worksheet; section 5).

**(c) NEEDS REVIEW.** PCN 770000462 (expected NEEDS REVIEW, predicted NEEDS REVIEW), trace
`tr-557d4c859f83a9dfe9efc4927a995295`. groundedness yes, no_fabricated_evidence yes, determination yes. Quotes 8/11 normalised,
6/11 strict. The model declined to write a letter because the FDA device status is undocumented in the chart. This is the
designed safe outcome.

## 7. Cost estimate vs measured

Estimate (printed by the job before any judge call; token proxies: characters / 4 plus 700 prompt tokens per call; 400 output
tokens per call; Sonnet 4.6 list $3 input / $15 output per 1M tokens; 2 judge calls per row):

| | Rows | Judge calls | Est. cost |
|---|---|---|---|
| Current run | 60 | 120 | **$2.41** (about $0.040 / row; the richer claim context added about $0.05) |
| Full 180 (not run) | 180 | 360 | about **$7.2**, above the $5 cap |

The 180-row evaluation was not run. The job refuses any run whose estimate exceeds `cost_cap_usd` (job parameter
`genai_cost_cap_usd`, default 5). The default `genai_max_rows` is 60.

Measured: **pending**. `system.billing.usage` had not posted this run at the check time; re-check with
`usage_metadata.job_run_id = '263358598052015'`.

## 8. Reading the groundedness and quote metrics together

- They measure different things. The quote metrics check copying: whether a quoted span appears in the grounding. Groundedness
  checks support: whether each claim is implied by the grounding, verbatim or not.
- Quote misses occur in both grounded and ungrounded rows, and the earlier cross-tab (superseded run) showed no ungrounded row
  with every span verbatim. Quotes are therefore a weak proxy for groundedness; neither substitutes for the other.
- The superseded run's groundedness drop was the identifier artifact. With the claim block in the context the remaining judge
  flags are about worksheet reasoning that goes beyond the notes and criteria. That is the signal a reviewer should look at.
- Judge variance remains (PCN 770000162 verdict contradicts its reasoning). Treat single-row judge verdicts as noisy and read a
  sample before relying on a rate.

## 8b. Tracing

- Each evaluated row produces one trace with a RETRIEVER span (the grounding) and the replayed generation. The assessments attach to
  the trace; read with `mlflow.search_traces(locations=[experiment_id], run_id=...)`.
- Chat endpoint `fe-bar-appeals-chat` (read-only check, not redeployed): `ENABLE_MLFLOW_TRACING=true`,
  `MLFLOW_EXPERIMENT_ID=775120465253827` (`/Users/naveen.sangana@databricks.com/fe-bar-appeals-chat`). `search_traces` returned
  **0 traces** there and in `/Shared/fe-bar-appeals-chat` at check time. No chat traces are recorded yet.

## 9. Deviations and limitations

- **Judge and generator are the same model family** (Claude). Verdicts are not independent of the generator.
- **Stored outputs.** The run evaluates stored generations; it does not test the current prompt or model.
- **Built-in groundedness prompt cannot be customised.** The placeholder rule reaches the judge only through the retrieval context.
- **Quote metric** is on 60_evaluate's definition (patient name excluded from the quote grounding). On the 180 rows, the 60_evaluate
  definition with the name gives 0.5472 / 0.8532, and this definition without the name gives the same numbers.
- **Row-level strict quote pass** is 0% because one span fails the row; shown as a detail only.
- **Cost.** 60 rows, not 180. Measured billing pending.
- **Tests.** Scorer and context logic in `genai/eval_logic.py`; 26 unit tests in `genai/test_eval_logic.py`, including the drift
  guard against `pipeline/30_generate_appeals.sql`. Full repo suite: 79 passing.

## 10. Artifacts

- Notebook: `pipeline/65_genai_evaluate.py` (job task `genai_evaluate`, after `evaluate`; environment `genai_eval`,
  `mlflow[databricks]>=3.1`; retries 1; timeout 3600 s).
- Logic and tests: `genai/eval_logic.py`, `genai/test_eval_logic.py`.
- Delta: `genai_eval_summary` and `genai_eval_results` (current run `b33ad37c…`; superseded `21d98aa5…` kept).
- MLflow: experiment `/Shared/fe-bar-appeals-eval`; current run `a91c379499cd4368aed42cff7824517b`; superseded
  `b5609faba6534b5a9d6aa772f3c85e18` and `ca079c25d7a640c99b5e0131beb11f54`.
