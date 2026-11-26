-- FE Bar governance: column masks on PHI (synthetic data).
-- Idempotent: CREATE OR REPLACE on the mask function (no other object depends on it), SET MASK replaces any existing mask.
-- Scope (deliberate, see evidence/13_column_masks.md):
--   MASKED   appeals_output.patient_name
--            data_sheet_facts.patient_name, data_sheet_facts.member_id, data_sheet_facts.dob_text
--   NOT      worklist_serving (source of the Lakebase synced table), gold_denial_worklist and other SDP-managed objects,
--            encounter_grounding (pipeline/20_encounter_grounding.sql runs CREATE OR REPLACE TABLE every job run, which
--            drops masks), eval tables, the four chat-tool UC functions (never replaced here), claim_number, notes_verbatim.
--
-- Who sees real values: members of the WORKSPACE group fe-bar-appeals-reviewers (is_member checks workspace-local groups),
-- and the app service principal 059b0419-b956-41e1-a788-e5104b645dc9 (the Genie tab runs as it; current_user() is its
-- application id). Everyone else sees '***MASKED***'.
-- The job and the chat endpoint run as the owner (a group member), so they keep real values.
-- Requires USE CATALOG/USE SCHEMA and EXECUTE on mask_phi, plus MANAGE and SELECT on each table (owner has both).

CREATE OR REPLACE FUNCTION appeals_hackathon_catalog.fe_bar_appeals.mask_phi(val STRING)
RETURNS STRING
COMMENT 'PHI column mask (synthetic demo). Returns the real value to members of workspace group fe-bar-appeals-reviewers and to the app service principal 059b0419-b956-41e1-a788-e5104b645dc9 (Genie tab). Everyone else gets ***MASKED***. Identity checks (is_member, session_user) run as the INVOKER inside masks (docs: functions that check user context run as the invoker).'
RETURN CASE
  WHEN is_member('fe-bar-appeals-reviewers') THEN val
  WHEN session_user() = '059b0419-b956-41e1-a788-e5104b645dc9' THEN val
  ELSE '***MASKED***'
END;

-- appeals_output (managed Delta; written by MERGE in 30_generate_appeals.sql and 40_render_pdfs.py)
ALTER TABLE appeals_hackathon_catalog.fe_bar_appeals.appeals_output
  ALTER COLUMN patient_name SET MASK appeals_hackathon_catalog.fe_bar_appeals.mask_phi;

-- data_sheet_facts (managed Delta; CREATE TABLE IF NOT EXISTS + MERGE only, so the mask survives job runs)
ALTER TABLE appeals_hackathon_catalog.fe_bar_appeals.data_sheet_facts
  ALTER COLUMN patient_name SET MASK appeals_hackathon_catalog.fe_bar_appeals.mask_phi;
ALTER TABLE appeals_hackathon_catalog.fe_bar_appeals.data_sheet_facts
  ALTER COLUMN member_id SET MASK appeals_hackathon_catalog.fe_bar_appeals.mask_phi;
ALTER TABLE appeals_hackathon_catalog.fe_bar_appeals.data_sheet_facts
  ALTER COLUMN dob_text SET MASK appeals_hackathon_catalog.fe_bar_appeals.mask_phi;


-- 2026-11-26 (orchestrator): session_user() replaces current_user() per docs recommendation; TIMESTAMP variant for dob;
-- encounter_grounding masked too (docs: masks are retained when a table is replaced if the column names are unchanged).
CREATE OR REPLACE FUNCTION appeals_hackathon_catalog.fe_bar_appeals.mask_phi_ts(val TIMESTAMP)
RETURNS TIMESTAMP
COMMENT 'PHI column mask for TIMESTAMP columns (DOB). Real value for fe-bar-appeals-reviewers members and the app SP; NULL for everyone else.'
RETURN CASE
  WHEN is_member('fe-bar-appeals-reviewers') THEN val
  WHEN session_user() = '059b0419-b956-41e1-a788-e5104b645dc9' THEN val
  ELSE CAST(NULL AS TIMESTAMP)
END;
ALTER TABLE appeals_hackathon_catalog.fe_bar_appeals.encounter_grounding
  ALTER COLUMN patient_name SET MASK appeals_hackathon_catalog.fe_bar_appeals.mask_phi;
ALTER TABLE appeals_hackathon_catalog.fe_bar_appeals.encounter_grounding
  ALTER COLUMN member_id SET MASK appeals_hackathon_catalog.fe_bar_appeals.mask_phi;
ALTER TABLE appeals_hackathon_catalog.fe_bar_appeals.encounter_grounding
  ALTER COLUMN dob SET MASK appeals_hackathon_catalog.fe_bar_appeals.mask_phi_ts;
