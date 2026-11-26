-- Stage 20: encounter_grounding — one row per NON-PAST_DUE denied encounter with everything the
-- generation step needs. Source = gold_denial_worklist (Agent A) joined to claim lines
-- (mednecessity_ai_agent) and dated clinical notes (medical_records), plus payer-routed criteria,
-- MPFS coding context and CARC routing.
--
-- Keys: composite (FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR). All legacy grounding columns are kept;
-- new: expected_reimbursement, appeal_deadline, days_remaining, deadline_status, priority_rank, input_hash.
--
-- Determinism matters: every collect_list is sorted so that input_hash is stable across runs. Otherwise an
-- unchanged encounter would look "changed" and be regenerated (the incremental MERGE in 30 depends on this).
-- input_hash deliberately EXCLUDES clinical_digest (an LLM summary that can vary run to run) and days_remaining
-- (changes daily). It covers every field that is placed into the generation prompt, except the digest.
--
-- INCREMENTAL DIGESTS (cost). ai_summarize is the only LLM call in this file. It runs only over
-- encounter_digest_pending: encounters whose current dated notes (notes_hash) have no cached digest yet.
-- An unchanged encounter costs nothing on a re-run, and its digest is read from encounter_digest_cache.
-- A failed summary (NULL) is not cached, so it is retried on the next run. Superseded digests are pruned
-- (only when encounter_notes_current is non-empty, so an empty gold can never wipe the cache).
-- input_hash does not depend on the digest, so caching it does not change input_hash for any encounter.
--
-- Run order inside this file: notes (no LLM) -> cache table -> pending (no LLM) -> MERGE (LLM) -> prune
-- -> grounding (no LLM). Each statement is idempotent; the job runs this file as one SQL task.
--
-- The appeals_output table is NOT touched by this file.

-- Parameters (SQL task): :catalog and :schema. Every statement after this point resolves unqualified
-- object names against them (the session keeps the USE settings for the whole file).
USE CATALOG IDENTIFIER(:catalog);
USE SCHEMA IDENTIFIER(:schema);

-- 1. Current dated notes per grounded encounter (no LLM). Derived; rebuilt each run.
CREATE OR REPLACE TABLE encounter_notes_current
COMMENT 'Current dated clinical notes per grounded encounter (one row each) with notes_hash = sha2(notes_full). Derived; rebuilt each run.'
AS
WITH gold AS (
  SELECT FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR
  FROM gold_denial_worklist
  WHERE deadline_status <> 'PAST_DUE'
),
-- Dated notes, ordered by note_date (then event_id) so citations can reference dated notes.
-- Each note line carries its date: "[2026-03-14 PT_VISIT] <text>".
note_items AS (
  SELECT r.FACILITY_ID, r.PATIENT_CONTROL_NUMBER, r.ENCOUNTER_NBR,
         named_struct('d', r.note_date, 'e', r.event_id,
           't', concat('[', coalesce(date_format(r.note_date, 'yyyy-MM-dd'), 'UNDATED'), ' ',
                        coalesce(r.event_tag, 'NOTE'), '] ', coalesce(r.plain_text, ''))) AS n
  FROM medical_records r
  JOIN gold g ON r.FACILITY_ID = g.FACILITY_ID AND r.PATIENT_CONTROL_NUMBER = g.PATIENT_CONTROL_NUMBER AND r.ENCOUNTER_NBR = g.ENCOUNTER_NBR
),
notes AS (
  SELECT FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR,
         concat_ws('\n\n', transform(sort_array(collect_list(n)), x -> x.t)) AS notes_full
  FROM note_items
  GROUP BY FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR
)
SELECT FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR, notes_full,
       sha2(notes_full, 256) AS notes_hash
FROM notes;

-- 2. Digest cache (survives runs). Keyed by the notes hash, so a changed note set is a new key.
CREATE TABLE IF NOT EXISTS encounter_digest_cache (
  FACILITY_ID BIGINT, PATIENT_CONTROL_NUMBER BIGINT, ENCOUNTER_NBR BIGINT,
  notes_hash STRING, clinical_digest STRING, digested_at TIMESTAMP
)
COMMENT 'LLM clinical digests (ai_summarize) keyed by notes_hash. Incremental cache: never CREATE OR REPLACE.';

-- 3. Pending = current notes with no cached digest for that exact notes_hash (no LLM).
CREATE OR REPLACE TABLE encounter_digest_pending
COMMENT 'Encounters whose notes are new or changed. The only rows ai_summarize sees. Derived; rebuilt each run.'
AS
SELECT n.FACILITY_ID, n.PATIENT_CONTROL_NUMBER, n.ENCOUNTER_NBR, n.notes_full, n.notes_hash
FROM encounter_notes_current n
LEFT ANTI JOIN encounter_digest_cache c
  ON c.FACILITY_ID = n.FACILITY_ID AND c.PATIENT_CONTROL_NUMBER = n.PATIENT_CONTROL_NUMBER
 AND c.ENCOUNTER_NBR = n.ENCOUNTER_NBR AND c.notes_hash = n.notes_hash;

