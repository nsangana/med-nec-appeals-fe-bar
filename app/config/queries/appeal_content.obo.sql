-- Full markdown content for a single appeal, keyed by the composite key.
-- Used to render the in-app "Text" fallback view of the letter / cheat sheet.
-- @param facility_id STRING
-- @param account STRING
-- @param encounter_nbr STRING
SELECT
  cheat_sheet,
  appeal_letter,
  patient_name,
  recommendation
FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_output
WHERE CAST(FACILITY_ID AS STRING) = :facility_id
  AND CAST(PATIENT_CONTROL_NUMBER AS STRING) = :account
  AND CAST(ENCOUNTER_NBR AS STRING) = :encounter_nbr
LIMIT 1
