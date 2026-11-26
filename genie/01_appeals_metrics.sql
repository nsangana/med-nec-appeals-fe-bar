-- FE Bar metric view: appeals_metrics
-- Grain: one row per denied encounter (gold_denial_worklist). Joins are many-to-one (appeals_output is one row per
-- encounter key), LEFT OUTER, so every worklist encounter is counted even before an appeal is generated.
-- Metric view joins can't be used directly at query time: Genie and the app wrap this view in a CTE when they need other tables.
-- Cost per appeal is an ESTIMATE (cost_assumptions row, is_estimate = TRUE) until the orchestrator writes the measured value.
-- Requires DBR 17.2+ for YAML 1.1 (comment fields on dimensions and measures).
-- Parameters (SQL task): :catalog and :schema. Every statement after this point resolves unqualified
-- object names against them (the session keeps the USE settings for the whole file).
USE CATALOG IDENTIFIER(:catalog);
USE SCHEMA IDENTIFIER(:schema);

CREATE OR REPLACE VIEW appeals_metrics
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "FE Bar medical-necessity appeals KPIs. One row per denied encounter (gold worklist) with its generated appeal. Dollar measures use expected_reimbursement (contracted/allowed), not billed charges. Cost per appeal is an ESTIMATE until replaced with measured billing."
  source: gold_denial_worklist
  joins:
    - name: appeals
      source: appeals_output
      on: source.FACILITY_ID = appeals.FACILITY_ID AND source.PATIENT_CONTROL_NUMBER = appeals.PATIENT_CONTROL_NUMBER AND source.ENCOUNTER_NBR = appeals.ENCOUNTER_NBR
    - name: review
      source: review_state_uc
      on: source.FACILITY_ID = review.facility_id AND source.PATIENT_CONTROL_NUMBER = review.patient_control_number AND source.ENCOUNTER_NBR = review.encounter_nbr
  dimensions:
    - name: payer
      expr: payer_name
      comment: "Payer name (for example BCBS of Arizona)."
    - name: payer_type
      expr: payer_type
      comment: "COMMERCIAL, MEDICARE_ADVANTAGE or MEDICAID. Drives the appeal window (180, 65, 60 days)."
    - name: denial_code
      expr: denial_code
      comment: "CARC denial code, for example CO50 (not medically necessary)."
    - name: worklist_tag
      expr: worklist_tag
      comment: "NEW = denied yesterday. AT_RISK = 14 days or fewer remain. PAST_DUE = deadline passed. OPEN = everything else."
    - name: deadline_status
      expr: deadline_status
      comment: "PAST_DUE = deadline passed. AT_RISK = 14 days or fewer remain. OK = more than 14 days remain."
    - name: recommendation
      expr: COALESCE(appeals.recommendation, 'NOT GENERATED')
      comment: "WARRANTED, NOT WARRANTED or NEEDS REVIEW (AI recommendation). NOT GENERATED = no appeal yet."
    - name: review_status
      expr: COALESCE(review.status, 'NOT REVIEWED')
      comment: "Latest reviewer action from the review state: SUBMIT, EDIT, ROUTE_TO_REVIEW, or NOT REVIEWED."
  measures:
    - name: Appealable Revenue
      expr: SUM(CASE WHEN deadline_status <> 'PAST_DUE' THEN expected_reimbursement END)
      comment: "Expected reimbursement ($) of encounters whose appeal window is still open (not PAST_DUE)."
    - name: Expected Reimbursement (All Encounters)
      expr: SUM(expected_reimbursement)
      comment: "Expected reimbursement ($) across every worklist encounter, including PAST_DUE. Use for plain expected-vs-charges questions."
    - name: Revenue At Deadline Risk
      expr: SUM(CASE WHEN deadline_status = 'AT_RISK' THEN expected_reimbursement END)
      comment: "Expected reimbursement ($) with 14 days or fewer left to appeal (AT_RISK)."
    - name: Revenue Lost To Deadline
      expr: SUM(CASE WHEN deadline_status = 'PAST_DUE' THEN expected_reimbursement END)
      comment: "Expected reimbursement ($) whose appeal window has closed (PAST_DUE)."
    - name: Denials In Worklist
      expr: COUNT(1)
      comment: "Denied encounters in the worklist."
    - name: Appeals Generated
      expr: COUNT(appeals.recommendation)
      comment: "Encounters with a generated appeal recommendation."
    - name: Warranted Rate
      expr: COUNT(CASE WHEN appeals.recommendation = 'WARRANTED' THEN 1 END) / NULLIF(COUNT(appeals.recommendation), 0)
      comment: "Share of generated appeals recommended WARRANTED. Denominator = Appeals Generated."
    - name: NEEDS REVIEW Rate
      expr: COUNT(CASE WHEN appeals.recommendation = 'NEEDS REVIEW' THEN 1 END) / NULLIF(COUNT(appeals.recommendation), 0)
      comment: "Share of generated appeals routed to NEEDS REVIEW (a human must decide). Denominator = Appeals Generated."
    - name: Reviewed Encounters
      expr: COUNT(review.status)
      comment: "Encounters with at least one reviewer action in the review state."
    - name: Approval Rate
      expr: COUNT(CASE WHEN review.status = 'SUBMIT' THEN 1 END) / NULLIF(COUNT(review.status), 0)
      comment: "Share of reviewed encounters submitted (SUBMIT) as the approved appeal. Denominator = Reviewed Encounters. In this build the review state is SIMULATED (demo seed, small sample); REJECT is not in the data."
    - name: Appeals Submitted
      expr: COUNT(CASE WHEN review.status = 'SUBMIT' THEN 1 END)
      comment: "Encounters whose latest reviewer action is SUBMIT (review state is SIMULATED in this build)."
    - name: Illustrative Recoverable Revenue (Prototype)
      expr: SUM(CASE WHEN appeals.recommendation = 'WARRANTED' AND deadline_status <> 'PAST_DUE' THEN expected_reimbursement END)
      comment: "PROTOTYPE, ILLUSTRATIVE, synthetic data. Expected reimbursement of WARRANTED appeals whose window is still open. Not a forecast and not a customer result."
    - name: Cost Per Appeal (ESTIMATE)
      expr: MAX((SELECT c.unit_cost_usd FROM cost_assumptions c WHERE c.assumption_key = 'cost_per_appeal_usd'))
      comment: "ESTIMATE, not measured. USD per generated appeal, from cost_assumptions. Replace with the system.billing figure."
$$;