-- 4. The only LLM call in this file: summarise the pending encounters and cache the non-NULL results.
MERGE INTO encounter_digest_cache AS t
USING (
  SELECT p.FACILITY_ID, p.PATIENT_CONTROL_NUMBER, p.ENCOUNTER_NBR, p.notes_hash,
         ai_summarize(p.notes_full, 400) AS clinical_digest,
         current_timestamp() AS digested_at
  FROM encounter_digest_pending p
) AS s
ON t.FACILITY_ID = s.FACILITY_ID AND t.PATIENT_CONTROL_NUMBER = s.PATIENT_CONTROL_NUMBER
 AND t.ENCOUNTER_NBR = s.ENCOUNTER_NBR AND t.notes_hash = s.notes_hash
WHEN NOT MATCHED AND s.clinical_digest IS NOT NULL THEN INSERT *;

-- 5. Prune digests of superseded note sets. Guarded: an empty current-notes table never wipes the cache.
DELETE FROM encounter_digest_cache c
WHERE EXISTS (SELECT 1 FROM encounter_notes_current)
  AND NOT EXISTS (
    SELECT 1 FROM encounter_notes_current n
    WHERE n.FACILITY_ID = c.FACILITY_ID AND n.PATIENT_CONTROL_NUMBER = c.PATIENT_CONTROL_NUMBER
      AND n.ENCOUNTER_NBR = c.ENCOUNTER_NBR AND n.notes_hash = c.notes_hash);

