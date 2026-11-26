-- Stage 30: generate appeals_output — INCREMENTAL, ONE ai_query per encounter (declarative, no agent framework).
--
-- Behaviour
--   * CREATE TABLE IF NOT EXISTS, never CREATE OR REPLACE: the render stage writes PDF paths into this table and
--     a replace would drop them. Change Data Feed is on.
--   * Candidates = encounter_grounding rows with NO appeals_output row, or whose input_hash changed.
--   * At most :max_appeals candidates per run (SQL task parameter, default 60 in the job). Order: hero claim (Elena Marquez, fixed demo key in SPEC) first, then
--     worklist_tag = NEW (denied yesterday), then lowest priority_rank.
--   * MERGE: matched rows are overwritten (PDF paths reset to NULL, so the render stage re-renders them);
--     unmatched rows are inserted. Model call errors (failOnError => false) are NOT written, so that encounter
--     stays pending and is retried on the next run.
--   * Three determinations: WARRANTED | NOT WARRANTED | NEEDS REVIEW. Output that cannot be normalised to one
--     of these, or that is missing a required section, is a PARSE FAILURE and is routed to NEEDS REVIEW with a
--     reason that starts with "PARSE_FAILURE:". Nothing is silently defaulted to WARRANTED.
--   * Never-fabricate rule: NEEDS REVIEW and NOT WARRANTED produce NO appeal letter (appeal_letter IS NULL).
--
-- Run order: 20_encounter_grounding -> 30_generate_appeals -> 40_render_pdfs.
-- The batch cap is the :max_appeals parameter, applied as LIMIT CAST(:max_appeals AS INT). A plain LIMIT :n
-- fails on this warehouse when the value arrives as a string (INVALID_LIMIT_LIKE_EXPRESSION), so it is cast.

-- Parameters (SQL task): :catalog and :schema. Every statement after this point resolves unqualified
-- object names against them (the session keeps the USE settings for the whole file).
USE CATALOG IDENTIFIER(:catalog);
USE SCHEMA IDENTIFIER(:schema);

CREATE TABLE IF NOT EXISTS appeals_output (
  FACILITY_ID BIGINT, PATIENT_CONTROL_NUMBER BIGINT, ENCOUNTER_NBR BIGINT,
  patient_name STRING, payer_name STRING, criteria_payer STRING, denial_code STRING, reason_text STRING,
  hcpcs_codes STRING, dx_codes STRING, dos TIMESTAMP, total_charges DOUBLE,
  recommendation STRING, needs_review_reason STRING, cheat_sheet STRING, appeal_letter STRING,
  clinical_digest STRING, raw_response STRING, generated_at TIMESTAMP,
  expected_reimbursement DOUBLE, appeal_deadline DATE, days_remaining INT, deadline_status STRING,
  priority_rank INT, input_hash STRING, model_name STRING,
  letter_pdf_path STRING, cheat_sheet_pdf_path STRING, data_sheet_pdf_path STRING
)
COMMENT 'Generated appeal recommendation per denied encounter (incremental MERGE from encounter_grounding). Never CREATE OR REPLACE: PDF paths live here.'
TBLPROPERTIES (delta.enableChangeDataFeed = true);

