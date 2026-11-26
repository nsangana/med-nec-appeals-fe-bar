-- Lakeflow SDP (SQL) | FE Bar appeals | Bronze: Auto Loader over the generator's landing volume.
-- Files are JSON lines written by pipeline/10_generate_raw_data.py. schemaHints pin every column type so a
-- batch with nulls cannot change the inferred schema. _ingested_at and _source_file are added for lineage and
-- for the latest-wins dedupe in the gold MVs (see 03_gold.sql).

CREATE OR REFRESH STREAMING TABLE bronze_claims
COMMENT 'Bronze: raw claim-line JSON landed by the synthetic generator (Auto Loader, one row per claim line as landed, including any injected defect rows). Append-only.'
AS SELECT *,
  current_timestamp() AS _ingested_at,
  _metadata.file_path AS _source_file
FROM STREAM read_files(
  '/Volumes/appeals_hackathon_catalog/fe_bar_appeals/landing/claims/',
  format => 'json',
  schemaHints => 'PATIENT_NAME STRING, PATIENT_BIRTHDATE STRING, PATIENT_SEX STRING, PATIENT_CONTROL_NUMBER BIGINT, FACILITY_ID BIGINT, MEDICAL_RECORD_NUMBER STRING, STATEMENT_COVERS_PERIOD STRING, TOTAL_CHARGES DOUBLE, SITEID BIGINT, CLAIM_NUMBER BIGINT, PAYER_NAME STRING, PAYER_ADDRESS_STREET STRING, PAYER_CSZ STRING, TYPE_OF_BILL STRING, HEALTH_PLAN_ID STRING, FEDERAL_TAX_ID BIGINT, PROVIDER_NAME STRING, BILL_DATE STRING, DENIAL_ID STRING, DENIAL_CODE STRING, PATIENTIDENTITYCODE STRING, CLAIMPOLICYNUMBER STRING, DATE_PAID STRING, HCPCS_CODE STRING, MOD1 STRING, POS DOUBLE, REV_CODE BIGINT, DOS STRING, LINE_ITEM_CONTROL_NUMBER BIGINT, ADMIT_DIAG STRING, DISCH_DIAG1 STRING, DISCH_DIAG2 STRING, DISCH_DIAG3 STRING, DISCH_DIAG4 STRING, DISCH_DIAG5 STRING, DISCH_DIAG6 STRING, ENCOUNTER_NBR BIGINT, DENIAL_DATE STRING, PAYER_TYPE STRING, APPEAL_LIMIT_DAYS INT, EXPECTED_REIMBURSEMENT DOUBLE, SOURCE_BATCH STRING'
);

CREATE OR REFRESH STREAMING TABLE bronze_clinical_notes
COMMENT 'Bronze: raw clinical-note JSON landed by the synthetic generator (Auto Loader). Append-only.'
AS SELECT *,
  current_timestamp() AS _ingested_at,
  _metadata.file_path AS _source_file
FROM STREAM read_files(
  '/Volumes/appeals_hackathon_catalog/fe_bar_appeals/landing/clinical_notes/',
  format => 'json',
  schemaHints => 'FACILITY_ID BIGINT, PATIENT_CONTROL_NUMBER BIGINT, ENCOUNTER_NBR BIGINT, PATIENT_NAME STRING, event_id BIGINT, event_tag STRING, note_date STRING, author_role STRING, plain_text STRING'
);
