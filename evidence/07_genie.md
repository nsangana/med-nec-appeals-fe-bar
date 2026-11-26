# 07 Genie benchmarks (FE Bar – Medical Necessity Appeals)

- Space: `01f1e7ec913217158b231c3e2f18fa20` (default workspace permissions; not shared)
- Run at: 2026-11-26 06:49 UTC (Genie Conversation API via CLI profile `fevm-appeals-hackathon`)
- appeals_output rows at run: 180
- Pass rate: **14/14** graded; PENDING_DATA: 0 (need generated appeals)
- Grading: Genie query COMPLETED with SQL; expected SQL (run on the same warehouse) values all present in Genie's result rows; empty expected => empty Genie result.
- Expected SQL is in `genie/benchmarks.json`. Results are real (not simulated).
- History: earlier runs are in git history.

| ID | Question | Result | Genie SQL (first 200 chars) | Note |
|---|---|---|---|---|
| B01 | How much appealable revenue is at deadline risk this week by payer? | PASS | `SELECT   `payer`,   MEASURE(`Revenue At Deadline Risk`) AS `at_risk_revenue` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` WHERE `payer` IS NOT NULL GROUP BY ALL ORDER BY `at_ris` | all expected values present |
| B02 | Which payer has the most CO50 denials? | PASS | `WITH `ranked_payers` AS (   SELECT     `payer`,     MEASURE(`Denials In Worklist`) AS `co50_denials`,     RANK() OVER (ORDER BY MEASURE(`Denials In Worklist`) DESC) AS `denial_rank`   FROM `appeals_ha` | all expected values present |
| B03 | What is the status of the claim for Elena Marquez? | PASS | `WITH `w` AS (   SELECT     `FACILITY_ID`,     `PATIENT_CONTROL_NUMBER`,     `ENCOUNTER_NBR`,     `patient_name`,     `payer_name`,     `denial_code`,     `deadline_status`,     `days_remaining`,     `` | all expected values present |
| B04 | What share of appeals were routed to NEEDS REVIEW, and why? | PASS | `WITH `share` AS (   SELECT     MEASURE(`NEEDS REVIEW Rate`) * 100 AS `needs_review_share_pct`,     MEASURE(`Appeals Generated`) AS `appeals_generated`   FROM `appeals_hackathon_catalog`.`fe_bar_appeal` | all expected values present |
| B05 | What is the warranted rate by payer type? | PASS | `SELECT   `payer_type`,   MEASURE(`Warranted Rate`) AS `warranted_rate` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` WHERE `payer_type` IS NOT NULL GROUP BY ALL ORDER BY `payer_t` | all expected values present |
| B06 | How many denials were logged as NEW (denied yesterday)? | PASS | `SELECT COUNT(*) AS `new_denials_logged` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`gold_denial_worklist` WHERE `worklist_tag` IS NOT NULL   AND `worklist_tag` ILIKE '%NEW%'   AND `denial_date`` | all expected values present |
| B07 | What is the cost per appeal? | PASS | `SELECT MEASURE(`Cost Per Appeal (ESTIMATE)`) AS `cost_per_appeal_estimate_usd` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` GROUP BY ALL` | all expected values present |
| B08 | How much expected reimbursement was lost to missed appeal deadlines by payer? | PASS | `SELECT   `payer`,   MEASURE(`Revenue Lost To Deadline`) AS `revenue_lost_to_deadline` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` WHERE `payer` IS NOT NULL GROUP BY ALL ORDER B` | all expected values present |
| B09 | Which 5 encounters have the highest priority score and are still appealable? | PASS | `WITH `ranked_encounters` AS (   SELECT     `FACILITY_ID`,     `PATIENT_CONTROL_NUMBER`,     `ENCOUNTER_NBR`,     `payer_name`,     `denial_code`,     `dos`,     `appeal_deadline`,     `days_remaining`` | all expected values present |
| B10 | How does expected reimbursement compare with total charges by denial code? | PASS | `WITH `m` AS (   SELECT     `denial_code`,     MEASURE(`Expected Reimbursement (All Encounters)`) AS `expected_reimbursement_all_encounters`   FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals` | all expected values present |
| B11 | What share of reviewed appeals were approved, meaning submitted? | PASS | `SELECT MEASURE(`Approval Rate`) AS `approval_rate`, MEASURE(`Reviewed Encounters`) AS `reviewed_encounters` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` GROUP BY ALL` | all expected values present |
| B12 | What is the illustrative recoverable revenue by payer? | PASS | `SELECT   `payer`,   MEASURE(`Illustrative Recoverable Revenue (Prototype)`) AS `illustrative_recoverable_revenue` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` WHERE `payer` IS N` | all expected values present |
| B13 | How many denials are in the backlog by worklist tag? | PASS | `SELECT   `worklist_tag`,   MEASURE(`Denials In Worklist`) AS `denials_in_backlog` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` WHERE `worklist_tag` IS NOT NULL GROUP BY ALL ORDE` | all expected values present |
| B14 | What is the AI accuracy and unsafe rate of the latest evaluation run? | PASS | `SELECT `run_id`, `run_ts`, `accuracy`, `unsafe_rate` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`eval_summary` WHERE `run_ts` IS NOT NULL ORDER BY `run_ts` DESC LIMIT 1` | all expected values present |


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
- Genie status: COMPLETED, conversation `01f1e964f79018348c013b0917e4cf8f`

Genie SQL:
```sql
SELECT
  `payer`,
  MEASURE(`Revenue At Deadline Risk`) AS `at_risk_revenue`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
WHERE `payer` IS NOT NULL
GROUP BY ALL
ORDER BY `at_risk_revenue` DESC
```
Genie result (snippet):

| payer | at_risk_revenue |
|---|---|
| BCBS of Arizona | 111669.45 |
| BCBS of Arizona Medicare Advantage | 89791.84 |
| AHCCCS Medicaid | 66852.36 |
| Aetna | 53794.27 |
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
| BCBS of Arizona | 111669.45 |
| BCBS of Arizona Medicare Advantage | 89791.84 |
| AHCCCS Medicaid | 66852.36 |
| Aetna | 53794.27 |
| Humana Medicare Advantage | 39356.15 |
| UnitedHealthcare | 32791.56 |
| ... 2 more rows |

Genie text: **$111,669.45** is at deadline risk for **BCBS of Arizona**, the highest payer in the current worklist snapshot. Examples include:
- **BCBS of Arizona** — **$111,669.45**
- **BCBS of Arizona Medicare Advantage** — **$89,791.84**
- **AHCCCS Medicaid** — **$66,852.36**
- **Aetna** — **$53,794.27**
- *

## B05: What is the warranted rate by payer type?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e9651d5914c095d52b72f0754b3a`

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
| COMMERCIAL | 0.3898305084745763 |
| MEDICAID | 0.5 |
| MEDICARE_ADVANTAGE | 0.38095238095238093 |

Expected SQL:
```sql
SELECT payer_type, MEASURE(`Warranted Rate`) AS warranted_rate FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY ALL
```
Expected result (snippet):

| payer_type | warranted_rate |
|---|---|
| COMMERCIAL | 0.3898305084745763 |
| MEDICAID | 0.5 |
| MEDICARE_ADVANTAGE | 0.38095238095238093 |

Genie text: Would you prefer to see these rates broken down by payer name instead of payer type?

## B08: How much expected reimbursement was lost to missed appeal deadlines by payer?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e965365e1c2b8fe88a95b86d340c`

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
| BCBS of Arizona | 74865.43000000001 |
| UnitedHealthcare | 53515.37 |
| BCBS of Arizona Medicare Advantage | 37912.170000000006 |
| AHCCCS Medicaid | 29892.489999999998 |
| UnitedHealthcare Medicare Advantage | 20196.120000000003 |
| Cigna | 14854.599999999999 |
| ... 2 more rows |

Expected SQL:
```sql
SELECT payer, MEASURE(`Revenue Lost To Deadline`) AS lost_revenue FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY lost_revenue DESC
```
Expected result (snippet):

| payer | lost_revenue |
|---|---|
| BCBS of Arizona | 74865.43000000001 |
| UnitedHealthcare | 53515.37 |
| BCBS of Arizona Medicare Advantage | 37912.170000000006 |
| AHCCCS Medicaid | 29892.489999999998 |
| UnitedHealthcare Medicare Advantage | 20196.120000000003 |
| Cigna | 14854.599999999999 |
| ... 2 more rows |

Genie text: **$74,865.43** was lost to missed appeal deadlines for **BCBS of Arizona**, the highest among the 8 payers shown. Examples include:
- **BCBS of Arizona** — **$74,865.43**
- **UnitedHealthcare** — **$53,515.37**
- **BCBS of Arizona Medicare Advantage** — **$37,912.17**
- **AHCCCS Medicaid** — **$29,8

## B09: Which 5 encounters have the highest priority score and are still appealable?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e965407a13518ef6daffe16ec75c`

Genie SQL:
```sql
WITH `ranked_encounters` AS (
  SELECT
    `FACILITY_ID`,
    `PATIENT_CONTROL_NUMBER`,
    `ENCOUNTER_NBR`,
    `payer_name`,
    `denial_code`,
    `dos`,
    `appeal_deadline`,
    `days_remaining`,
    `deadline_status`,
    `expected_reimbursement`,
    `priority_score`,
    `priority_rank`,
    RANK() OVER (ORDER BY `priority_score` DESC, `priority_rank` ASC) AS `encounter_rank`
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
  `denial_code`,
  `dos`,
  `appeal_deadline`,
  `days_remaining`,
  `deadline_status`,
  `expected_reimbursement`,
  `priority_score`,
  `priority_rank`
FROM `ranked_encounters`
WHERE `encounter_rank` <= 5
ORDER BY `priority_score` DESC, `priority_rank` ASC
```
Genie result (snippet):

| FACILITY_ID | PATIENT_CONTROL_NUMBER | ENCOUNTER_NBR | payer_name | denial_code | dos | appeal_deadline | days_remaining | deadline_status | expected_reimbursement | priority_score | priority_rank |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 101 | 770000001 | 50000001 | BCBS of Arizona | CO50 | 2026-05-15 | 2026-12-04 | 8 | AT_RISK | 24850.0 | 49700.0 | 1 |
| 102 | 770000203 | 50000203 | Aetna | CO50 | 2026-05-14 | 2026-11-27 | 1 | AT_RISK | 20096.92 | 40193.84 | 2 |
| 101 | 770000394 | 50000394 | BCBS of Arizona Medicare Advantage | CO50 | 2026-08-27 | 2026-11-26 | 0 | AT_RISK | 18585.01 | 37170.02 | 3 |
| 101 | 770000231 | 50000231 | Humana Medicare Advantage | CO50 | 2026-09-05 | 2026-12-06 | 10 | AT_RISK | 18438.19 | 36876.38 | 4 |
| 102 | 770000233 | 50000233 | Aetna | CO50 | 2026-05-20 | 2026-11-30 | 4 | AT_RISK | 17437.31 | 34874.62 | 5 |

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

Genie text: **5** still-appealable encounters have the highest priority scores, and all **5** are currently **AT_RISK**.
- **Priority rank 1**: Encounter **50000001** at **BCBS of Arizona** — priority score **49,700.0**, expected reimbursement **$24,850.00**, **8** days remaining
- **Priority rank 2**: Encounte

# Role: CDAIO

## B04: What share of appeals were routed to NEEDS REVIEW, and why?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e9651319186ea29cbd6bd6dab159`

Genie SQL:
```sql
WITH `share` AS (
  SELECT
    MEASURE(`NEEDS REVIEW Rate`) * 100 AS `needs_review_share_pct`,
    MEASURE(`Appeals Generated`) AS `appeals_generated`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
  GROUP BY ALL
),
`reasons` AS (
  SELECT
    COALESCE(`needs_review_reason`, 'NO REASON RECORDED') AS `needs_review_reason`,
    COUNT(*) AS `appeals`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_output`
  WHERE `recommendation` ILIKE '%NEEDS REVIEW%'
    AND `needs_review_reason` IS NOT NULL
  GROUP BY ALL
)
SELECT
  `r`.`needs_review_reason`,
  `r`.`appeals`,
  `s`.`needs_review_share_pct`,
  `s`.`appeals_generated`
FROM `reasons` `r`
CROSS JOIN `share` `s`
ORDER BY `appeals` DESC
```
Genie result (snippet):

| needs_review_reason | appeals | needs_review_share_pct | appeals_generated |
|---|---|---|---|
| below.  ---  **Coding/MPFS context** - CPT 99223: MPFS status "A" (Active, separately payable). Global period XXX (no gl | 1 | 23.333333333333332 | 180 |
| - **Conflicting status orders:** Both an observation order and an inpatient order are dated for the same encounter [2026 | 1 | 23.333333333333332 | 180 |
| - **Psychological clearance letter absent from chart:** [2026-05-23 BARIATRIC_CONSULT] explicitly documents that the psy | 1 | 23.333333333333332 | 180 |
| - **FDA device regulatory status is undocumented:** The consent form in [2026-05-27 PAIN_MGMT] explicitly notes "Device  | 1 | 23.333333333333332 | 180 |
| - **Physical therapy records not in chart**: Outside PT records were requested but never received as of [2026-03-01 PT_E | 1 | 23.333333333333332 | 180 |
| - **Repeat troponin result is absent from the chart**: [2026-07-07 ED_NOTE] documents that a repeat Troponin I was order | 1 | 23.333333333333332 | 180 |
| ... 36 more rows |

Expected SQL:
```sql
SELECT COALESCE(needs_review_reason, 'NO REASON RECORDED') AS needs_review_reason, COUNT(*) AS appeals FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_output WHERE recommendation = 'NEEDS REVIEW' GROUP BY ALL ORDER BY appeals DESC
```
Expected result (snippet):

| needs_review_reason | appeals |
|---|---|
| - **FDA device regulatory status is undocumented**: The consent form from [2026-10-05 PAIN_MGMT] explicitly notes that " | 1 |
| - **Date-of-service conflict (critical):** The claim bills CPT 63650 with a DOS of 2026-10-31, but the only clinical not | 1 |
| - **Missing: Repeat troponin result** — The [2026-06-07 ED_NOTE] documents that a repeat Troponin I was ordered but the  | 1 |
| - **Missing operative/procedure note for DOS 2026-06-17:** No clinical documentation (operative report, procedure note,  | 1 |
| - **Device FDA regulatory status not documented:** The [2026-04-14 PAIN_MGMT] note explicitly states "Device FDA status  | 1 |
| - **Repeat troponin result missing**: [2026-10-02 ED_NOTE] documents that a serial troponin I was ordered but the result | 1 |
| ... 36 more rows |

Genie text: **23.3%** of appeals generated were routed to **NEEDS REVIEW** (**180** appeals generated in total). Examples of reasons include:
- **Missing clinical results or records**, such as a repeat troponin result, telemetry strip, EKG findings, or operative note
- **Conflicting or incomplete admission/stat

## B07: What is the cost per appeal?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e9652efc1db8995ad4644f939a54`

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

Genie text: **$0.1070 per appeal** is the reported **Cost Per Appeal (ESTIMATE)**. This is an **estimate**, not a measured cost.

## B14: What is the AI accuracy and unsafe rate of the latest evaluation run?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e965731316d4b7cc73918739d44a`

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
| f7047f94-b5ad-4213-a44c-d350cc777b7c | 2026-11-26T03:09:43.482Z | 0.9722 | 0.0 |

Expected SQL:
```sql
SELECT accuracy, unsafe_rate FROM appeals_hackathon_catalog.fe_bar_appeals.eval_summary ORDER BY run_ts DESC LIMIT 1
```
Expected result (snippet):

| accuracy | unsafe_rate |
|---|---|
| 0.9722 | 0.0 |

Genie text: **97.22%** accuracy, latest evaluation run **f7047f94-b5ad-4213-a44c-d350cc777b7c** had an unsafe rate of **0.0%** at **2026-11-26T03:09:43.482Z**. These evaluation labels are **synthetic**, and in the latest run the model showed high accuracy with no unsafe predictions recorded.

# Role: CFO

## B10: How does expected reimbursement compare with total charges by denial code?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e9654d371e1ebdfccb23c0979131`

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
`c` AS (
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
  `c`.`total_charges`,
  try_divide(`m`.`expected_reimbursement_all_encounters`,`c`.`total_charges`) AS `expected_reimbursement_to_charges_ratio`
FROM `m`
INNER JOIN `c`
  ON `m`.`denial_code` = `c`.`denial_code`
ORDER BY `m`.`expected_reimbursement_all_encounters` DESC
```
Genie result (snippet):

| denial_code | expected_reimbursement_all_encounters | total_charges | expected_reimbursement_to_charges_ratio |
|---|---|---|---|
| CO50 | 1812376.7100000002 | 4357307.860000003 | 0.41593955906526164 |
| CO186 | 533021.5499999999 | 1322495.0199999998 | 0.40304238725980235 |
| CO55 | 364172.6 | 889544.7200000002 | 0.40939212139891057 |
| CO57 | 139829.85 | 328857.33 | 0.42519912814471855 |
| CO150 | 21205.2 | 50534.01999999999 | 0.4196222663465128 |

Expected SQL:
```sql
SELECT denial_code, SUM(expected_reimbursement) AS expected_reimbursement, SUM(total_charges) AS total_charges FROM appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist GROUP BY denial_code ORDER BY denial_code
```
Expected result (snippet):

| denial_code | expected_reimbursement | total_charges |
|---|---|---|
| CO150 | 21205.2 | 50534.01999999999 |
| CO186 | 533021.5499999999 | 1322495.0199999998 |
| CO50 | 1812376.7100000002 | 4357307.860000003 |
| CO55 | 364172.6 | 889544.7200000002 |
| CO57 | 139829.85 | 328857.33 |

Genie text: Expected reimbursement is lower than total charges for **all 5 denial codes shown**, ranging from about **40.3% to 42.5%** of charges. Examples include:
- **CO50**: **$1.81M** expected reimbursement vs **$4.36M** in charges (**41.6%**)
- **CO186**: **$533.0K** vs **$1.32M** (**40.3%**)
- **CO55**: *

## B12: What is the illustrative recoverable revenue by payer?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e96561821528bef99fbfa7b8d3dd`

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
| BCBS of Arizona | 301102.04000000004 |
| BCBS of Arizona Medicare Advantage | 138539.27999999997 |
| AHCCCS Medicaid | 123603.04999999999 |
| Aetna | 117484.73 |
| UnitedHealthcare | 87881.82999999999 |
| Cigna | 60157.240000000005 |
| ... 2 more rows |

Expected SQL:
```sql
SELECT payer, MEASURE(`Illustrative Recoverable Revenue (Prototype)`) AS illustrative_recoverable FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY illustrative_recoverable DESC
```
Expected result (snippet):

| payer | illustrative_recoverable |
|---|---|
| BCBS of Arizona | 301102.04000000004 |
| BCBS of Arizona Medicare Advantage | 138539.27999999997 |
| AHCCCS Medicaid | 123603.04999999999 |
| Aetna | 117484.73 |
| UnitedHealthcare | 87881.82999999999 |
| Cigna | 60157.240000000005 |
| ... 2 more rows |

Genie text: **Illustrative recoverable revenue (prototype, synthetic data)** is highest for **BCBS of Arizona** at **$301,102.04**. Examples include:
- **BCBS of Arizona** — **$301,102.04**
- **BCBS of Arizona Medicare Advantage** — **$138,539.28**
- **AHCCCS Medicaid** — **$123,603.05**
- **Aetna** — **$117,48

# Role: Director of Denial Management

## B06: How many denials were logged as NEW (denied yesterday)?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e96524e61201891a1ae61e4f45e0`

Genie SQL:
```sql
SELECT COUNT(*) AS `new_denials_logged`
FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`gold_denial_worklist`
WHERE `worklist_tag` IS NOT NULL
  AND `worklist_tag` ILIKE '%NEW%'
  AND `denial_date` = date_sub(current_date(), 1)
```
Genie result (snippet):

| new_denials_logged |
|---|
| 0 |

Expected SQL:
```sql
SELECT MEASURE(`Denials In Worklist`) AS new_denials FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics WHERE worklist_tag = 'NEW'
```
Expected result (snippet):

| new_denials |
|---|
| 0 |

Genie text: **0** denials were logged as **NEW** with a denial date of **yesterday**. In this result, the count of `new_denials_logged` is **0**, so there were no newly denied encounters added for yesterday under the SQL filter used.

## B11: What share of reviewed appeals were approved, meaning submitted?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e965572818b8b4f0016e2a2ad664`

Genie SQL:
```sql
SELECT MEASURE(`Approval Rate`) AS `approval_rate`, MEASURE(`Reviewed Encounters`) AS `reviewed_encounters` FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics` GROUP BY ALL
```
Genie result (snippet):

| approval_rate | reviewed_encounters |
|---|---|
| 0.3333333333333333 | 3 |

Expected SQL:
```sql
SELECT MEASURE(`Reviewed Encounters`) AS reviewed, MEASURE(`Approval Rate`) AS approval_rate FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics
```
Expected result (snippet):

| reviewed | approval_rate |
|---|---|
| 3 | 0.3333333333333333 |

Genie text: **33.3%** of reviewed appeals were approved, meaning submitted. That approval rate is based on **3 reviewed encounters**, and the reviewer actions in this build are **simulated demo data** on a small sample.

## B13: How many denials are in the backlog by worklist tag?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e9656bcc10cabf7b01fdc2efd324`

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
| OPEN | 383 |
| AT_RISK | 67 |
| PAST_DUE | 50 |

Expected SQL:
```sql
SELECT worklist_tag, MEASURE(`Denials In Worklist`) AS denials FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY denials DESC
```
Expected result (snippet):

| worklist_tag | denials |
|---|---|
| OPEN | 383 |
| AT_RISK | 67 |
| PAST_DUE | 50 |

Genie text: **500** denials are in the backlog across 3 worklist tags: **OPEN** has **383**, **AT_RISK** has **67**, and **PAST_DUE** has **50**. **OPEN** is the clear majority, representing more than seven times the **PAST_DUE** backlog.

# Role: General analyst

## B02: Which payer has the most CO50 denials?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e96501c31cd8bec7981c3f971cf1`

Genie SQL:
```sql
WITH `ranked_payers` AS (
  SELECT
    `payer`,
    MEASURE(`Denials In Worklist`) AS `co50_denials`,
    RANK() OVER (ORDER BY MEASURE(`Denials In Worklist`) DESC) AS `denial_rank`
  FROM `appeals_hackathon_catalog`.`fe_bar_appeals`.`appeals_metrics`
  WHERE `payer` IS NOT NULL
    AND `denial_code` = 'CO50'
  GROUP BY ALL
)
SELECT
  `payer`,
  `co50_denials`
FROM `ranked_payers`
WHERE `denial_rank` <= 1
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

Genie text: **56** CO50 denials are tied for the highest count under **BCBS of Arizona**. In the returned top-ranked result, **BCBS of Arizona** is the payer with **56** CO50 denials.

## B03: What is the status of the claim for Elena Marquez?
- Result: **PASS** (all expected values present)
- Genie status: COMPLETED, conversation `01f1e9650bd91763a4f1e58e456c070f`

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
| Elena Marquez | BCBS of Arizona | CO50 | AT_RISK | 8 | 24850.0 | WARRANTED |

Expected SQL:
```sql
SELECT patient_name, payer_name, denial_code, deadline_status, days_remaining, expected_reimbursement FROM appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist WHERE patient_name = 'Elena Marquez'
```
Expected result (snippet):

| patient_name | payer_name | denial_code | deadline_status | days_remaining | expected_reimbursement |
|---|---|---|---|---|---|
| Elena Marquez | BCBS of Arizona | CO50 | AT_RISK | 8 | 24850.0 |

Genie text: **8 days remaining** for Elena Marquez with **BCBS of Arizona**; the claim is **AT_RISK** with denial code **CO50**, expected reimbursement **$24,850.00**, and AI recommendation **WARRANTED**. This is a single claim result, and the **WARRANTED** recommendation is AI output rather than a final determ

