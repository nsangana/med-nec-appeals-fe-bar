-- Stage 25: data_sheet_facts — DETERMINISTIC data sheet facts, one row per encounter in encounter_grounding.
-- Plain SQL only: NO ai_* calls. Every block is verbatim from source tables (claim, routing, criteria, notes, MPFS).
-- Not limited by the 60-per-run LLM cap: every grounded encounter gets a data sheet PDF (rendered by 40).
--
-- Incremental: MERGE keyed on the encounter. facts_hash is a sha2 over the rendered content, INCLUDING the
-- daily-varying days_remaining and worklist_tag, because they are printed on the sheet (a PDF re-render is cheap;
-- the LLM input_hash in 20 deliberately excludes them). A changed row keeps
-- its PDF path NULL so 40 re-renders it; an unchanged row keeps its path. Rows that drop out of grounding are deleted.

CREATE TABLE IF NOT EXISTS appeals_hackathon_catalog.fe_bar_appeals.data_sheet_facts (
  FACILITY_ID BIGINT, PATIENT_CONTROL_NUMBER BIGINT, ENCOUNTER_NBR BIGINT,
  patient_name STRING, dob_text STRING, sex STRING, member_id STRING, claim_number STRING, provider_name STRING,
  payer_name STRING, criteria_payer STRING, criteria_routing STRING, criteria_passages STRING,
  denial_code STRING, denial_reason STRING, what_to_prove STRING, carc_category STRING,
  dos_text STRING, pos STRING, hcpcs_codes STRING, modifiers STRING, dx_codes STRING,
  total_charges DOUBLE, expected_reimbursement DOUBLE,
  worklist_tag STRING, denial_date DATE, appeal_limit_days INT, appeal_deadline DATE, days_remaining INT, deadline_status STRING,
  mpfs_context STRING, notes_verbatim STRING, payer_contract_terms STRING,
  facts_hash STRING, data_sheet_pdf_path STRING, built_at TIMESTAMP
)
COMMENT 'Deterministic data sheet facts per grounded encounter (no LLM). Source of the *_datasheet.pdf renders.';

MERGE INTO appeals_hackathon_catalog.fe_bar_appeals.data_sheet_facts AS t
USING (
  WITH crit_src AS (
    SELECT payer_type,
      concat_ws('\n', transform(sort_array(collect_list(named_struct('id', chunk_id,
          'line', concat('[', source_file, ' ', substr(chunk_id, 1, 8), '] ', chunk_to_retrieve)))), x -> x.line)) AS criteria_passages,
      concat_ws(', ', sort_array(array_distinct(collect_list(source_file)))) AS criteria_sources
    FROM appeals_hackathon_catalog.fe_bar_appeals.med_nec_criteria
    GROUP BY payer_type
  ),
  src AS (
    SELECT g.FACILITY_ID, g.PATIENT_CONTROL_NUMBER, g.ENCOUNTER_NBR,
      coalesce(g.patient_name, '') AS patient_name,
      coalesce(date_format(g.dob, 'yyyy-MM-dd'), '') AS dob_text,
      coalesce(g.sex, '') AS sex,
      coalesce(g.member_id, '') AS member_id,
      coalesce(cast(g.claim_number AS STRING), '') AS claim_number,
      coalesce(g.provider_name, '') AS provider_name,
      coalesce(g.payer_name, '') AS payer_name,
      g.criteria_payer,
      concat('Payer ', coalesce(g.payer_name, '?'), ' routed to the ', g.criteria_payer, ' criteria set (source: ',
             coalesce(cr.criteria_sources, 'n/a'), '). Denial ', coalesce(g.denial_code, '?'), ': ',
             coalesce(g.reason_text, 'n/a'), '. The appeal must prove: ', coalesce(g.what_to_prove, 'n/a'), '.') AS criteria_routing,
      coalesce(cr.criteria_passages, '') AS criteria_passages,
      coalesce(g.denial_code, '') AS denial_code,
      coalesce(g.reason_text, '') AS denial_reason,
      coalesce(g.what_to_prove, '') AS what_to_prove,
      coalesce(g.category, '') AS carc_category,
      coalesce(cast(g.dos AS STRING), '') AS dos_text,
      coalesce(cast(g.pos AS STRING), '') AS pos,
      coalesce(g.hcpcs_codes, '') AS hcpcs_codes,
      coalesce(g.modifiers, '') AS modifiers,
      coalesce(g.dx_codes, '') AS dx_codes,
      g.total_charges, g.expected_reimbursement,
      g.worklist_tag, g.denial_date, g.appeal_limit_days, g.appeal_deadline, g.days_remaining, g.deadline_status,
      coalesce(g.mpfs_context, '(n/a)') AS mpfs_context,
      coalesce(g.notes_full, '(no notes)') AS notes_verbatim,
      'Payer contract terms: not reviewed (not available in this build)' AS payer_contract_terms
    FROM appeals_hackathon_catalog.fe_bar_appeals.encounter_grounding g
    LEFT JOIN crit_src cr ON cr.payer_type = g.criteria_payer
  )
  SELECT s.*,
    sha2(concat_ws('||',
      patient_name, dob_text, sex, member_id, claim_number, provider_name, payer_name, criteria_payer, criteria_routing,
      criteria_passages, denial_code, denial_reason, what_to_prove, carc_category, dos_text, pos, hcpcs_codes, modifiers,
      dx_codes, cast(total_charges AS STRING), cast(expected_reimbursement AS STRING), cast(denial_date AS STRING),
      cast(appeal_limit_days AS STRING), cast(appeal_deadline AS STRING), deadline_status,
      cast(days_remaining AS STRING), worklist_tag, mpfs_context, notes_verbatim,
      payer_contract_terms), 256) AS facts_hash,
    CAST(NULL AS STRING) AS data_sheet_pdf_path,
    current_timestamp() AS built_at
  FROM src s
) AS s
ON t.FACILITY_ID = s.FACILITY_ID AND t.PATIENT_CONTROL_NUMBER = s.PATIENT_CONTROL_NUMBER AND t.ENCOUNTER_NBR = s.ENCOUNTER_NBR
WHEN MATCHED AND t.facts_hash <> s.facts_hash THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE THEN DELETE;
