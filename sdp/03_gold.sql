-- Lakeflow SDP (SQL) | FE Bar appeals | Gold: the tables the downstream stages consume (SPEC columns + addendum).
-- Dedupe rule: the landing is append-only, so a re-landed or re-generated batch can repeat a natural key.
-- mednecessity_ai_agent and medical_records keep the latest _ingested_at per natural key (latest-wins).

-- Claim-line grain. Legacy column names + the new SPEC fields. Consumed by encounter_grounding (B) and the UC functions.
CREATE OR REFRESH MATERIALIZED VIEW mednecessity_ai_agent (
  PATIENT_NAME STRING COMMENT 'Patient name (synthetic, fictional). PHI: restrict in governance.',
  PATIENT_BIRTHDATE TIMESTAMP COMMENT 'Date of birth (synthetic). PHI.',
  PATIENT_SEX STRING COMMENT 'Sex code F or M (synthetic).',
  PATIENT_CONTROL_NUMBER BIGINT COMMENT 'Patient control number: composite key part 2 (with FACILITY_ID, ENCOUNTER_NBR).',
  FACILITY_ID BIGINT COMMENT 'Facility id: composite key part 1.',
  MEDICAL_RECORD_NUMBER STRING COMMENT 'Medical record number (synthetic). PHI.',
  STATEMENT_COVERS_PERIOD STRING COMMENT 'Statement period as text: DOS - end date.',
  TOTAL_CHARGES DOUBLE COMMENT 'Claim-level total billed charges, repeated on every line of the claim. Use max() per encounter, not sum().',
  SITEID BIGINT COMMENT 'Site id of the facility.',
  CLAIM_NUMBER BIGINT COMMENT 'Claim number (synthetic).',
  PAYER_NAME STRING COMMENT 'Payer name (synthetic routing labels). BCBS names route to BCBS criteria, others to CMS criteria.',
  PAYER_ADDRESS_STREET STRING COMMENT 'Payer address street (generic).',
  PAYER_CSZ STRING COMMENT 'Payer city, state, zip (generic).',
  TYPE_OF_BILL STRING COMMENT 'UB-04 type of bill (0111 inpatient, 0131 outpatient). Null for professional lines.',
  HEALTH_PLAN_ID STRING COMMENT 'Payer plan identifier (synthetic).',
  FEDERAL_TAX_ID BIGINT COMMENT 'Facility federal tax id (synthetic).',
  PROVIDER_NAME STRING COMMENT 'Rendering facility name (synthetic).',
  BILL_DATE TIMESTAMP COMMENT 'Claim bill date (timestamp).',
  DENIAL_ID STRING COMMENT 'Denial reference id (synthetic).',
  DENIAL_CODE STRING COMMENT 'X12 CARC denial code. In scope: CO50, CO55, CO57, CO150, CO186.',
  PATIENTIDENTITYCODE STRING COMMENT 'Patient relationship code (18 = self).',
  CLAIMPOLICYNUMBER STRING COMMENT 'Member id (synthetic). PHI.',
  DATE_PAID TIMESTAMP COMMENT 'Adjudication date for the denial (timestamp). Synthetic: equals the denial date.',
  HCPCS_CODE STRING COMMENT 'CPT or HCPCS procedure code for this line.',
  MOD1 STRING COMMENT 'First modifier on the line (e.g. RT, LT). Null when none.',
  POS DOUBLE COMMENT 'Place of service code (21 inpatient, 22 outpatient hospital, 23 ED, 11 office).',
  REV_CODE BIGINT COMMENT 'Revenue code for the line (e.g. 360 surgery, 120 room and board). Null for professional lines.',
  DOS TIMESTAMP COMMENT 'Date of service (timestamp). Must be before DENIAL_DATE (enforced in silver).',
  LINE_ITEM_CONTROL_NUMBER BIGINT COMMENT 'Claim line id: part of the natural key with the composite key (latest-wins dedupe).',
  ADMIT_DIAG STRING COMMENT 'ICD-10-CM admitting or primary diagnosis.',
  DISCH_DIAG1 STRING COMMENT 'ICD-10-CM diagnosis 1 (primary, same as ADMIT_DIAG in this build).',
  DISCH_DIAG2 STRING COMMENT 'ICD-10-CM diagnosis 2.',
  DISCH_DIAG3 STRING COMMENT 'ICD-10-CM diagnosis 3.',
  DISCH_DIAG4 STRING COMMENT 'ICD-10-CM diagnosis 4.',
  DISCH_DIAG5 STRING COMMENT 'ICD-10-CM diagnosis 5.',
  DISCH_DIAG6 STRING COMMENT 'ICD-10-CM diagnosis 6.',
  ENCOUNTER_NBR BIGINT COMMENT 'Encounter number: composite key part 3.',
  DENIAL_DATE DATE COMMENT 'Denial (adjudication) date. The appeal clock starts here.',
  PAYER_TYPE STRING COMMENT 'COMMERCIAL, MEDICARE_ADVANTAGE or MEDICAID. Drives the appeal window.',
  APPEAL_LIMIT_DAYS INT COMMENT 'Appeal window in days from DENIAL_DATE. ASSUMPTION: 180 commercial, 65 Medicare Advantage, 60 Medicaid (state-specific, to verify).',
  EXPECTED_REIMBURSEMENT DOUBLE COMMENT 'Expected contracted or allowed dollars for this line (synthetic). Well below charges. Not the billed charge.',
  SOURCE_BATCH STRING COMMENT 'Generator batch name: batch_<as_of>_seed<seed>_n<n>.'
)
COMMENT 'Claim-line grain for denied medical-necessity claims (FE Bar). Legacy mednecessity_ai_agent column names plus DENIAL_DATE, PAYER_TYPE, APPEAL_LIMIT_DAYS, EXPECTED_REIMBURSEMENT, SOURCE_BATCH. Latest version per (FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR, LINE_ITEM_CONTROL_NUMBER). Synthetic data.'
AS SELECT
  PATIENT_NAME, PATIENT_BIRTHDATE, PATIENT_SEX, PATIENT_CONTROL_NUMBER, FACILITY_ID, MEDICAL_RECORD_NUMBER,
  STATEMENT_COVERS_PERIOD, TOTAL_CHARGES, SITEID, CLAIM_NUMBER, PAYER_NAME, PAYER_ADDRESS_STREET, PAYER_CSZ,
  TYPE_OF_BILL, HEALTH_PLAN_ID, FEDERAL_TAX_ID, PROVIDER_NAME, BILL_DATE, DENIAL_ID, DENIAL_CODE,
  PATIENTIDENTITYCODE, CLAIMPOLICYNUMBER, DATE_PAID, HCPCS_CODE, MOD1, POS, REV_CODE, DOS,
  LINE_ITEM_CONTROL_NUMBER, ADMIT_DIAG, DISCH_DIAG1, DISCH_DIAG2, DISCH_DIAG3, DISCH_DIAG4, DISCH_DIAG5,
  DISCH_DIAG6, ENCOUNTER_NBR, DENIAL_DATE, PAYER_TYPE, APPEAL_LIMIT_DAYS, EXPECTED_REIMBURSEMENT, SOURCE_BATCH