-- 6. Grounding (no LLM). Same columns and the same input_hash expression as before; the digest is read from the cache.
CREATE OR REPLACE TABLE encounter_grounding
COMMENT 'Per-encounter grounding for appeal generation (non-PAST_DUE denied encounters). Derived; rebuilt each run. clinical_digest comes from encounter_digest_cache.'
AS
WITH gold AS (
  SELECT FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR,
         expected_reimbursement, appeal_deadline, days_remaining, deadline_status, priority_rank,
         worklist_tag, denial_date, appeal_limit_days
  FROM gold_denial_worklist
  WHERE deadline_status <> 'PAST_DUE'
),
claim AS (
  SELECT m.FACILITY_ID, m.PATIENT_CONTROL_NUMBER, m.ENCOUNTER_NBR,
    max(m.PATIENT_NAME) AS patient_name, max(m.PATIENT_BIRTHDATE) AS dob, max(m.PATIENT_SEX) AS sex,
    max(m.PAYER_NAME) AS payer_name, max(m.HEALTH_PLAN_ID) AS member_id, max(m.CLAIM_NUMBER) AS claim_number,
    max(m.PROVIDER_NAME) AS provider_name, max(m.DOS) AS dos, max(m.POS) AS pos, max(m.TOTAL_CHARGES) AS total_charges,
    max(m.DENIAL_CODE) AS denial_code,
    concat_ws(', ', sort_array(array_distinct(collect_list(m.HCPCS_CODE)))) AS hcpcs_codes,
    concat_ws(', ', sort_array(array_distinct(filter(collect_list(m.MOD1), x -> x IS NOT NULL AND x <> '')))) AS modifiers,
    concat_ws(', ', sort_array(array_distinct(filter(flatten(collect_list(array(m.ADMIT_DIAG, m.DISCH_DIAG1, m.DISCH_DIAG2,
          m.DISCH_DIAG3, m.DISCH_DIAG4, m.DISCH_DIAG5, m.DISCH_DIAG6))), x -> x IS NOT NULL AND x <> '')))) AS dx_codes,
    CASE WHEN (upper(max(m.PAYER_NAME)) LIKE '%BLUE%' OR upper(max(m.PAYER_NAME)) LIKE '%BCBS%')
              AND upper(max(m.PAYER_NAME)) NOT LIKE '%MEDICARE%' AND upper(max(m.PAYER_NAME)) NOT LIKE '%ADVANTAGE%'
         THEN 'BCBS' ELSE 'CMS' END AS criteria_payer
  FROM mednecessity_ai_agent m
  JOIN gold g ON m.FACILITY_ID = g.FACILITY_ID AND m.PATIENT_CONTROL_NUMBER = g.PATIENT_CONTROL_NUMBER AND m.ENCOUNTER_NBR = g.ENCOUNTER_NBR
  WHERE m.DENIAL_CODE IN ('CO50','CO55','CO57','CO150','CO186')
  GROUP BY m.FACILITY_ID, m.PATIENT_CONTROL_NUMBER, m.ENCOUNTER_NBR
),
digest AS (
  -- notes_full is the same text as before (input_hash depends on it); the digest comes from the cache by notes_hash.
  SELECT n.FACILITY_ID, n.PATIENT_CONTROL_NUMBER, n.ENCOUNTER_NBR, n.notes_full, c.clinical_digest
  FROM encounter_notes_current n
  LEFT JOIN encounter_digest_cache c
    ON c.FACILITY_ID = n.FACILITY_ID AND c.PATIENT_CONTROL_NUMBER = n.PATIENT_CONTROL_NUMBER
   AND c.ENCOUNTER_NBR = n.ENCOUNTER_NBR AND c.notes_hash = n.notes_hash
),
mpfs_ctx AS (
  SELECT m.FACILITY_ID, m.PATIENT_CONTROL_NUMBER, m.ENCOUNTER_NBR,
    concat_ws('\n', sort_array(collect_list(concat(
      m.HCPCS_CODE, CASE WHEN coalesce(m.MOD1,'') <> '' THEN concat('-', m.MOD1) ELSE '' END,
      ': status ', coalesce(mp.S,'?'), ' (', coalesce(sd.description,'n/a'),
      '); global ', coalesce(mp.GLB,'?'), '; bilateral ', coalesce(mp.B,'?'), '; assistant ', coalesce(mp.A,'?'))))) AS mpfs_context
  FROM mednecessity_ai_agent m
  JOIN gold g ON m.FACILITY_ID = g.FACILITY_ID AND m.PATIENT_CONTROL_NUMBER = g.PATIENT_CONTROL_NUMBER AND m.ENCOUNTER_NBR = g.ENCOUNTER_NBR
  LEFT JOIN mpfs_indicator_listing mp
         ON m.HCPCS_CODE = mp.Code AND coalesce(mp.Modifier,'') = ''
  LEFT JOIN mpfs_indicator_descriptors sd
         ON sd.indicator_group = 'Status Code' AND sd.indicator_code = mp.S
  WHERE m.DENIAL_CODE IN ('CO50','CO55','CO57','CO150','CO186')
  GROUP BY m.FACILITY_ID, m.PATIENT_CONTROL_NUMBER, m.ENCOUNTER_NBR
),
crit AS (
  SELECT payer_type,
         concat_ws('\n- ', transform(sort_array(collect_list(named_struct('id', chunk_id, 'txt', chunk_to_retrieve))), x -> x.txt)) AS criteria_block
  FROM med_nec_criteria
  GROUP BY payer_type
)
SELECT c.FACILITY_ID, c.PATIENT_CONTROL_NUMBER, c.ENCOUNTER_NBR,
       c.patient_name, c.dob, c.sex, c.payer_name, c.member_id, c.claim_number,
       c.provider_name, c.dos, c.pos, c.total_charges, c.denial_code,
       s.reason_text, s.category, s.what_to_prove,
       c.hcpcs_codes, c.modifiers, c.dx_codes, c.criteria_payer,
       d.clinical_digest, d.notes_full, x.mpfs_context, cr.criteria_block,
       -- new columns (SPEC)
       g.expected_reimbursement, g.appeal_deadline, g.days_remaining, g.deadline_status, g.priority_rank,
       g.worklist_tag, g.denial_date, g.appeal_limit_days,
       sha2(concat_ws('||',
         coalesce(c.denial_code,''), coalesce(s.reason_text,''), coalesce(s.what_to_prove,''),
         coalesce(c.patient_name,''), coalesce(cast(c.dob AS STRING),''), coalesce(c.sex,''),
         coalesce(c.payer_name,''), coalesce(c.member_id,''), coalesce(cast(c.claim_number AS STRING),''),
         coalesce(cast(c.dos AS STRING),''), coalesce(cast(c.pos AS STRING),''), coalesce(cast(c.total_charges AS STRING),''),
         coalesce(c.provider_name,''), coalesce(c.hcpcs_codes,''), coalesce(c.modifiers,''), coalesce(c.dx_codes,''),
         coalesce(c.criteria_payer,''), coalesce(cr.criteria_block,''), coalesce(x.mpfs_context,''),
         coalesce(d.notes_full,''), coalesce(cast(g.expected_reimbursement AS STRING),''),
         coalesce(cast(g.appeal_deadline AS STRING),'')
       ), 256) AS input_hash
FROM claim c
JOIN gold g           ON c.FACILITY_ID = g.FACILITY_ID AND c.PATIENT_CONTROL_NUMBER = g.PATIENT_CONTROL_NUMBER AND c.ENCOUNTER_NBR = g.ENCOUNTER_NBR
LEFT JOIN digest d    ON c.FACILITY_ID = d.FACILITY_ID AND c.PATIENT_CONTROL_NUMBER = d.PATIENT_CONTROL_NUMBER AND c.ENCOUNTER_NBR = d.ENCOUNTER_NBR
LEFT JOIN mpfs_ctx x  ON c.FACILITY_ID = x.FACILITY_ID AND c.PATIENT_CONTROL_NUMBER = x.PATIENT_CONTROL_NUMBER AND c.ENCOUNTER_NBR = x.ENCOUNTER_NBR
LEFT JOIN denial_strategy s ON c.denial_code = s.denial_code
LEFT JOIN crit cr     ON c.criteria_payer = cr.payer_type;
