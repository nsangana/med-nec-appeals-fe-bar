# 07 Genie benchmarks (FE Bar – Medical Necessity Appeals)

- Space: `01f1e7ec913217158b231c3e2f18fa20` (default workspace permissions; not shared)
- Run at: 2026-11-25 22:52 UTC (Genie Conversation API via CLI profile `fevm-appeals-hackathon`)
- appeals_output rows at run: 180
- Pass rate: **14/14** graded; PENDING_DATA: 0 (need generated appeals)
- Grading: Genie query COMPLETED with SQL; expected SQL (run on the same warehouse) values all present in Genie's result rows; empty expected => empty Genie result.
- Expected SQL is in `genie/benchmarks.json`. Results are real (not simulated).
- Expectations: `benchmarks.json` holds SQL only, with no hard-coded values. The expected values are recomputed from the 2026-11-25 data on every run, so none needed a manual update after the rerun.
- Re-run: `python3 genie/run_benchmarks.py` (writes this file). Previous run (2026-11-24, 120-row state) is kept below as SUPERSEDED.

| ID | Question | Result | Genie SQL (first 200 chars) | Note |
|---|---|---|---|---|
| B01 | How much appealable revenue is at deadline risk this week by payer? | PASS | `SELECT   `payer` AS `payer`,   MEASURE(`Revenue At Deadline Risk`) AS `at_risk_revenue` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` WHERE `payer` IS NOT NULL GROUP BY ALL ORDER` | all expected values present |
| B02 | Which payer has the most CO50 denials? | PASS | `WITH `ranked_payers` AS (   SELECT     `payer`,     MEASURE(`Denials In Worklist`) AS `co50_denials`,     RANK() OVER (ORDER BY MEASURE(`Denials In Worklist`) DESC) AS `payer_rank`   FROM `appeals_hac` | all expected values present |
| B03 | What is the status of the claim for Elena Marquez? | PASS | `WITH `w` AS (   SELECT     `FACILITY_ID`,     `PATIENT_CONTROL_NUMBER`,     `ENCOUNTER_NBR`,     `patient_name`,     `payer_name`,     `denial_code`,     `deadline_status`,     `days_remaining`,     `` | all expected values present |
| B04 | What share of appeals were routed to NEEDS REVIEW, and why? | PASS | `WITH `share` AS (   SELECT     MEASURE(`Appeals Generated`) AS `appeals_generated`,     MEASURE(`NEEDS REVIEW Rate`) * 100 AS `needs_review_share_pct`   FROM `appeals_hackathon_catalog`.`fe_bar_appeal` | all expected values present |
| B05 | What is the warranted rate by payer type? | PASS | `SELECT   `payer_type`,   MEASURE(`Warranted Rate`) AS `warranted_rate` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` WHERE `payer_type` IS NOT NULL GROUP BY ALL ORDER BY `payer_t` | all expected values present |
| B06 | How many denials were logged as NEW (denied yesterday)? | PASS | `SELECT COUNT(*) AS `new_denials_yesterday` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`gold_denial_worklist` WHERE `denial_date` = date_sub(current_date(), 1)   AND `worklist_tag` IS NOT NULL  ` | all expected values present |
| B07 | What is the cost per appeal? | PASS | `SELECT MEASURE(`Cost Per Appeal (ESTIMATE)`) AS `cost_per_appeal_estimate_usd` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` GROUP BY ALL` | all expected values present |
| B08 | How much expected reimbursement was lost to missed appeal deadlines by payer? | PASS | `SELECT `payer`, MEASURE(`Revenue Lost To Deadline`) AS `revenue_lost_to_deadline` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` WHERE `payer` IS NOT NULL GROUP BY ALL ORDER BY `r` | all expected values present |
| B09 | Which 5 encounters have the highest priority score and are still appealable? | PASS | `SELECT `FACILITY_ID`, `PATIENT_CONTROL_NUMBER`, `ENCOUNTER_NBR`, `payer_name`, `denial_code`, `dos`, `appeal_deadline`, `days_remaining`, `deadline_status`, `expected_reimbursement`, `priority_score`,` | all expected values present |
| B10 | How does expected reimbursement compare with total charges by denial code? | PASS | `WITH `expected_by_code` AS (   SELECT     `denial_code`,     MEASURE(`Expected Reimbursement (All Encounters)`) AS `expected_reimbursement_all_encounters`   FROM `appeals_hackathon_catalog`.`fe_bar_ap` | all expected values present |
| B11 | What share of reviewed appeals were approved, meaning submitted? | PASS | `SELECT MEASURE(`Approval Rate`) AS `approval_rate`, MEASURE(`Reviewed Encounters`) AS `reviewed_encounters`, MEASURE(`Appeals Submitted`) AS `appeals_submitted` FROM `appeals_hackathon_catalog`.`fe_ba` | all expected values present |
| B12 | What is the illustrative recoverable revenue by payer? | PASS | `SELECT   `payer`,   MEASURE(`Illustrative Recoverable Revenue (Prototype)`) AS `illustrative_recoverable_revenue` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` WHERE `payer` IS N` | all expected values present |
| B13 | How many denials are in the backlog by worklist tag? | PASS | `SELECT `worklist_tag`, MEASURE(`Denials In Worklist`) AS `denials_in_backlog` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` WHERE `worklist_tag` IS NOT NULL GROUP BY ALL ORDER BY` | all expected values present |
| B14 | What is the AI accuracy and unsafe rate of the latest evaluation run? | PASS | `SELECT `run_ts`, `accuracy`, `unsafe_rate` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`eval_summary` WHERE `run_ts` IS NOT NULL ORDER BY `run_ts` DESC LIMIT 1` | all expected values present |


## Pass rate by stakeholder role

| Role | Pass | Benchmarks |
|---|---|---|
| VP Revenue Cycle | 4/4 | B01, B05, B08, B09 |
| CDAIO | 3/3 | B04, B07, B14 |
| CFO | 2/2 | B10, B12 |
| Director of Denial Management | 3/3 | B06, B11, B13 |
| General analyst | 2/2 | B02, B03 |

# Role: VP Revenue Cycle

## B01: How much appealable revenue is at deadline risk this week by payer?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e92258d11755ae21f8618fe411df`

Genie SQL:
```sql
SELECT
  `payer` AS `payer`,
  MEASURE(`Revenue At Deadline Risk`) AS `at_risk_revenue`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
WHERE `payer` IS NOT NULL
GROUP BY ALL
ORDER BY `at_risk_revenue` DESC
```
Genie result (snippet):

| payer | at_risk_revenue |
|---|---|
| BCBS of Arizona | 118605.41 |
| BCBS of Arizona Medicare Advantage | 103334.26 |
| AHCCCS Medicaid | 70715.92 |
| Aetna | 54099.63999999999 |
| Humana Medicare Advantage | 39356.15 |
| UnitedHealthcare | 32791.56 |
| ... 2 more rows |

Expected SQL:
```sql
SELECT payer, MEASURE(`Revenue At Deadline Risk`) AS at_risk_revenue FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY at_risk_revenue DESC
```
Expected result (snippet):

| payer | at_risk_revenue |
|---|---|
| BCBS of Arizona | 118605.41 |
| BCBS of Arizona Medicare Advantage | 103334.26 |
| AHCCCS Medicaid | 70715.92 |
| Aetna | 54099.63999999999 |
| Humana Medicare Advantage | 39356.15 |
| UnitedHealthcare | 32791.56 |
| ... 2 more rows |

Genie text: **$118,605.41** for **BCBS of Arizona** is the largest amount of appealable revenue currently at deadline risk, followed by these representative payer amounts from the 8 payers in the snapshot:
- **BCBS of Arizona Medicare Advantage** — **$103,334.26**
- **AHCCCS Medicaid** — **$70,715.92**
- **Aetn

## B05: What is the warranted rate by payer type?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e92283e11f6ba7605fa71b73c7b7`

Genie SQL:
```sql
SELECT
  `payer_type`,
  MEASURE(`Warranted Rate`) AS `warranted_rate`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
WHERE `payer_type` IS NOT NULL
GROUP BY ALL
ORDER BY `payer_type` ASC
```
Genie result (snippet):

| payer_type | warranted_rate |
|---|---|
| COMMERCIAL | 0.3813559322033898 |
| MEDICAID | 0.5 |
| MEDICARE_ADVANTAGE | 0.42857142857142855 |

Expected SQL:
```sql
SELECT payer_type, MEASURE(`Warranted Rate`) AS warranted_rate FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY ALL
```
Expected result (snippet):

| payer_type | warranted_rate |
|---|---|
| COMMERCIAL | 0.3813559322033898 |
| MEDICAID | 0.5 |
| MEDICARE_ADVANTAGE | 0.42857142857142855 |

Genie text: Would you like to see these rates broken down by payer name instead of payer type?

## B08: How much expected reimbursement was lost to missed appeal deadlines by payer?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e9229ebf144d852a1000e39f0cd3`

Genie SQL:
```sql
SELECT `payer`, MEASURE(`Revenue Lost To Deadline`) AS `revenue_lost_to_deadline`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
WHERE `payer` IS NOT NULL
GROUP BY ALL
ORDER BY `revenue_lost_to_deadline` DESC
```
Genie result (snippet):

| payer | revenue_lost_to_deadline |
|---|---|
| BCBS of Arizona | 67929.47 |
| UnitedHealthcare | 53515.37 |
| AHCCCS Medicaid | 25889.219999999998 |
| BCBS of Arizona Medicare Advantage | 22495.82 |
| UnitedHealthcare Medicare Advantage | 17276.9 |
| Cigna | 7625.87 |
| ... 2 more rows |

Expected SQL:
```sql
SELECT payer, MEASURE(`Revenue Lost To Deadline`) AS lost_revenue FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY lost_revenue DESC
```
Expected result (snippet):

| payer | lost_revenue |
|---|---|
| BCBS of Arizona | 67929.47 |
| UnitedHealthcare | 53515.37 |
| AHCCCS Medicaid | 25889.219999999998 |
| BCBS of Arizona Medicare Advantage | 22495.82 |
| UnitedHealthcare Medicare Advantage | 17276.9 |
| Cigna | 7625.87 |
| ... 2 more rows |

Genie text: **$67,929.47** was lost to missed appeal deadlines for **BCBS of Arizona**, the highest among the 8 payers shown. Examples include:
- **BCBS of Arizona** — **$67,929.47**
- **UnitedHealthcare** — **$53,515.37**
- **AHCCCS Medicaid** — **$25,889.22**
- **BCBS of Arizona Medicare Advantage** — **$22,4

## B09: Which 5 encounters have the highest priority score and are still appealable?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e922a9121307abaf6719f7950d20`

Genie SQL:
```sql
SELECT `FACILITY_ID`, `PATIENT_CONTROL_NUMBER`, `ENCOUNTER_NBR`, `payer_name`, `denial_code`, `dos`, `appeal_deadline`, `days_remaining`, `deadline_status`, `expected_reimbursement`, `priority_score`, `priority_rank`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`gold_denial_worklist`
WHERE `deadline_status` IS NOT NULL
  AND `priority_rank` IS NOT NULL
  AND `deadline_status` NOT ILIKE '%PAST_DUE%'
ORDER BY `priority_rank` ASC
LIMIT 5
```
Genie result (snippet):

| FACILITY_ID | PATIENT_CONTROL_NUMBER | ENCOUNTER_NBR | payer_name | denial_code | dos | appeal_deadline | days_remaining | deadline_status | expected_reimbursement | priority_score | priority_rank |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 101 | 770000001 | 50000001 | BCBS of Arizona | CO50 | 2026-05-15 | 2026-12-04 | 9 | AT_RISK | 24850.0 | 49700.0 | 1 |
| 102 | 770000203 | 50000203 | Aetna | CO50 | 2026-05-14 | 2026-11-27 | 2 | AT_RISK | 20096.92 | 40193.84 | 2 |
| 101 | 770000394 | 50000394 | BCBS of Arizona Medicare Advantage | CO50 | 2026-08-27 | 2026-11-26 | 1 | AT_RISK | 18585.01 | 37170.02 | 3 |
| 101 | 770000231 | 50000231 | Humana Medicare Advantage | CO50 | 2026-09-05 | 2026-12-06 | 11 | AT_RISK | 18438.19 | 36876.38 | 4 |
| 102 | 770000233 | 50000233 | Aetna | CO50 | 2026-05-20 | 2026-11-30 | 5 | AT_RISK | 17437.31 | 34874.62 | 5 |

Expected SQL:
```sql
SELECT FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR, payer_name, denial_code, priority_rank, priority_score FROM appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist WHERE deadline_status <> 'PAST_DUE' ORDER BY priority_score DESC LIMIT 5
```
Expected result (snippet):

| FACILITY_ID | PATIENT_CONTROL_NUMBER | ENCOUNTER_NBR | payer_name | denial_code | priority_rank | priority_score |
|---|---|---|---|---|---|---|
| 101 | 770000001 | 50000001 | BCBS of Arizona | CO50 | 1 | 49700.0 |
| 102 | 770000203 | 50000203 | Aetna | CO50 | 2 | 40193.84 |
| 101 | 770000394 | 50000394 | BCBS of Arizona Medicare Advantage | CO50 | 3 | 37170.02 |
| 101 | 770000231 | 50000231 | Humana Medicare Advantage | CO50 | 4 | 36876.38 |
| 102 | 770000233 | 50000233 | Aetna | CO50 | 5 | 34874.62 |

Genie text: **5** still-appealable encounters have the highest priority scores, all currently **AT_RISK**.
- **Rank 1:** Encounter **50000001** — **BCBS of Arizona**, priority score **49,700.0**, expected reimbursement **$24,850.00**, **9 days** remaining
- **Rank 2:** Encounter **50000203** — **Aetna**, priori

# Role: CDAIO

## B04: What share of appeals were routed to NEEDS REVIEW, and why?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e922768f1d14b185cf8ee7065f73`

Genie SQL:
```sql
WITH `share` AS (
  SELECT
    MEASURE(`Appeals Generated`) AS `appeals_generated`,
    MEASURE(`NEEDS REVIEW Rate`) * 100 AS `needs_review_share_pct`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
  GROUP BY ALL
),
`reasons` AS (
  SELECT
    COALESCE(`needs_review_reason`, 'NO REASON RECORDED') AS `needs_review_reason`,
    COUNT(*) AS `appeals`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_output`
  WHERE `recommendation` ILIKE '%NEEDS REVIEW%'
  GROUP BY ALL
)
SELECT
  `s`.`appeals_generated`,
  `s`.`needs_review_share_pct`,
  `r`.`needs_review_reason`,
  `r`.`appeals`
FROM `share` `s`
CROSS JOIN `reasons` `r`
ORDER BY `r`.`appeals` DESC
```
Genie result (snippet):

| appeals_generated | needs_review_share_pct | needs_review_reason | appeals |
|---|---|---|---|
| 180 | 23.88888888888889 | - **Physical therapy records absent:** [2026-04-20 PT_EVAL] documents that outside PT records were requested but never r | 1 |
| 180 | 23.88888888888889 | - **MISSING: MRI report (imaging) not in chart.** The [2026-09-19 ORTHO_CONSULT] note states the surgeon reviewed an out | 1 |
| 180 | 23.88888888888889 | • **Conflicting critical care time between two same-day notes:** The critical care attestation documents 25 minutes of c | 1 |
| 180 | 23.88888888888889 | - **FDA regulatory status of the implanted electrode array device is undocumented**: The consent form explicitly notes t | 1 |
| 180 | 23.88888888888889 | - **Contradictory critical care time between two same-date notes:** The critical care attestation in [2026-11-08 CRIT_CA | 1 |
| 180 | 23.88888888888889 | - **Missing MRI/imaging report:** The orthopedic surgeon reviewed an "outside MRI from 2025" [2026-07-28 ORTHO_CONSULT], | 1 |
| ... 37 more rows |

Expected SQL:
```sql
SELECT COALESCE(needs_review_reason, 'NO REASON RECORDED') AS needs_review_reason, COUNT(*) AS appeals FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_output WHERE recommendation = 'NEEDS REVIEW' GROUP BY ALL ORDER BY appeals DESC
```
Expected result (snippet):

| needs_review_reason | appeals |
|---|---|
| • **BMI conflict between intake and pre-operative measurements**: [2026-07-20 INTAKE] documents BMI 41; [2026-08-14 ANES | 1 |
| • **MDM documentation absent:** No medical decision-making narrative (complexity of problems addressed, amount/complexit | 1 |
| - **Repeat troponin result missing:** [2026-05-10 ED_NOTE] documents that a repeat Troponin I was ordered but the result | 1 |
| - **FDA device approval status not documented:** The consent form in [2026-04-14 PAIN_MGMT] explicitly states the device | 1 |
| - **Missing: Repeat troponin I result** — [2026-10-02 ED_NOTE] documents that a repeat troponin was ordered but states " | 1 |
| • **Repeat troponin result absent from chart** — [2026-05-25 ED_NOTE] documents that a repeat troponin I was ordered but | 1 |
| ... 37 more rows |

Genie text: **23.9%** of generated appeals were routed to **NEEDS REVIEW**. The visible reasons were documentation and record issues that required human follow-up, including **missing therapy, imaging, medication, injection, operative, and pre-op records**, **conflicting clinical details**, and **unclear critic

## B07: What is the cost per appeal?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e92296811d0bacad9334f053594a`

Genie SQL:
```sql
SELECT MEASURE(`Cost Per Appeal (ESTIMATE)`) AS `cost_per_appeal_estimate_usd`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
GROUP BY ALL
```
Genie result (snippet):

| cost_per_appeal_estimate_usd |
|---|
| 0.1070 |

Expected SQL:
```sql
SELECT MEASURE(`Cost Per Appeal (ESTIMATE)`) AS cost_per_appeal_estimate_usd FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics
```
Expected result (snippet):

| cost_per_appeal_estimate_usd |
|---|
| 0.1070 |

Genie text: **$0.1070 per appeal** is the current **Cost Per Appeal (ESTIMATE)**. This is an **estimate**, not a measured cost.

## B14: What is the AI accuracy and unsafe rate of the latest evaluation run?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e922d73b1748986ff4f1785db0fb`

Genie SQL:
```sql
SELECT `run_ts`, `accuracy`, `unsafe_rate`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`eval_summary`
WHERE `run_ts` IS NOT NULL
ORDER BY `run_ts` DESC
LIMIT 1
```
Genie result (snippet):

| run_ts | accuracy | unsafe_rate |
|---|---|---|
| 2026-11-25T22:42:27.948Z | 0.9722 | 0.0 |

Expected SQL:
```sql
SELECT accuracy, unsafe_rate FROM appeals_hackathon_catalog.fe_bar_appeals.eval_summary ORDER BY run_ts DESC LIMIT 1
```
Expected result (snippet):

| accuracy | unsafe_rate |
|---|---|
| 0.9722 | 0.0 |

Genie text: **97.22%** accuracy and **0.0%** unsafe rate in the latest evaluation run at **2026-11-25T22:42:27.948Z**. These evaluation labels are **synthetic**, and in this latest run the unsafe rate was **zero**.

# Role: CFO

## B10: How does expected reimbursement compare with total charges by denial code?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e922b5fa1b02aa54d115fea72d51`

Genie SQL:
```sql
WITH `expected_by_code` AS (
  SELECT
    `denial_code`,
    MEASURE(`Expected Reimbursement (All Encounters)`) AS `expected_reimbursement_all_encounters`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
  WHERE `denial_code` IS NOT NULL
  GROUP BY ALL
),
`charges_by_code` AS (
  SELECT
    `denial_code`,
    SUM(`total_charges`) AS `total_charges`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`gold_denial_worklist`
  WHERE `denial_code` IS NOT NULL
  GROUP BY `denial_code`
)
SELECT
  e.`denial_code`,
  e.`expected_reimbursement_all_encounters`,
  c.`total_charges`,
  try_divide(e.`expected_reimbursement_all_encounters`,NULLIF(c.`total_charges`, 0)) AS `expected_reimbursement_to_charges_ratio`
FROM `expected_by_code` e
INNER JOIN `charges_by_code` c
  ON e.`denial_code` = c.`denial_code`
ORDER BY e.`expected_reimbursement_all_encounters` DESC
```
Genie result (snippet):

| denial_code | expected_reimbursement_all_encounters | total_charges | expected_reimbursement_to_charges_ratio |
|---|---|---|---|
| CO50 | 1812376.7100000002 | 4357307.860000003 | 0.41593955906526164 |
| CO186 | 533021.5499999999 | 1322495.0200000005 | 0.4030423872598021 |
| CO55 | 364172.6 | 889544.7200000002 | 0.40939212139891057 |
| CO57 | 139829.85 | 328857.32999999996 | 0.4251991281447186 |
| CO150 | 21205.200000000004 | 50534.01999999999 | 0.4196222663465129 |

Expected SQL:
```sql
SELECT denial_code, SUM(expected_reimbursement) AS expected_reimbursement, SUM(total_charges) AS total_charges FROM appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist GROUP BY denial_code ORDER BY denial_code
```
Expected result (snippet):

| denial_code | expected_reimbursement | total_charges |
|---|---|---|
| CO150 | 21205.200000000004 | 50534.01999999999 |
| CO186 | 533021.5499999999 | 1322495.0200000005 |
| CO50 | 1812376.7100000002 | 4357307.860000003 |
| CO55 | 364172.6 | 889544.7200000002 |
| CO57 | 139829.85 | 328857.32999999996 |

Genie text: **Expected reimbursement is lower than total charges for all 5 denial codes shown, at about 40% to 43% of charges.** Examples include:
- **CO50:** **$1.81M** expected reimbursement vs **$4.36M** in charges (**41.6%**)
- **CO186:** **$533.0K** expected reimbursement vs **$1.32M** in charges (**40.3%*

## B12: What is the illustrative recoverable revenue by payer?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e922c7c7150a833aa08bd7511551`

Genie SQL:
```sql
SELECT
  `payer`,
  MEASURE(`Illustrative Recoverable Revenue (Prototype)`) AS `illustrative_recoverable_revenue`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
WHERE `payer` IS NOT NULL
GROUP BY ALL
ORDER BY `illustrative_recoverable_revenue` DESC
```
Genie result (snippet):

| payer | illustrative_recoverable_revenue |
|---|---|
| BCBS of Arizona | 287251.02999999997 |
| BCBS of Arizona Medicare Advantage | 153955.62999999998 |
| AHCCCS Medicaid | 123603.04999999999 |
| Aetna | 121060.26999999999 |
| UnitedHealthcare | 88236.91999999998 |
| Cigna | 61954.92 |
| ... 2 more rows |

Expected SQL:
```sql
SELECT payer, MEASURE(`Illustrative Recoverable Revenue (Prototype)`) AS illustrative_recoverable FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY illustrative_recoverable DESC
```
Expected result (snippet):

| payer | illustrative_recoverable |
|---|---|
| BCBS of Arizona | 287251.02999999997 |
| BCBS of Arizona Medicare Advantage | 153955.62999999998 |
| AHCCCS Medicaid | 123603.04999999999 |
| Aetna | 121060.26999999999 |
| UnitedHealthcare | 88236.91999999998 |
| Cigna | 61954.92 |
| ... 2 more rows |

Genie text: **$287,251.03** for **BCBS of Arizona** is the highest illustrative recoverable revenue in this synthetic prototype view; this is an illustrative figure, not a forecast or business case.

Examples include:
- **BCBS of Arizona** — **$287,251.03**
- **BCBS of Arizona Medicare Advantage** — **$153,955.

# Role: Director of Denial Management

## B06: How many denials were logged as NEW (denied yesterday)?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e9228bdc1eb18e30b439dad39c0c`

Genie SQL:
```sql
SELECT COUNT(*) AS `new_denials_yesterday`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`gold_denial_worklist`
WHERE `denial_date` = date_sub(current_date(), 1)
  AND `worklist_tag` IS NOT NULL
  AND `worklist_tag` ILIKE '%NEW%'
```
Genie result (snippet):

| new_denials_yesterday |
|---|
| 20 |

Expected SQL:
```sql
SELECT MEASURE(`Denials In Worklist`) AS new_denials FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics WHERE worklist_tag = 'NEW'
```
Expected result (snippet):

| new_denials |
|---|
| 20 |

Genie text: **20** denials were logged as **NEW** with a denial date of **yesterday**. Based on the current worklist snapshot, the count is **20** records where `worklist_tag` includes **NEW** and `denial_date` equals **yesterday**.

## B11: What share of reviewed appeals were approved, meaning submitted?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e922c03b11338f05d1992364b290`

Genie SQL:
```sql
SELECT MEASURE(`Approval Rate`) AS `approval_rate`, MEASURE(`Reviewed Encounters`) AS `reviewed_encounters`, MEASURE(`Appeals Submitted`) AS `appeals_submitted`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
GROUP BY ALL
```
Genie result (snippet):

| approval_rate | reviewed_encounters | appeals_submitted |
|---|---|---|
| 0.3333333333333333 | 3 | 1 |

Expected SQL:
```sql
SELECT MEASURE(`Reviewed Encounters`) AS reviewed, MEASURE(`Approval Rate`) AS approval_rate FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics
```
Expected result (snippet):

| reviewed | approval_rate |
|---|---|
| 3 | 0.3333333333333333 |

Genie text: **33.3%** of reviewed appeals were approved, meaning submitted: **1** submitted appeal out of **3** reviewed encounters. Caveat: the approval rate is based on **simulated reviewer actions** in this demo build, and only **3** encounters were reviewed.

## B13: How many denials are in the backlog by worklist tag?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e922cfba1a9bb1cf2c3231db6390`

Genie SQL:
```sql
SELECT `worklist_tag`, MEASURE(`Denials In Worklist`) AS `denials_in_backlog`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
WHERE `worklist_tag` IS NOT NULL
GROUP BY ALL
ORDER BY `denials_in_backlog` DESC
```
Genie result (snippet):

| worklist_tag | denials_in_backlog |
|---|---|
| OPEN | 365 |
| AT_RISK | 75 |
| PAST_DUE | 40 |
| NEW | 20 |

Expected SQL:
```sql
SELECT worklist_tag, MEASURE(`Denials In Worklist`) AS denials FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY denials DESC
```
Expected result (snippet):

| worklist_tag | denials |
|---|---|
| OPEN | 365 |
| AT_RISK | 75 |
| PAST_DUE | 40 |
| NEW | 20 |

Genie text: **500** denials are in the backlog across **4** worklist tags. By tag: 
- **OPEN:** **365**
- **AT_RISK:** **75**
- **PAST_DUE:** **40**
- **NEW:** **20**

The backlog is concentrated in **OPEN**, which accounts for the clear majority of denials.

# Role: General analyst

## B02: Which payer has the most CO50 denials?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e922637218a9a3157249c47f8398`

Genie SQL:
```sql
WITH `ranked_payers` AS (
  SELECT
    `payer`,
    MEASURE(`Denials In Worklist`) AS `co50_denials`,
    RANK() OVER (ORDER BY MEASURE(`Denials In Worklist`) DESC) AS `payer_rank`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
  WHERE `denial_code` = 'CO50'
    AND `payer` IS NOT NULL
  GROUP BY ALL
)
SELECT
  `payer`,
  `co50_denials`
FROM `ranked_payers`
WHERE `payer_rank` <= 1
ORDER BY `co50_denials` DESC, `payer` ASC
```
Genie result (snippet):

| payer | co50_denials |
|---|---|
| BCBS of Arizona | 56 |

Expected SQL:
```sql
SELECT payer, MEASURE(`Denials In Worklist`) AS co50_denials FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics WHERE denial_code = 'CO50' GROUP BY ALL ORDER BY co50_denials DESC LIMIT 1
```
Expected result (snippet):

| payer | co50_denials |
|---|---|
| BCBS of Arizona | 56 |

Genie text: **56 — BCBS of Arizona** has the most CO50 denials in the worklist. In the returned result set, **BCBS of Arizona** is the top payer with **56** CO50 denials.

## B03: What is the status of the claim for Elena Marquez?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e9226b0718f5abe81d39dccf3829`

Genie SQL:
```sql
WITH `w` AS (
  SELECT
    `FACILITY_ID`,
    `PATIENT_CONTROL_NUMBER`,
    `ENCOUNTER_NBR`,
    `patient_name`,
    `payer_name`,
    `denial_code`,
    `deadline_status`,
    `days_remaining`,
    `expected_reimbursement`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`gold_denial_worklist`
  WHERE `patient_name` ILIKE '%Elena Marquez%'
)
SELECT
  `w`.`patient_name`,
  `w`.`payer_name`,
  `w`.`denial_code`,
  `w`.`deadline_status`,
  `w`.`days_remaining`,
  `w`.`expected_reimbursement`,
  COALESCE(`a`.`recommendation`, 'NOT GENERATED') AS `recommendation`
FROM `w`
LEFT JOIN `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_output` `a`
  ON `w`.`FACILITY_ID` = `a`.`FACILITY_ID`
 AND `w`.`PATIENT_CONTROL_NUMBER` = `a`.`PATIENT_CONTROL_NUMBER`
 AND `w`.`ENCOUNTER_NBR` = `a`.`ENCOUNTER_NBR`
```
Genie result (snippet):

| patient_name | payer_name | denial_code | deadline_status | days_remaining | expected_reimbursement | recommendation |
|---|---|---|---|---|---|---|
| Elena Marquez | BCBS of Arizona | CO50 | AT_RISK | 9 | 24850.0 | WARRANTED |

Expected SQL:
```sql
SELECT patient_name, payer_name, denial_code, deadline_status, days_remaining, expected_reimbursement FROM appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist WHERE patient_name = 'Elena Marquez'
```
Expected result (snippet):

| patient_name | payer_name | denial_code | deadline_status | days_remaining | expected_reimbursement |
|---|---|---|---|---|---|
| Elena Marquez | BCBS of Arizona | CO50 | AT_RISK | 9 | 24850.0 |

Genie text: **9 days remaining** — Elena Marquez’s claim with **BCBS of Arizona** is **AT_RISK** for denial code **CO50**, with **expected reimbursement of $24,850.00**. The appeal recommendation is **WARRANTED**, which is AI output and not a final determination.

---

## SUPERSEDED: 2026-11-24 benchmark run (120-row state, before the clean rerun)

Kept for audit only. Its 14/14 result predates the 2026-11-25 data.


- Space: `01f1e7ec913217158b231c3e2f18fa20` (default workspace permissions; not shared)
- Run at: 2026-11-24 10:19 UTC (Genie Conversation API via CLI profile `fevm-appeals-hackathon`)
- appeals_output rows at run: 120
- Pass rate: **14/14** graded; PENDING_DATA: 0 (need generated appeals)
- Grading: Genie query COMPLETED with SQL; expected SQL (run on the same warehouse) values all present in Genie's result rows; empty expected => empty Genie result.
- Expected SQL is in `genie/benchmarks.json`. Results are real (not simulated).

| ID | Question | Result | Genie SQL (first 200 chars) | Note |
|---|---|---|---|---|
| B01 | How much appealable revenue is at deadline risk this week by payer? | PASS | `SELECT   `payer` AS `payer`,   MEASURE(`Revenue At Deadline Risk`) AS `at_risk_revenue` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` WHERE `payer` IS NOT NULL GROUP BY ALL ORDER` | all expected values present |
| B02 | Which payer has the most CO50 denials? | PASS | `WITH `ranked_payers` AS (   SELECT     `payer`,     MEASURE(`Denials In Worklist`) AS `co50_denials`,     RANK() OVER (ORDER BY MEASURE(`Denials In Worklist`) DESC) AS `payer_rank`   FROM `appeals_hac` | all expected values present |
| B03 | What is the status of the claim for Elena Marquez? | PASS | `WITH `w` AS (   SELECT     `FACILITY_ID`,     `PATIENT_CONTROL_NUMBER`,     `ENCOUNTER_NBR`,     `patient_name`,     `payer_name`,     `denial_code`,     `deadline_status`,     `days_remaining`,     `` | all expected values present |
| B04 | What share of appeals were routed to NEEDS REVIEW, and why? | PASS | `WITH `needs_review_reasons` AS (   SELECT     COALESCE(`needs_review_reason`, 'NO REASON RECORDED') AS `needs_review_reason`,     COUNT(*) AS `appeals`   FROM `appeals_hackathon_catalog`.`fe_bar_appea` | all expected values present |
| B05 | What is the warranted rate by payer type? | PASS | `SELECT   `payer_type`,   MEASURE(`Warranted Rate`) AS `warranted_rate` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` WHERE `payer_type` IS NOT NULL GROUP BY ALL ORDER BY `payer_t` | all expected values present |
| B06 | How many denials were logged as NEW (denied yesterday)? | PASS | `SELECT COUNT(*) AS `new_denials` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`gold_denial_worklist` WHERE `denial_date` = date_sub(current_date(), 1)` | all expected values present |
| B07 | What is the cost per appeal? | PASS | `SELECT MEASURE(`Cost Per Appeal (ESTIMATE)`) AS `cost_per_appeal_estimate_usd` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` GROUP BY ALL` | all expected values present |
| B08 | How much expected reimbursement was lost to missed appeal deadlines by payer? | PASS | `SELECT   `payer`,   MEASURE(`Revenue Lost To Deadline`) AS `revenue_lost_to_deadline` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` WHERE `payer` IS NOT NULL GROUP BY ALL ORDER B` | all expected values present |
| B09 | Which 5 encounters have the highest priority score and are still appealable? | PASS | `WITH ranked AS (   SELECT     `FACILITY_ID`,     `PATIENT_CONTROL_NUMBER`,     `ENCOUNTER_NBR`,     `payer_name`,     `payer_type`,     `denial_code`,     `dos`,     `appeal_deadline`,     `days_remai` | all expected values present |
| B10 | How does expected reimbursement compare with total charges by denial code? | PASS | `WITH `m` AS (   SELECT     `denial_code`,     MEASURE(`Expected Reimbursement (All Encounters)`) AS `expected_reimbursement_all_encounters`   FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals` | all expected values present |
| B11 | What share of reviewed appeals were approved, meaning submitted? | PASS | `SELECT MEASURE(`Approval Rate`) AS `approval_rate`, MEASURE(`Reviewed Encounters`) AS `reviewed_encounters`, MEASURE(`Appeals Submitted`) AS `appeals_submitted` FROM `appeals_hackathon_catalog`.`fe_ba` | all expected values present |
| B12 | What is the illustrative recoverable revenue by payer? | PASS | `SELECT   `payer`,   MEASURE(`Illustrative Recoverable Revenue (Prototype)`) AS `illustrative_recoverable_revenue` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` WHERE `payer` IS N` | all expected values present |
| B13 | How many denials are in the backlog by worklist tag? | PASS | `SELECT   `worklist_tag`,   MEASURE(`Denials In Worklist`) AS `denials_in_backlog` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` WHERE `worklist_tag` IS NOT NULL GROUP BY ALL ORDE` | all expected values present |
| B14 | What is the AI accuracy and unsafe rate of the latest evaluation run? | PASS | `SELECT `run_id`, `run_ts`, `accuracy`, `unsafe_rate` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`eval_summary` WHERE `run_ts` IS NOT NULL ORDER BY `run_ts` DESC LIMIT 1` | all expected values present |


### Pass rate by stakeholder role

| Role | Pass | Benchmarks |
|---|---|---|
| VP Revenue Cycle | 4/4 | B01, B05, B08, B09 |
| CDAIO | 3/3 | B04, B07, B14 |
| CFO | 2/2 | B10, B12 |
| Director of Denial Management | 3/3 | B06, B11, B13 |
| General analyst | 2/2 | B02, B03 |

# Role: VP Revenue Cycle

### B01: How much appealable revenue is at deadline risk this week by payer?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e7f016fc14d8a1afa78a4cd38edd`

Genie SQL:
```sql
SELECT
  `payer` AS `payer`,
  MEASURE(`Revenue At Deadline Risk`) AS `at_risk_revenue`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
WHERE `payer` IS NOT NULL
GROUP BY ALL
ORDER BY `at_risk_revenue` DESC
```
Genie result (snippet):

| payer | at_risk_revenue |
|---|---|
| BCBS of Arizona | 118605.41 |
| BCBS of Arizona Medicare Advantage | 103334.26 |
| AHCCCS Medicaid | 70715.92 |
| Aetna | 54099.63999999999 |
| Humana Medicare Advantage | 39356.15 |
| UnitedHealthcare | 32791.56 |
| ... 2 more rows |

Expected SQL:
```sql
SELECT payer, MEASURE(`Revenue At Deadline Risk`) AS at_risk_revenue FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY at_risk_revenue DESC
```
Expected result (snippet):

| payer | at_risk_revenue |
|---|---|
| BCBS of Arizona | 118605.41 |
| BCBS of Arizona Medicare Advantage | 103334.26 |
| AHCCCS Medicaid | 70715.92 |
| Aetna | 54099.63999999999 |
| Humana Medicare Advantage | 39356.15 |
| UnitedHealthcare | 32791.56 |
| ... 2 more rows |

Genie text: **$118,605.41** is the highest appealable revenue at deadline risk, led by **BCBS of Arizona** in the current worklist snapshot. Examples include:
- **BCBS of Arizona** — **$118,605.41**
- **BCBS of Arizona Medicare Advantage** — **$103,334.26**
- **AHCCCS Medicaid** — **$70,715.92**
- **Aetna** — *

### B05: What is the warranted rate by payer type?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e7f03a201784b65d4ce8e5ef86e3`

Genie SQL:
```sql
SELECT
  `payer_type`,
  MEASURE(`Warranted Rate`) AS `warranted_rate`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
WHERE `payer_type` IS NOT NULL
GROUP BY ALL
ORDER BY `payer_type`
```
Genie result (snippet):

| payer_type | warranted_rate |
|---|---|
| COMMERCIAL | 0.38461538461538464 |
| MEDICAID | 0.5 |
| MEDICARE_ADVANTAGE | 0.4 |

Expected SQL:
```sql
SELECT payer_type, MEASURE(`Warranted Rate`) AS warranted_rate FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY ALL
```
Expected result (snippet):

| payer_type | warranted_rate |
|---|---|
| COMMERCIAL | 0.38461538461538464 |
| MEDICAID | 0.5 |
| MEDICARE_ADVANTAGE | 0.4 |

Genie text: **3 payer types** are shown for warranted rate, and **MEDICAID** is highest at **50.0%**, followed by **MEDICARE_ADVANTAGE** at **40.0%** and **COMMERCIAL** at **38.5%**. This rate is based on generated appeals, and the spread across payer types is relatively narrow, ranging from **38.5% to 50.0%**.

### B08: How much expected reimbursement was lost to missed appeal deadlines by payer?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e7f052f81b8dbdffba8ddbb13470`

Genie SQL:
```sql
SELECT
  `payer`,
  MEASURE(`Revenue Lost To Deadline`) AS `revenue_lost_to_deadline`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
WHERE `payer` IS NOT NULL
GROUP BY ALL
ORDER BY `revenue_lost_to_deadline` DESC
```
Genie result (snippet):

| payer | revenue_lost_to_deadline |
|---|---|
| BCBS of Arizona | 67929.47 |
| UnitedHealthcare | 53515.37 |
| AHCCCS Medicaid | 22775.829999999998 |
| BCBS of Arizona Medicare Advantage | 22495.82 |
| UnitedHealthcare Medicare Advantage | 17276.9 |
| Cigna | 7625.87 |
| ... 2 more rows |

Expected SQL:
```sql
SELECT payer, MEASURE(`Revenue Lost To Deadline`) AS lost_revenue FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY lost_revenue DESC
```
Expected result (snippet):

| payer | lost_revenue |
|---|---|
| BCBS of Arizona | 67929.47 |
| UnitedHealthcare | 53515.37 |
| AHCCCS Medicaid | 22775.829999999998 |
| BCBS of Arizona Medicare Advantage | 22495.82 |
| UnitedHealthcare Medicare Advantage | 17276.9 |
| Cigna | 7625.87 |
| ... 2 more rows |

Genie text: **$67,929.47** was lost to missed appeal deadlines for **BCBS of Arizona**, the highest payer in the results. Examples include:
- **BCBS of Arizona** — **$67,929.47**
- **UnitedHealthcare** — **$53,515.37**
- **AHCCCS Medicaid** — **$22,775.83**
- **BCBS of Arizona Medicare Advantage** — **$22,495.8

### B09: Which 5 encounters have the highest priority score and are still appealable?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e7f05d221d77884ca84a8b8d49c4`

Genie SQL:
```sql
WITH ranked AS (
  SELECT
    `FACILITY_ID`,
    `PATIENT_CONTROL_NUMBER`,
    `ENCOUNTER_NBR`,
    `payer_name`,
    `payer_type`,
    `denial_code`,
    `dos`,
    `appeal_deadline`,
    `days_remaining`,
    `deadline_status`,
    `expected_reimbursement`,
    `priority_score`,
    `priority_rank`,
    ROW_NUMBER() OVER (
      ORDER BY `priority_score` DESC, `priority_rank` ASC, `FACILITY_ID` ASC, `PATIENT_CONTROL_NUMBER` ASC, `ENCOUNTER_NBR` ASC
    ) AS `rn`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`gold_denial_worklist`
  WHERE `deadline_status` IS NOT NULL
    AND `deadline_status` != 'PAST_DUE'
    AND `priority_score` IS NOT NULL
    AND `priority_rank` IS NOT NULL
    AND `FACILITY_ID` IS NOT NULL
    AND `PATIENT_CONTROL_NUMBER` IS NOT NULL
    AND `ENCOUNTER_NBR` IS NOT NULL
)
SELECT
  `FACILITY_ID`,
  `PATIENT_CONTROL_NUMBER`,
  `ENCOUNTER_NBR`,
  `payer_name`,
  `payer_type`,
  `denial_code`,
  `dos`,
  `appeal_deadline`,
  `days_remaining`,
  `deadline_status`,
  `expected_reimbursement`,
  `priority_score`,
  `priority_rank`
FROM ranked
WHERE `rn` <= 5
ORDER BY `priority_score` DESC, `priority_rank` ASC, `FACILITY_ID` ASC, `PATIENT_CONTROL_NUMBER` ASC, `ENCOUNTER_NBR` ASC
```
Genie result (snippet):

| FACILITY_ID | PATIENT_CONTROL_NUMBER | ENCOUNTER_NBR | payer_name | payer_type | denial_code | dos | appeal_deadline | days_remaining | deadline_status | expected_reimbursement | priority_score | priority_rank |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 101 | 770000001 | 50000001 | BCBS of Arizona | COMMERCIAL | CO50 | 2026-05-14 | 2026-12-03 | 9 | AT_RISK | 24850.0 | 49700.0 | 1 |
| 102 | 770000203 | 50000203 | Aetna | COMMERCIAL | CO50 | 2026-05-13 | 2026-11-26 | 2 | AT_RISK | 20096.92 | 40193.84 | 2 |
| 101 | 770000394 | 50000394 | BCBS of Arizona Medicare Advantage | MEDICARE_ADVANTAGE | CO50 | 2026-08-26 | 2026-11-25 | 1 | AT_RISK | 18585.01 | 37170.02 | 3 |
| 101 | 770000231 | 50000231 | Humana Medicare Advantage | MEDICARE_ADVANTAGE | CO50 | 2026-09-04 | 2026-12-05 | 11 | AT_RISK | 18438.19 | 36876.38 | 4 |
| 102 | 770000233 | 50000233 | Aetna | COMMERCIAL | CO50 | 2026-05-19 | 2026-11-29 | 5 | AT_RISK | 17437.31 | 34874.62 | 5 |

Expected SQL:
```sql
SELECT FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR, payer_name, denial_code, priority_rank, priority_score FROM appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist WHERE deadline_status <> 'PAST_DUE' ORDER BY priority_score DESC LIMIT 5
```
Expected result (snippet):

| FACILITY_ID | PATIENT_CONTROL_NUMBER | ENCOUNTER_NBR | payer_name | denial_code | priority_rank | priority_score |
|---|---|---|---|---|---|---|
| 101 | 770000001 | 50000001 | BCBS of Arizona | CO50 | 1 | 49700.0 |
| 102 | 770000203 | 50000203 | Aetna | CO50 | 2 | 40193.84 |
| 101 | 770000394 | 50000394 | BCBS of Arizona Medicare Advantage | CO50 | 3 | 37170.02 |
| 101 | 770000231 | 50000231 | Humana Medicare Advantage | CO50 | 4 | 36876.38 |
| 102 | 770000233 | 50000233 | Aetna | CO50 | 5 | 34874.62 |

Genie text: **5** encounters are the highest-priority still appealable cases, and all **5** are currently **AT_RISK** rather than past due.

Examples include:
- **Priority rank 1**: Encounter **50000001** at facility **101** with **BCBS of Arizona** — priority score **49,700.00**, expected reimbursement **$24,8

# Role: CDAIO

### B04: What share of appeals were routed to NEEDS REVIEW, and why?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e7f02fef13f598ef7effa1684afe`

Genie SQL:
```sql
WITH `needs_review_reasons` AS (
  SELECT
    COALESCE(`needs_review_reason`, 'NO REASON RECORDED') AS `needs_review_reason`,
    COUNT(*) AS `appeals`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_output`
  WHERE `recommendation` = 'NEEDS REVIEW'
  GROUP BY ALL
),
`needs_review_share` AS (
  SELECT
    MEASURE(`NEEDS REVIEW Rate`) * 100 AS `needs_review_share_pct`,
    MEASURE(`Appeals Generated`) AS `appeals_generated`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
  GROUP BY ALL
)
SELECT
  s.`needs_review_share_pct`,
  s.`appeals_generated`,
  r.`needs_review_reason`,
  r.`appeals`
FROM `needs_review_share` s
CROSS JOIN `needs_review_reasons` r
ORDER BY r.`appeals` DESC
```
Genie result (snippet):

| needs_review_share_pct | appeals_generated | needs_review_reason | appeals |
|---|---|---|---|
| 28.333333333333332 | 120 | - **Missing repeat troponin result:** [2026-10-31 ED_NOTE] documents that a repeat troponin I was ordered but states "re | 1 |
| 28.333333333333332 | 120 | - **Outside physical therapy records are absent**: [2026-04-19 PT_EVAL] documents that records were requested from the o | 1 |
| 28.333333333333332 | 120 | - **Missing: Physical therapy records with dates and outcomes** — [2026-02-05 PRIMARY_CARE] documents only a patient rep | 1 |
| 28.333333333333332 | 120 | - **BMI/weight conflict unresolved**: [2026-07-30 INTAKE] records BMI 41 and weight 268 lb; [2026-08-24 ANESTHESIA_PRE]  | 1 |
| 28.333333333333332 | 120 | • **BMI conflict between intake and pre-operative visit:** Intake BMI documented as 41 [2026-04-29 INTAKE] but pre-anest | 1 |
| 28.333333333333332 | 120 | - **MRI report not in chart:** The 2025 outside MRI was reviewed by the surgeon per [2026-06-13 ORTHO_CONSULT] but the a | 1 |
| ... 28 more rows |

Expected SQL:
```sql
SELECT COALESCE(needs_review_reason, 'NO REASON RECORDED') AS needs_review_reason, COUNT(*) AS appeals FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_output WHERE recommendation = 'NEEDS REVIEW' GROUP BY ALL ORDER BY appeals DESC
```
Expected result (snippet):

| needs_review_reason | appeals |
|---|---|
| • **FDA device approval/clearance pathway undocumented**: The consent form in [2026-10-04 PAIN_MGMT] does not specify wh | 1 |
| - **Missing repeat troponin result:** [2026-10-31 ED_NOTE] documents that a repeat troponin I was ordered but states "re | 1 |
| - **Conflicting critical care time between two same-date notes**: The critical care attestation in [2026-11-07 CRIT_CARE | 1 |
| - **Conflicting critical care time between two same-day notes:** The critical care attestation in [2026-10-26 CRIT_CARE_ | 1 |
| - **Missing: Medical Decision-Making (MDM) documentation** — [2026-10-29 ED_NOTE] explicitly states MDM is not documente | 1 |
| - **Missing: Outside MRI report (2025) — not present in chart.** The orthopedic surgeon reviewed an outside MRI from 202 | 1 |
| ... 28 more rows |

Genie text: **28.3%** of generated appeals were routed to **NEEDS REVIEW**. The visible reasons point to documentation gaps or conflicts, including **missing repeat troponin and utilization review documentation**, **absent outside physical therapy and imaging records**, and **missing MRI, epidural injection, an

### B07: What is the cost per appeal?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e7f04bae183db0fbaf13e4b86db6`

Genie SQL:
```sql
SELECT MEASURE(`Cost Per Appeal (ESTIMATE)`) AS `cost_per_appeal_estimate_usd`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
GROUP BY ALL
```
Genie result (snippet):

| cost_per_appeal_estimate_usd |
|---|
| 1.0000 |

Expected SQL:
```sql
SELECT MEASURE(`Cost Per Appeal (ESTIMATE)`) AS cost_per_appeal_estimate_usd FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics
```
Expected result (snippet):

| cost_per_appeal_estimate_usd |
|---|
| 1.0000 |

Genie text: **$1.00** is the **estimated** cost per appeal. This is a placeholder estimate from `appeals_metrics`, not a measured operating cost.

### B14: What is the AI accuracy and unsafe rate of the latest evaluation run?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e7f0920b155e84fe5b2bc4fe2062`

Genie SQL:
```sql
SELECT `run_id`, `run_ts`, `accuracy`, `unsafe_rate`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`eval_summary`
WHERE `run_ts` IS NOT NULL
ORDER BY `run_ts` DESC
LIMIT 1
```
Genie result (snippet):

| run_id | run_ts | accuracy | unsafe_rate |
|---|---|---|---|
| 0764a465-9245-47bf-97d6-a70f51973a08 | 2026-11-24T10:06:51.238Z | 0.9667 | 0.0 |

Expected SQL:
```sql
SELECT accuracy, unsafe_rate FROM appeals_hackathon_catalog.fe_bar_appeals.eval_summary ORDER BY run_ts DESC LIMIT 1
```
Expected result (snippet):

| accuracy | unsafe_rate |
|---|---|
| 0.9667 | 0.0 |

Genie text: **96.67% accuracy** and **0.0% unsafe rate** were recorded for the latest evaluation run, run ID `0764a465-9245-47bf-97d6-a70f51973a08`, completed at `2026-11-24T10:06:51.238Z`. These evaluation labels are **synthetic**, based on the latest row available in `eval_summary`.

# Role: CFO

### B10: How does expected reimbursement compare with total charges by denial code?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e7f069d71c1d91c8489a38badf62`

Genie SQL:
```sql
WITH `m` AS (
  SELECT
    `denial_code`,
    MEASURE(`Expected Reimbursement (All Encounters)`) AS `expected_reimbursement_all_encounters`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
  WHERE `denial_code` IS NOT NULL
  GROUP BY ALL
),
`w` AS (
  SELECT
    `denial_code`,
    SUM(`total_charges`) AS `total_charges`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`gold_denial_worklist`
  WHERE `denial_code` IS NOT NULL
  GROUP BY `denial_code`
)
SELECT
  `m`.`denial_code`,
  `m`.`expected_reimbursement_all_encounters`,
  `w`.`total_charges`,
  try_divide(`m`.`expected_reimbursement_all_encounters`,`w`.`total_charges`) AS `expected_reimbursement_to_charges_ratio`
FROM `m`
INNER JOIN `w`
  ON `m`.`denial_code` = `w`.`denial_code`
ORDER BY `m`.`expected_reimbursement_all_encounters` DESC
```
Genie result (snippet):

| denial_code | expected_reimbursement_all_encounters | total_charges | expected_reimbursement_to_charges_ratio |
|---|---|---|---|
| CO50 | 1812045.2300000002 | 4357307.860000003 | 0.41586348456911626 |
| CO186 | 529908.16 | 1322495.0200000005 | 0.40068820826259127 |
| CO55 | 364172.6 | 889544.7200000002 | 0.40939212139891057 |
| CO57 | 139829.85 | 328857.32999999996 | 0.4251991281447186 |
| CO150 | 21205.200000000004 | 50534.01999999999 | 0.4196222663465129 |

Expected SQL:
```sql
SELECT denial_code, SUM(expected_reimbursement) AS expected_reimbursement, SUM(total_charges) AS total_charges FROM appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist GROUP BY denial_code ORDER BY denial_code
```
Expected result (snippet):

| denial_code | expected_reimbursement | total_charges |
|---|---|---|
| CO150 | 21205.200000000004 | 50534.01999999999 |
| CO186 | 529908.16 | 1322495.0200000005 |
| CO50 | 1812045.2300000002 | 4357307.860000003 |
| CO55 | 364172.6 | 889544.7200000002 |
| CO57 | 139829.85 | 328857.32999999996 |

Genie text: **Expected reimbursement is lower than total charges for every denial code shown, at about 40% to 43% of charges.** Examples include:
- **CO50:** **$1.81M** expected reimbursement vs **$4.36M** in charges (**41.6%**)
- **CO186:** **$529.9K** vs **$1.32M** (**40.1%**)
- **CO55:** **$364.2K** vs **$88

### B12: What is the illustrative recoverable revenue by payer?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e7f07dcd1a468122435809bbfe41`

Genie SQL:
```sql
SELECT
  `payer`,
  MEASURE(`Illustrative Recoverable Revenue (Prototype)`) AS `illustrative_recoverable_revenue`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
WHERE `payer` IS NOT NULL
GROUP BY ALL
ORDER BY `illustrative_recoverable_revenue` DESC
```
Genie result (snippet):

| payer | illustrative_recoverable_revenue |
|---|---|
| BCBS of Arizona | 230072.73999999996 |
| BCBS of Arizona Medicare Advantage | 124689.23999999999 |
| Aetna | 104130.83999999998 |
| AHCCCS Medicaid | 86097.91 |
| Humana Medicare Advantage | 55062.32 |
| Cigna | 54726.19 |
| ... 2 more rows |

Expected SQL:
```sql
SELECT payer, MEASURE(`Illustrative Recoverable Revenue (Prototype)`) AS illustrative_recoverable FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY illustrative_recoverable DESC
```
Expected result (snippet):

| payer | illustrative_recoverable |
|---|---|
| BCBS of Arizona | 230072.73999999996 |
| BCBS of Arizona Medicare Advantage | 124689.23999999999 |
| Aetna | 104130.83999999998 |
| AHCCCS Medicaid | 86097.91 |
| Humana Medicare Advantage | 55062.32 |
| Cigna | 54726.19 |
| ... 2 more rows |

Genie text: **$230,072.74** for **BCBS of Arizona** is the highest illustrative recoverable revenue by payer in this synthetic prototype view. Examples include:
- **BCBS of Arizona** — **$230,072.74**
- **BCBS of Arizona Medicare Advantage** — **$124,689.24**
- **Aetna** — **$104,130.84**
- **AHCCCS Medicaid** 

# Role: Director of Denial Management

### B06: How many denials were logged as NEW (denied yesterday)?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e7f04479138a8fa2ed6540999568`

Genie SQL:
```sql
SELECT COUNT(*) AS `new_denials`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`gold_denial_worklist`
WHERE `denial_date` = date_sub(current_date(), 1)
```
Genie result (snippet):

| new_denials |
|---|
| 20 |

Expected SQL:
```sql
SELECT MEASURE(`Denials In Worklist`) AS new_denials FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics WHERE worklist_tag = 'NEW'
```
Expected result (snippet):

| new_denials |
|---|
| 20 |

Genie text: **20** denials were logged as **NEW** based on `denial_date = yesterday`. This result is a current count of encounters with `denial_date` equal to one day before today.

### B11: What share of reviewed appeals were approved, meaning submitted?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e7f073d318b6b9362926d81f6e79`

Genie SQL:
```sql
SELECT MEASURE(`Approval Rate`) AS `approval_rate`, MEASURE(`Reviewed Encounters`) AS `reviewed_encounters`, MEASURE(`Appeals Submitted`) AS `appeals_submitted`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
GROUP BY ALL
```
Genie result (snippet):

| approval_rate | reviewed_encounters | appeals_submitted |
|---|---|---|
| 0.3333333333333333 | 3 | 1 |

Expected SQL:
```sql
SELECT MEASURE(`Reviewed Encounters`) AS reviewed, MEASURE(`Approval Rate`) AS approval_rate FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics
```
Expected result (snippet):

| reviewed | approval_rate |
|---|---|
| 3 | 0.3333333333333333 |

Genie text: **33.3%** approval rate: **1** appeal was submitted out of **3** reviewed appeals. This approval rate is based on **3 reviewed encounters** and uses simulated reviewer actions in this demo build, so treat it as directional.

### B13: How many denials are in the backlog by worklist tag?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e7f087f513bc8a65d8ea5cc760bc`

Genie SQL:
```sql
SELECT
  `worklist_tag`,
  MEASURE(`Denials In Worklist`) AS `denials_in_backlog`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
WHERE `worklist_tag` IS NOT NULL
GROUP BY ALL
ORDER BY `denials_in_backlog` DESC
```
Genie result (snippet):

| worklist_tag | denials_in_backlog |
|---|---|
| OPEN | 365 |
| AT_RISK | 75 |
| PAST_DUE | 40 |
| NEW | 20 |

Expected SQL:
```sql
SELECT worklist_tag, MEASURE(`Denials In Worklist`) AS denials FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY denials DESC
```
Expected result (snippet):

| worklist_tag | denials |
|---|---|
| OPEN | 365 |
| AT_RISK | 75 |
| PAST_DUE | 40 |
| NEW | 20 |

Genie text: **500** denials are in the backlog across 4 worklist tags, led by **OPEN** with **365**. By tag: 
- **OPEN:** **365**
- **AT_RISK:** **75**
- **PAST_DUE:** **40**
- **NEW:** **20**

The backlog is concentrated in **OPEN**, which accounts for most denials in the current worklist snapshot.

# Role: General analyst

### B02: Which payer has the most CO50 denials?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e7f01e71101bad9c431396cf7f2b`

Genie SQL:
```sql
WITH `ranked_payers` AS (
  SELECT
    `payer`,
    MEASURE(`Denials In Worklist`) AS `co50_denials`,
    RANK() OVER (ORDER BY MEASURE(`Denials In Worklist`) DESC) AS `payer_rank`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
  WHERE `denial_code` = 'CO50'
    AND `payer` IS NOT NULL
  GROUP BY ALL
)
SELECT
  `payer`,
  `co50_denials`
FROM `ranked_payers`
WHERE `payer_rank` <= 1
ORDER BY `co50_denials` DESC, `payer` ASC;
```
Genie result (snippet):

| payer | co50_denials |
|---|---|
| BCBS of Arizona | 56 |

Expected SQL:
```sql
SELECT payer, MEASURE(`Denials In Worklist`) AS co50_denials FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics WHERE denial_code = 'CO50' GROUP BY ALL ORDER BY co50_denials DESC LIMIT 1
```
Expected result (snippet):

| payer | co50_denials |
|---|---|
| BCBS of Arizona | 56 |

Genie text: **56** CO50 denials — **BCBS of Arizona** has the most CO50 denials in the worklist. In the returned result set, **BCBS of Arizona** is the top payer by CO50 denial volume.

### B03: What is the status of the claim for Elena Marquez?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e7f028ab124c978f8249cf13b0b9`

Genie SQL:
```sql
WITH `w` AS (
  SELECT
    `FACILITY_ID`,
    `PATIENT_CONTROL_NUMBER`,
    `ENCOUNTER_NBR`,
    `patient_name`,
    `payer_name`,
    `denial_code`,
    `deadline_status`,
    `days_remaining`,
    `expected_reimbursement`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`gold_denial_worklist`
  WHERE `patient_name` ILIKE '%Elena Marquez%'
)
SELECT
  `w`.`patient_name`,
  `w`.`payer_name`,
  `w`.`denial_code`,
  `w`.`deadline_status`,
  `w`.`days_remaining`,
  `w`.`expected_reimbursement`,
  COALESCE(`a`.`recommendation`, 'NOT GENERATED') AS `recommendation`
FROM `w`
LEFT JOIN `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_output` `a`
  ON `w`.`FACILITY_ID` = `a`.`FACILITY_ID`
 AND `w`.`PATIENT_CONTROL_NUMBER` = `a`.`PATIENT_CONTROL_NUMBER`
 AND `w`.`ENCOUNTER_NBR` = `a`.`ENCOUNTER_NBR`
```
Genie result (snippet):

| patient_name | payer_name | denial_code | deadline_status | days_remaining | expected_reimbursement | recommendation |
|---|---|---|---|---|---|---|
| Elena Marquez | BCBS of Arizona | CO50 | AT_RISK | 9 | 24850.0 | WARRANTED |

Expected SQL:
```sql
SELECT patient_name, payer_name, denial_code, deadline_status, days_remaining, expected_reimbursement FROM appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist WHERE patient_name = 'Elena Marquez'
```
Expected result (snippet):

| patient_name | payer_name | denial_code | deadline_status | days_remaining | expected_reimbursement |
|---|---|---|---|---|---|
| Elena Marquez | BCBS of Arizona | CO50 | AT_RISK | 9 | 24850.0 |

Genie text: **Elena Marquez** has a claim with **BCBS of Arizona** that is currently **AT_RISK**, with **9 days remaining** to appeal. The denial code is **CO50**, the expected reimbursement is **$24,850.00**, and the AI recommendation is **WARRANTED**.