FROM silver_claim_lines
QUALIFY row_number() OVER (
  PARTITION BY FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR, LINE_ITEM_CONTROL_NUMBER
  ORDER BY _ingested_at DESC, SOURCE_BATCH DESC) = 1;

-- Note grain. Composite key + PATIENT_NAME + event fields (SPEC).
CREATE OR REFRESH MATERIALIZED VIEW medical_records (
  FACILITY_ID BIGINT COMMENT 'Facility id: composite key part 1.',
  PATIENT_CONTROL_NUMBER BIGINT COMMENT 'Patient control number: composite key part 2.',
  ENCOUNTER_NBR BIGINT COMMENT 'Encounter number: composite key part 3.',
  PATIENT_NAME STRING COMMENT 'Patient name (synthetic). PHI.',
  event_id BIGINT COMMENT 'Clinical event id, unique within the encounter.',
  event_tag STRING COMMENT 'Note type tag, e.g. PT_DISCHARGE, IMAGING_XRAY, ORTHO_CONSULT.',
  note_date DATE COMMENT 'Date of the clinical note (date).',
  author_role STRING COMMENT 'Author role (e.g. ORTHOPEDIC_SURGEON, PHYSICAL_THERAPIST). Not a person.',
  plain_text STRING COMMENT 'Clinical narrative (synthetic). Grounding input for the appeal.'
)
COMMENT 'Clinical-note grain for FE Bar denied encounters (synthetic). plain_text is the chart narrative. Latest version per (FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR, event_id).'
AS SELECT
  FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR, PATIENT_NAME,
  event_id, event_tag, note_date, author_role, plain_text
FROM silver_clinical_notes
QUALIFY row_number() OVER (
  PARTITION BY FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR, event_id
  ORDER BY _ingested_at DESC) = 1;