MERGE INTO appeals_output AS t
USING (
  WITH pending AS (
    SELECT g.*
    FROM encounter_grounding g
    LEFT JOIN appeals_output o
      ON o.FACILITY_ID = g.FACILITY_ID AND o.PATIENT_CONTROL_NUMBER = g.PATIENT_CONTROL_NUMBER AND o.ENCOUNTER_NBR = g.ENCOUNTER_NBR
    WHERE o.FACILITY_ID IS NULL OR o.input_hash IS NULL OR o.input_hash <> g.input_hash
    -- order: hero claim first (fixed demo key, must be in batch 1), then NEW (denied yesterday), then priority_rank
    ORDER BY CASE WHEN g.FACILITY_ID = 101 AND g.PATIENT_CONTROL_NUMBER = 770000001 AND g.ENCOUNTER_NBR = 50000001 THEN 0
                  WHEN g.worklist_tag = 'NEW' THEN 1 ELSE 2 END,
             g.priority_rank
    LIMIT CAST(:max_appeals AS INT)
  ),
  gen AS (
    SELECT p.*,
      ai_query('databricks-claude-sonnet-4-6',
        concat(
          'You are a Medical-Necessity Appeals analyst for the Revenue Cycle team of a hospital health system. Work through this EXACT process internally, then output the required sections.\n\n',
          'PROCESS:\n',
          '1. Payer: ', coalesce(payer_name,''), '. Criteria set to apply: ', coalesce(criteria_payer,''),
          ' (BCBS Arizona commercial -> BCBS criteria; BCBS Medicare Advantage or any other/Medicare payer -> CMS definition).\n',
          '2. Denial ', coalesce(denial_code,''), ' - ', coalesce(reason_text,''), '. The appeal must prove: ', coalesce(what_to_prove,''), '.\n',
          '3. Apply the applicable medical-necessity criteria (below) to the documented clinical facts.\n',
          '4. Assess medical necessity: clinical indication vs diagnosis, severity, appropriateness of the service, timing/urgency.\n',
          '5. Assess supporting documentation: conservative treatment tried (with DATES and outcomes) OR a valid contraindication; imaging; functional limitations; provider rationale.\n',
          '6. Decide exactly one of: WARRANTED, NOT WARRANTED, NEEDS REVIEW.\n',
          '   - WARRANTED: the documented evidence clearly meets the criteria.\n',
          '   - NOT WARRANTED: the documented evidence clearly fails the criteria. State which criterion fails.\n',
          '   - NEEDS REVIEW: the evidence is insufficient, ambiguous or contradictory to decide either way. Name exactly which documentation is missing or conflicting. Do NOT write an appeal letter in this case. Do NOT guess.\n\n',
          'EVIDENCE RULES (apply to every determination):\n',
          '- Every clinical fact must cite the dated note it came from, using its bracket label exactly, for example [2026-03-14 PT_VISIT].\n',
          '- Every criterion you rely on must be quoted or named from the criteria block below.\n',
          '- Never invent facts, dates, scores, member IDs or provider identifiers. If a field is unknown, say unknown or use a bracketed placeholder.\n\n',
          'APPLICABLE MEDICAL-NECESSITY CRITERIA (', coalesce(criteria_payer,''), '):\n- ', coalesce(criteria_block,''), '\n\n',
          'CLAIM:\n- Patient: ', coalesce(patient_name,''), ', DOB ', coalesce(cast(dob AS STRING),''), ', Sex ', coalesce(sex,''), '\n',
          '- Payer: ', coalesce(payer_name,''), ', Member ID ', coalesce(member_id,'[Member ID]'), ', Claim ', coalesce(cast(claim_number AS STRING),''), '\n',
          '- Date of Service: ', coalesce(cast(dos AS STRING),''), ', POS ', coalesce(cast(pos AS STRING),''), '\n',
          '- Procedures (CPT/HCPCS): ', coalesce(hcpcs_codes,''), '  Modifiers: ', coalesce(modifiers,'(none)'), '\n',
          '- Diagnoses (ICD-10): ', coalesce(dx_codes,''), '\n- Total charges: $', coalesce(cast(total_charges AS STRING),''),
          '\n- Provider: ', coalesce(provider_name,''), '\n\n',
          'MPFS CODING CONTEXT (cite only if relevant to the denial):\n', coalesce(mpfs_context,'(n/a)'), '\n\n',
          'CLINICAL DOCUMENTATION - DATED NOTES (chronological; cite by bracket label):\n', coalesce(notes_full,'(no notes)'), '\n\n',
          'CLINICAL DIGEST (orientation only; cite the dated notes, not this summary):\n', coalesce(clinical_digest,''), '\n\n',
          'OUTPUT exactly these four sections with these literal delimiters, nothing before the first delimiter:\n',
          '===DETERMINATION===\nOne line only: WARRANTED or NOT WARRANTED or NEEDS REVIEW\n',
          '===CHEAT_SHEET===\n',
          'AI REASONING WORKSHEET: a decision worksheet of how the determination was reached, so a reviewer can verify it against the notes. Use these headings:\n',
          '- Determination and one-line rationale\n',
          '- Payer and criteria set (which and why)\n',
          '- Denial and what must be proven\n',
          '- Criteria applied (quote the specific criteria text from the block above)\n',
          '- Evidence mapping: for EACH criterion, the specific fact and its dated citation, e.g. "[2026-03-14 PT_VISIT] ..." -> meets / fails / missing\n',
          '- Medical necessity assessment (indication, severity, appropriateness, timing)\n',
          '- Supporting-documentation checklist: conservative treatment with dates and outcomes, imaging, functional limitation, provider rationale -> present / absent, with citation\n',
          '- Gaps or conflicts found (required when NEEDS REVIEW)\n',
          '- Coding/MPFS context (only if relevant)\n',
          '===APPEAL_LETTER===\n',
          'If WARRANTED: a complete send-ready formal appeal letter (at most 1.5 pages) on the letterhead of the health system (use the placeholder [Health System Name]) with a signature block, business format. Include a RE: block (Patient, DOB, Member ID, DOS, Claim number, Denial Reason, Procedure Codes). Argue medical necessity grounded in the criteria. QUOTE the specific dated record excerpts (with dates and note type) that support each criterion, and cite the criteria passage. Request the denial be overturned and the claim reprocessed. Use bracketed placeholders like [Provider NPI] for any field not supplied. Do NOT use the phrase "not warranted" in a warranted letter.\n',
          'If NOT WARRANTED or NEEDS REVIEW: output exactly "(No appeal letter - not warranted.)" or "(No appeal letter - needs review.)" and nothing else.\n',
          '===NEEDS_REVIEW_REASON===\n',
          'If NEEDS REVIEW: a bulleted list naming EXACTLY which documentation is missing or conflicting, one item per gap, each specific enough for a reviewer to request it. Otherwise output: N/A\n',
          'Do not add any text outside these four sections.'
        ),
        modelParameters => named_struct('temperature', CAST(0.1 AS DOUBLE), 'max_tokens', 6000),
        failOnError => false
      ) AS ai
    FROM pending p
  ),
  ok AS (
    -- model-call errors are dropped here on purpose: the encounter stays pending and is retried next run
    SELECT * FROM gen WHERE ai.errorMessage IS NULL AND ai.result IS NOT NULL
  ),
  split AS (
    SELECT o.*, ai.result AS resp,
      regexp_extract(ai.result, '(?s)===DETERMINATION===\\s*(.*?)\\s*(?:===CHEAT_SHEET===|$)', 1) AS det_block,
      regexp_extract(ai.result, '(?s)===CHEAT_SHEET===\\s*(.*?)\\s*(?:===APPEAL_LETTER===|===NEEDS_REVIEW_REASON===|$)', 1) AS cheat_block,
      regexp_extract(ai.result, '(?s)===APPEAL_LETTER===\\s*(.*?)\\s*(?:===NEEDS_REVIEW_REASON===|$)', 1) AS letter_block,
      regexp_extract(ai.result, '(?s)===NEEDS_REVIEW_REASON===\\s*(.*)$', 1) AS nr_block
    FROM ok o
  ),
  norm AS (
    -- first non-empty line of the determination section, reduced to letters and single spaces
    SELECT s.*,
      trim(regexp_replace(
        regexp_replace(upper(trim(regexp_extract(det_block, '(?s)^\\s*([^\\r\\n]+)', 1))), '[^A-Z ]', ''),
        ' +', ' ')) AS det_norm
    FROM split s
  ),
  checked AS (
    SELECT n.*,
      CASE WHEN det_norm IN ('WARRANTED', 'NOT WARRANTED', 'NEEDS REVIEW') THEN det_norm END AS det_valid,
      (length(trim(letter_block)) > 0 AND letter_block NOT LIKE '(No appeal letter%') AS letter_ok,
      (length(trim(cheat_block)) > 0) AS cheat_ok
    FROM norm n
  ),
  flagged AS (
    SELECT c.*,
      CASE
        WHEN det_valid IS NULL THEN concat('determination not one of WARRANTED / NOT WARRANTED / NEEDS REVIEW (model wrote: "', left(trim(det_block), 80), '")')
        WHEN NOT cheat_ok THEN 'AI reasoning worksheet section missing'
        WHEN det_valid = 'WARRANTED' AND NOT letter_ok THEN 'WARRANTED without an appeal letter'
      END AS parse_problem
    FROM checked c
  ),
  decided AS (
    SELECT f.*,
      CASE WHEN parse_problem IS NOT NULL THEN 'NEEDS REVIEW' ELSE det_valid END AS recommendation
    FROM flagged f
  )
  SELECT d.FACILITY_ID, d.PATIENT_CONTROL_NUMBER, d.ENCOUNTER_NBR,
         d.patient_name, d.payer_name, d.criteria_payer, d.denial_code, d.reason_text,
         d.hcpcs_codes, d.dx_codes, d.dos, d.total_charges,
         d.recommendation,
         CASE
           WHEN d.parse_problem IS NOT NULL THEN concat('PARSE_FAILURE: ', d.parse_problem,
                '. Routed to NEEDS REVIEW by the pipeline; reviewer to check raw_response.')
           WHEN d.det_valid = 'NEEDS REVIEW' THEN coalesce(nullif(trim(d.nr_block), ''), 'NEEDS REVIEW (model gave no reason)')
         END AS needs_review_reason,
         nullif(trim(d.cheat_block), '') AS cheat_sheet,
         CASE WHEN d.recommendation = 'WARRANTED' THEN nullif(trim(d.letter_block), '') END AS appeal_letter,
         d.clinical_digest, d.resp AS raw_response, current_timestamp() AS generated_at,
         d.expected_reimbursement, d.appeal_deadline, d.days_remaining, d.deadline_status,
         d.priority_rank, d.input_hash, 'databricks-claude-sonnet-4-6' AS model_name,
         CAST(NULL AS STRING) AS letter_pdf_path, CAST(NULL AS STRING) AS cheat_sheet_pdf_path,
         CAST(NULL AS STRING) AS data_sheet_pdf_path
  FROM decided d
) AS s
ON t.FACILITY_ID = s.FACILITY_ID AND t.PATIENT_CONTROL_NUMBER = s.PATIENT_CONTROL_NUMBER AND t.ENCOUNTER_NBR = s.ENCOUNTER_NBR
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
