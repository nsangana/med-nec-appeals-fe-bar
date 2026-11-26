> **SUPERSEDED (2026-11-25).** This is the 120-row evaluation from the 2026-11-24 data layer (96.7% accuracy). Do not cite. The current evaluation is `evidence/11_eval_180.md` (180 rows, 97.2%).

# 05 — Evaluation results (Agent B)

Mark: **REAL** = computed by `pipeline/60_evaluate.py` on `appeals_output` in this session. Labels: `eval_case_labels` (generator ground truth, SYNTHETIC). Labels are joined in the evaluation job only and never given to the model.

## 1. Summary (REAL, run after generation batch 2)

| Metric | Value |
|---|---|
| Encounters evaluated | 120 of 120 generated (coverage 100% of generated rows) |
| Accuracy | **96.7%** (116 / 120) |
| Unsafe rate (predicted WARRANTED where expected ≠ WARRANTED, over all evaluated) | **0.0%** (0 / 120) |
| Parse failures | 0 |
| quote_verified_rate, strict verbatim (metric only) | 55.3% (1,019 / 1,843 quoted spans) |
| quote_verified_rate, normalised diagnostic | 87.4% (1,610 / 1,843) |
| Run id / timestamp | `0764a465-9245-47bf-97d6-a70f51973a08` / 2026-11-24T10:06:51Z |

Note on the run history: the evaluation job ran twice on the same 120 rows (a duplicate submission, 47 seconds apart, identical numbers). The second run's rows were removed from `eval_results` and `eval_summary`, so the table holds one run.

Batch-1-only evaluation (60 rows, earlier and superseded) gave accuracy 98.3% and unsafe rate 0%. It is not the reported number. The evaluate job's schema changed afterwards (quote check fixed), so those batch-1 rows were dropped.

## 2. Per-class precision and recall (REAL)

| Class | Support (expected) | Precision | Recall |
|---|---|---|---|
| WARRANTED | 52 | 1.000 | 0.923 |
| NOT WARRANTED | 38 | 1.000 | 1.000 |
| NEEDS REVIEW | 30 | 0.882 | 1.000 |

## 3. Confusion matrix (REAL; rows = expected, columns = predicted)

| expected \ predicted | WARRANTED | NOT WARRANTED | NEEDS REVIEW |
|---|---|---|---|
| **WARRANTED** | 48 | 0 | 4 |
| **NOT WARRANTED** | 0 | 38 | 0 |
| **NEEDS REVIEW** | 0 | 0 | 30 |

## 4. Scenario breakdown (REAL, selected)

| Scenario (generator label) | Evaluated | Correct |
|---|---|---|
| lumbar_fusion:fusion_full_chain_with_instability | 18 | 18 |
| tka:no_conservative_care_mild_imaging | 14 | 14 |
| tka:full_conservative_chain | 13 | 11 |
| bariatric:supervised_program_comorbidities_psych_cleared | 12 | 11 |
| scs_trial:fda_labeled_use_guideline_supported | 4 | 3 |
| all other scenarios | 59 | 59 |

## 5. Misclassified examples (REAL model outputs, reasons truncated)

All four errors are WARRANTED → NEEDS REVIEW. None is WARRANTED → NOT WARRANTED or a wrong-direction approval.

**a. Encounter `770000219` (TKA, full conservative chain), expected WARRANTED.** The model flagged a laterality conflict: CPT 27447 billed **LT** on claim 600000218, but every dated note (`[2026-01-22 RX_HISTORY]` … `[2026-08-20 ORTHO_CONSULT]`) documents **right** knee pathology and the surgeon wrote "27447-RT". It also flagged a missing operative note for DOS 2026-09-19.
*Analysis:* the flag is correct for the data as generated. The generator's label assumes a clean chart, but the claim and chart disagree on side. In production this is a real stop-and-check item.

**b. Encounter `770000306` (TKA, full conservative chain), expected WARRANTED.** Same pattern: claim 27447-**LT**, ICD-10 M17.12 (left knee) on the claim, notes and the consult document **right** knee.
*Analysis:* same as (a). Two of the four misses are this data-quality conflict, and the model's NEEDS REVIEW is defensible. The generator should either remove the laterality conflict from these WARRANTED cases or relabel them.

**c. Encounter `770000119` (bariatric, supervised program with comorbidities and psych clearance), expected WARRANTED.** The model asked for the **BCBSAZ bariatric-surgery Evidence-Based Criteria document** (CPT 43775), which it says is required before WARRANTED can be stated.
*Analysis:* the grounding corpus holds only the general BCBS definitions document. The bariatric-specific criteria are not in `med_nec_criteria`. The model was honest about that gap, and the never-fabricate rule forced NEEDS REVIEW. This is a **corpus gap**, not a reasoning failure. Fix: add the specialty EBC to `raw_references` and rebuild the index.

**d. Encounter `770000373` (spinal cord stimulator trial, FDA labelled use), expected WARRANTED.** The note states "FDA-approved (PMA) for this indication" and "randomized trial evidence … cited in the plan", but gives no device name, PMA number or citation. The model asked for the PMA letter and the trial citations.
*Analysis:* reasonable under the rule that every criterion must be grounded in the record. The generator's note text asserts approval without the document. Same corpus-and-record pattern as (c).

## 6. Quote verification (metric only; does not change determinations)

Quoted spans are double-quoted text of at least 20 characters, on a single line, in the letter or AI worksheet. A span counts as verified when it appears verbatim (whitespace-normalised) in the grounding inputs: dated notes, criteria block, MPFS context, claim fields.

| Measure | Result |
|---|---|
| Strict verbatim | **55.3%** (1,019 / 1,843) |
| Normalised (ignores punctuation and case, splits on ellipses) | 87.4% (1,610 / 1,843) |

The gap is partly **PDF extraction artifacts** in the criteria text (for example `Evidence- Based`, footnote digits fused to words such as `evaluation4`, bullet glyphs `•`) and partly **genuine paraphrase**. Examples of genuine non-verbatim spans:
- A prompt echo, "BCBS Arizona commercial → BCBS criteria" (quoting the instructions, not evidence).
- A paraphrased criterion, "Meet the standards of good medical practice…" where the source reads differently.
- A paraphrased note, "approximately 3 weeks of relief" where the note gives different wording.

Reading: the model usually cites real text, but it paraphrases often enough that strict verbatim quoting cannot be claimed. The worksheets are labelled "AI reasoning" for that reason. The data sheet, which quotes notes and criteria verbatim, is the source of record.

## 7. What this does and does not show

- Accuracy and unsafe rate are measured against **synthetic** generator labels on **synthetic** data. They show consistency with the generator's scenarios, not clinical validity.
- Unsafe rate is 0 on 120 rows. That is a small sample; the per-class CI is wide.
- The NEEDS REVIEW class is the most conservative. Its 88% precision means some WARRANTED-labelled cases are flagged for review. That is the designed failure direction.
- No groundedness scorers (`mlflow.genai.evaluate`) were run; that is P1. The MLflow run logs the metrics above to `~@databricks.com/fe-bar-appeals-eval`.
