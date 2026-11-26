-- review_state view: latest action per encounter + submitted_at + deadline_met.
-- Depends on the synced worklist table (fe_bar_appeals.worklist_serving) -> applied by setup_lakebase.sh once it exists.
CREATE OR REPLACE VIEW review_state AS
WITH latest AS (
  SELECT DISTINCT ON (facility_id, patient_control_number, encounter_nbr)
         facility_id, patient_control_number, encounter_nbr,
         action AS status, reviewer AS last_reviewer, created_at AS last_action_at
  FROM review_actions
  ORDER BY facility_id, patient_control_number, encounter_nbr, created_at DESC, id DESC
), submitted AS (
  SELECT facility_id, patient_control_number, encounter_nbr, MAX(created_at) AS submitted_at
  FROM review_actions WHERE action = 'SUBMIT'
  GROUP BY facility_id, patient_control_number, encounter_nbr
)
SELECT l.facility_id, l.patient_control_number, l.encounter_nbr,
       l.status, l.last_reviewer, l.last_action_at,
       s.submitted_at,
       (s.submitted_at IS NOT NULL AND s.submitted_at::date <= w.appeal_deadline) AS deadline_met
FROM latest l
LEFT JOIN submitted s USING (facility_id, patient_control_number, encounter_nbr)
-- Synced-table key columns are uppercase in Postgres (quoted identifiers).
LEFT JOIN fe_bar_appeals.worklist_serving w
  ON w."FACILITY_ID" = l.facility_id
 AND w."PATIENT_CONTROL_NUMBER" = l.patient_control_number
 AND w."ENCOUNTER_NBR" = l.encounter_nbr;
