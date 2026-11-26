-- FE Bar governance: PHI column tags + synthetic table classification.
-- Idempotent: SET TAGS upserts, so re-running is safe.
-- Scope: the :catalog.:schema build schema only. Synthetic data (seed 20261124); tags are still applied
-- so the PHI pattern is exercised end to end.
-- phi_type values: name | dob | mrn | member_id | claim_id

-- ---- bronze (raw claim lines and notes, landed JSON) ----
-- Parameters (SQL task): :catalog and :schema. Every statement after this point resolves unqualified
-- object names against them (the session keeps the USE settings for the whole file).
USE CATALOG IDENTIFIER(:catalog);
USE SCHEMA IDENTIFIER(:schema);

ALTER TABLE bronze_claims ALTER COLUMN PATIENT_NAME SET TAGS ('phi' = 'true', 'phi_type' = 'name');
ALTER TABLE bronze_claims ALTER COLUMN PATIENT_BIRTHDATE SET TAGS ('phi' = 'true', 'phi_type' = 'dob');
ALTER TABLE bronze_claims ALTER COLUMN MEDICAL_RECORD_NUMBER SET TAGS ('phi' = 'true', 'phi_type' = 'mrn');
ALTER TABLE bronze_claims ALTER COLUMN HEALTH_PLAN_ID SET TAGS ('phi' = 'true', 'phi_type' = 'member_id');
ALTER TABLE bronze_claims ALTER COLUMN CLAIMPOLICYNUMBER SET TAGS ('phi' = 'true', 'phi_type' = 'member_id');
ALTER TABLE bronze_claims ALTER COLUMN CLAIM_NUMBER SET TAGS ('phi' = 'true', 'phi_type' = 'claim_id');
ALTER TABLE bronze_clinical_notes ALTER COLUMN PATIENT_NAME SET TAGS ('phi' = 'true', 'phi_type' = 'name');

-- ---- silver ----
ALTER TABLE silver_claim_lines ALTER COLUMN PATIENT_NAME SET TAGS ('phi' = 'true', 'phi_type' = 'name');
ALTER TABLE silver_claim_lines ALTER COLUMN PATIENT_BIRTHDATE SET TAGS ('phi' = 'true', 'phi_type' = 'dob');
ALTER TABLE silver_claim_lines ALTER COLUMN MEDICAL_RECORD_NUMBER SET TAGS ('phi' = 'true', 'phi_type' = 'mrn');
ALTER TABLE silver_claim_lines ALTER COLUMN HEALTH_PLAN_ID SET TAGS ('phi' = 'true', 'phi_type' = 'member_id');
ALTER TABLE silver_claim_lines ALTER COLUMN CLAIMPOLICYNUMBER SET TAGS ('phi' = 'true', 'phi_type' = 'member_id');
ALTER TABLE silver_claim_lines ALTER COLUMN CLAIM_NUMBER SET TAGS ('phi' = 'true', 'phi_type' = 'claim_id');
ALTER TABLE silver_clinical_notes ALTER COLUMN PATIENT_NAME SET TAGS ('phi' = 'true', 'phi_type' = 'name');