-- One row per denied encounter: the worklist. Formulas per SPEC.
--   days_remaining   = datediff(appeal_deadline, current_date())
--   deadline_status  = PAST_DUE (<0 days) | AT_RISK (<=14 days) | OK
--   priority_score   = expected_reimbursement x (0 if PAST_DUE, 2.0 if AT_RISK, 1.5 if <=30 days, else 1.0)
--   priority_rank    = row_number by priority_score desc
--   worklist_tag     = PAST_DUE > NEW (denial_date >= as_of - 1 day, "denied yesterday") > AT_RISK > OPEN
CREATE OR REFRESH MATERIALIZED VIEW gold_denial_worklist (
  FACILITY_ID BIGINT COMMENT 'Facility id: composite key part 1 (worklist primary key with the next two).',
  PATIENT_CONTROL_NUMBER BIGINT COMMENT 'Patient control number: composite key part 2.',
  ENCOUNTER_NBR BIGINT COMMENT 'Encounter number: composite key part 3.',
  patient_name STRING COMMENT 'Patient name (synthetic). PHI.',
  payer_name STRING COMMENT 'Payer name.',
  payer_type STRING COMMENT 'COMMERCIAL, MEDICARE_ADVANTAGE or MEDICAID.',
  denial_code STRING COMMENT 'X12 CARC denial code (one per encounter).',
  hcpcs_codes STRING COMMENT 'Distinct CPT/HCPCS codes on the encounter, sorted, comma-separated.',
  dos DATE COMMENT 'Earliest date of service (date).',
  denial_date DATE COMMENT 'Denial date (date).',
  appeal_limit_days INT COMMENT 'Appeal window in days (ASSUMPTION, see APPEAL_LIMIT_DAYS).',
  appeal_deadline DATE COMMENT 'denial_date + appeal_limit_days.',
  days_remaining INT COMMENT 'appeal_deadline minus current_date() at refresh. Negative = past due.',
  deadline_status STRING COMMENT 'PAST_DUE (<0 days), AT_RISK (0-14 days), OK.',
  total_charges DOUBLE COMMENT 'Encounter total billed charges (max of claim-level TOTAL_CHARGES). Not the expected payment.',
  expected_reimbursement DOUBLE COMMENT 'Sum of line-level EXPECTED_REIMBURSEMENT for the encounter, negative (invalid, warned) lines floored at 0 (synthetic).',
  priority_score DOUBLE COMMENT 'expected_reimbursement x weight: 0 if PAST_DUE, 2.0 if AT_RISK, 1.5 if <=30 days, else 1.0.',
  priority_rank INT COMMENT '1 = highest priority_score (ties broken by keys). Deterministic.',
  worklist_tag STRING COMMENT 'Trigger tag, precedence PAST_DUE > NEW (denied yesterday or today) > AT_RISK > OPEN.'
)
COMMENT 'One row per denied encounter (FE Bar worklist): payer, denial, codes, dates, appeal deadline and status, dollars, deterministic priority rank and worklist trigger tag. Synthetic data. Deadline fields are relative to current_date() at refresh time.'
AS
WITH enc AS (
  SELECT
    FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR,
    max(PATIENT_NAME) AS patient_name,
    max(PAYER_NAME) AS payer_name,
    max(PAYER_TYPE) AS payer_type,
    max(DENIAL_CODE) AS denial_code,
    concat_ws(', ', array_sort(array_distinct(collect_list(HCPCS_CODE)))) AS hcpcs_codes,
    CAST(min(DOS) AS DATE) AS dos,
    max(DENIAL_DATE) AS denial_date,
    max(APPEAL_LIMIT_DAYS) AS appeal_limit_days,
    max(TOTAL_CHARGES) AS total_charges,
    -- Lines that fail the silver warn-expectation (EXPECTED_REIMBURSEMENT >= 0) stay visible in silver and the
    -- event log, but an invalid negative amount contributes $0 to appealable value (decision 2026-11-25).
    sum(greatest(EXPECTED_REIMBURSEMENT, 0)) AS expected_reimbursement
  FROM mednecessity_ai_agent
  GROUP BY FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR
),
dl AS (
  SELECT *, CAST(date_add(denial_date, appeal_limit_days) AS DATE) AS appeal_deadline FROM enc
),
st AS (
  SELECT *, CAST(datediff(appeal_deadline, current_date()) AS INT) AS days_remaining FROM dl
),
ds AS (
  SELECT *,
    CASE WHEN days_remaining < 0 THEN 'PAST_DUE'
         WHEN days_remaining <= 14 THEN 'AT_RISK'
         ELSE 'OK' END AS deadline_status
  FROM st
),
pr AS (
  SELECT *,
    CAST(expected_reimbursement * CASE WHEN deadline_status = 'PAST_DUE' THEN 0.0
                                       WHEN deadline_status = 'AT_RISK' THEN 2.0
                                       WHEN days_remaining <= 30 THEN 1.5
                                       ELSE 1.0 END AS DOUBLE) AS priority_score,
    CASE WHEN deadline_status = 'PAST_DUE' THEN 'PAST_DUE'
         WHEN denial_date >= date_sub(current_date(), 1) THEN 'NEW'
         WHEN deadline_status = 'AT_RISK' THEN 'AT_RISK'
         ELSE 'OPEN' END AS worklist_tag
  FROM ds
)
SELECT
  FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR,
  patient_name, payer_name, payer_type, denial_code, hcpcs_codes,
  dos, denial_date, appeal_limit_days, appeal_deadline, days_remaining, deadline_status,
  total_charges, expected_reimbursement, priority_score,
  CAST(row_number() OVER (ORDER BY priority_score DESC, FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR) AS INT) AS priority_rank,
  worklist_tag
FROM pr;
