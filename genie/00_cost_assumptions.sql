-- FE Bar cost assumptions for the appeals metric view (cost per appeal).
-- Idempotent: creates the table if missing and inserts the ESTIMATE row only when that key is absent.
-- The orchestrator replaces the ESTIMATE with the measured system.billing figure by UPDATE on assumption_key
-- (never by CREATE OR REPLACE, which would drop the row).
-- The ESTIMATE value below is a placeholder, NOT a measured cost.
-- Parameters (SQL task): :catalog and :schema. Every statement after this point resolves unqualified
-- object names against them (the session keeps the USE settings for the whole file).
USE CATALOG IDENTIFIER(:catalog);
USE SCHEMA IDENTIFIER(:schema);

CREATE TABLE IF NOT EXISTS cost_assumptions (
  assumption_key STRING NOT NULL COMMENT 'Stable key, e.g. cost_per_appeal_usd',
  unit_cost_usd DECIMAL(21,4) COMMENT 'USD per unit. Keep 4 decimals: per-appeal costs are small',
  basis STRING COMMENT 'Where the number came from',
  is_estimate BOOLEAN COMMENT 'TRUE = placeholder estimate, not measured',
  updated_at TIMESTAMP COMMENT 'When the row was last written'
)
COMMENT 'Unit-cost assumptions used by appeals_metrics. Currently one ESTIMATE row (cost per appeal).';

MERGE INTO cost_assumptions AS t
USING (
  SELECT 'cost_per_appeal_usd' AS assumption_key,
         CAST(1.0000 AS DECIMAL(21,4)) AS unit_cost_usd,
         'ESTIMATE placeholder. Not measured. Replace with the system.billing figure for the appeals pipeline and LLM calls.' AS basis,
         TRUE AS is_estimate
) AS s
ON t.assumption_key = s.assumption_key
WHEN NOT MATCHED THEN INSERT (assumption_key, unit_cost_usd, basis, is_estimate, updated_at)
  VALUES (s.assumption_key, s.unit_cost_usd, s.basis, s.is_estimate, current_timestamp());