-- ---- gold / serving-layer inputs ----
ALTER TABLE mednecessity_ai_agent ALTER COLUMN PATIENT_NAME SET TAGS ('phi' = 'true', 'phi_type' = 'name');
ALTER TABLE mednecessity_ai_agent ALTER COLUMN PATIENT_BIRTHDATE SET TAGS ('phi' = 'true', 'phi_type' = 'dob');
ALTER TABLE mednecessity_ai_agent ALTER COLUMN MEDICAL_RECORD_NUMBER SET TAGS ('phi' = 'true', 'phi_type' = 'mrn');
ALTER TABLE mednecessity_ai_agent ALTER COLUMN HEALTH_PLAN_ID SET TAGS ('phi' = 'true', 'phi_type' = 'member_id');
ALTER TABLE mednecessity_ai_agent ALTER COLUMN CLAIMPOLICYNUMBER SET TAGS ('phi' = 'true', 'phi_type' = 'member_id');
ALTER TABLE mednecessity_ai_agent ALTER COLUMN CLAIM_NUMBER SET TAGS ('phi' = 'true', 'phi_type' = 'claim_id');
ALTER TABLE medical_records ALTER COLUMN PATIENT_NAME SET TAGS ('phi' = 'true', 'phi_type' = 'name');
ALTER TABLE gold_denial_worklist ALTER COLUMN patient_name SET TAGS ('phi' = 'true', 'phi_type' = 'name');
ALTER TABLE encounter_grounding ALTER COLUMN patient_name SET TAGS ('phi' = 'true', 'phi_type' = 'name');
ALTER TABLE encounter_grounding ALTER COLUMN dob SET TAGS ('phi' = 'true', 'phi_type' = 'dob');
ALTER TABLE encounter_grounding ALTER COLUMN member_id SET TAGS ('phi' = 'true', 'phi_type' = 'member_id');
ALTER TABLE encounter_grounding ALTER COLUMN claim_number SET TAGS ('phi' = 'true', 'phi_type' = 'claim_id');

-- ---- table-level synthetic marker. Key is `synthetic` (NOT data_classification): the workspace tag policy for
-- data_classification allows only u-nnpi, cui, pii, so 'synthetic' is rejected there. Do not edit the policy from here. ----
ALTER TABLE bronze_claims SET TAGS ('synthetic' = 'true');
ALTER TABLE bronze_clinical_notes SET TAGS ('synthetic' = 'true');
ALTER TABLE silver_claim_lines SET TAGS ('synthetic' = 'true');
ALTER TABLE silver_clinical_notes SET TAGS ('synthetic' = 'true');
ALTER TABLE mednecessity_ai_agent SET TAGS ('synthetic' = 'true');
ALTER TABLE medical_records SET TAGS ('synthetic' = 'true');
ALTER TABLE gold_denial_worklist SET TAGS ('synthetic' = 'true');
ALTER TABLE mpfs_indicator_listing SET TAGS ('synthetic' = 'true');
ALTER TABLE encounter_grounding SET TAGS ('synthetic' = 'true');
ALTER TABLE denial_strategy SET TAGS ('synthetic' = 'true');
ALTER TABLE med_nec_criteria SET TAGS ('synthetic' = 'true');
ALTER TABLE mpfs_indicator_descriptors SET TAGS ('synthetic' = 'true');
ALTER TABLE eval_case_labels SET TAGS ('synthetic' = 'true');

-- ---- added once B (appeals_output), C (worklist_serving, data_sheet_facts, review_state_uc) and D's cost table existed ----
ALTER TABLE appeals_output ALTER COLUMN patient_name SET TAGS ('phi' = 'true', 'phi_type' = 'name');
ALTER TABLE worklist_serving ALTER COLUMN patient_name SET TAGS ('phi' = 'true', 'phi_type' = 'name');
ALTER TABLE data_sheet_facts ALTER COLUMN patient_name SET TAGS ('phi' = 'true', 'phi_type' = 'name');
ALTER TABLE data_sheet_facts ALTER COLUMN dob_text SET TAGS ('phi' = 'true', 'phi_type' = 'dob');
ALTER TABLE data_sheet_facts ALTER COLUMN member_id SET TAGS ('phi' = 'true', 'phi_type' = 'member_id');
ALTER TABLE data_sheet_facts ALTER COLUMN claim_number SET TAGS ('phi' = 'true', 'phi_type' = 'claim_id');
ALTER TABLE appeals_output SET TAGS ('synthetic' = 'true');
ALTER TABLE worklist_serving SET TAGS ('synthetic' = 'true');
ALTER TABLE data_sheet_facts SET TAGS ('synthetic' = 'true');
ALTER TABLE review_state_uc SET TAGS ('synthetic' = 'true');
ALTER TABLE cost_assumptions SET TAGS ('synthetic' = 'true');
