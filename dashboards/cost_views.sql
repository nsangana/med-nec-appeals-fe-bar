-- =====================================================================
-- FE Bar appeals automation: platform cost attribution views
-- Catalog/schema: the :catalog and :schema job parameters (live: appeals_hackathon_catalog / fe_bar_appeals).
-- Workspace: fevm-appeals-hackathon (workspace_id 7474656043998914) only.
-- Idempotent: every statement is CREATE OR REPLACE / IF NOT EXISTS.
--
-- Definition (one place; dashboard + evidence both read these views):
--   * Metered rows: system.billing.usage filtered to this workspace and to
--     resources tagged with this build's IDs (usage_metadata.*). Only the
--     IDs listed in the mapping table below are included; everything else in
--     the workspace (other builds, other endpoints, other warehouses) is excluded.
--   * Price: system.billing.list_prices pricing.effective_list.default, joined
--     on sku_name and usage_start_time (time-correct; effective list = the
--     price that applies, e.g. Lakebase $0.26 from 2026-07-01). LIST PRICE ONLY,
--     no discounts.
--   * attribution = direct  : the cost is tagged to a build-owned resource ID.
--   * attribution = allocated: the cost sits on a shared resource (SQL warehouse,
--     VS endpoint) or cannot be split by caller; the rule is stated in `note`.
--   * cost_type = variable  : scales with appeals generated (LLM generation,
--     grounding, job compute, job warehouse share, SDP, Lakebase sync pipeline).
--   * cost_type = fixed    : always-on uptime (app, chat endpoint, Lakebase
--     compute/storage, VS endpoint).
--   * cost_type = other    : per-question / unlabelled items (Genie space,
--     unlabelled LLM calls). Included in fully loaded, not in variable.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. cost_attribution_daily
--    grain: usage_date x component x resource x product x sku x run_ref
-- ---------------------------------------------------------------------
-- Parameters (SQL task): :catalog and :schema. The schema is created first so that USE SCHEMA can succeed.
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema);
USE CATALOG IDENTIFIER(:catalog);
USE SCHEMA IDENTIFIER(:schema);

CREATE OR REPLACE VIEW cost_attribution_daily
COMMENT 'Daily list-price cost of the FE Bar appeals build, by component. Direct = tagged to build IDs; allocated = shared resource (rule in note). Variable/fixed/other per cost_type. Workspace 7474656043998914 only. List price (effective_list), no discounts. Billing lags a few hours.'
AS
WITH
-- Mapping: the ONLY place the build's resource IDs are listed.
component_map AS (
  SELECT * FROM VALUES
    ('Generation LLM',
     'databricks-claude-sonnet-4-6 via ai_query on warehouse 559faf81',
     'direct', 'variable',
     'Metered FM tokens for the appeal-generation ai_query. Warehouse tag = call origin (the build runs ai_query on 559faf81); the warehouse is not charged for these tokens.'),
    ('Grounding digests (ai_summarize)',
     'databricks-ai-summarize via ai_query on warehouse 559faf81',
     'direct', 'variable',
     'Per-encounter digest summaries (ai_summarize) run in the job before generation. Tagged by the warehouse the job queries.'),
    ('Job compute',
     'fe-bar-appeals-job (job_id 211997391364769)',
     'direct', 'variable',
     'Serverless jobs compute for the appeals job. run_ref = usage_metadata.job_run_id, so cost is per run.'),
    ('Warehouse SQL (job statements)',
     'SQL warehouse 559faf81 (shared, Medium, serverless)',
     'allocated', 'variable',
     'Allocation: job-attributed statement minutes (system.query.history query_source.job_info.job_id = 211997391364769) x 24 DBU/h (Medium serverless, as in COST_2B). Excludes warehouse idle/auto-stop uptime and all non-job statements (Naveen ad hoc, other builds), which stay unallocated.'),
    ('SDP pipeline',
     'fe-bar-appeals-sdp (4873b47b-47a7-4081-97c0-7cdf018c71a1)',
     'direct', 'variable',
     'Lakeflow SDP pipeline usage (usage_metadata.dlt_pipeline_id). run_ref = dlt_update_id.'),
    ('Lakebase sync pipeline',
     'synced-table refresh pipeline (0245f1ce-9b6c-49c9-88ae-1942576611d7)',
     'direct', 'variable',
     'Lakebase synced-table refresh pipeline (dlt_pipeline_id). run_ref = dlt_update_id.'),
    ('Lakebase compute + storage',
     'fe-bar-appeals-lakebase (project 401d8a7c-b2ea-4d86-b169-dd7dbf47a115)',
     'direct', 'fixed',
     'Autoscaling Lakebase project (0.5 CU, autosuspend). usage_metadata.project_id. Storage (DSU) and compute (DBU) both included.'),
    ('App',
     'fe-bar-appeals-app (usage_metadata.app_name)',
     'direct', 'fixed',
     'Databricks App compute uptime. Fixed while the app is running.'),
    ('Chat endpoint (always-on)',
     'fe-bar-appeals-chat (endpoint 4c30a63ab96f44c48a75be8d521af913)',
     'direct', 'fixed',
     'Model Serving endpoint compute billed by uptime. Scale-to-zero OFF, so this is fixed. Includes its AI Gateway rows. Per-request LLM tokens are in Unlabelled LLM calls.'),
    ('Vector Search endpoint (shared)',
     'appeals-vs-endpoint (b9138e36-84cd-452a-8003-a7f5f5ddf0df)',
     'allocated', 'fixed',
     'Shared with the earlier build on the same endpoint. Shown at 100% of endpoint uptime, so this is an upper bound for this build. The earlier build is not split out.'),
    ('Unlabelled LLM calls (chat + judge)',
     'databricks-claude-sonnet-4-6 and databricks-gte-large-en with no warehouse or job tag',
     'allocated', 'other',
     'Per-request FM tokens for the chat agent and the genai_evaluate judge. Billing carries no caller tag, so these cannot be split by caller and may include other workspace users of the same FM endpoints.'),
    ('Genie space (Agent)',
     'Genie space 01f1e7ec913217158b231c3e2f18fa20 (FE Bar Medical Necessity Appeals)',
     'direct', 'other',
     'Genie usage_metadata.genie.agent_id = this space. Per question/API call. Genie Code and other spaces are excluded.')
  AS m(component, resource, attribution, cost_type, note)
),
-- Metered rows for the build's resources (workspace-scoped).
metered AS (
  SELECT
    u.usage_date,
    u.usage_start_time,
    u.billing_origin_product AS product,
    u.sku_name,
    u.usage_quantity AS dbu,
    COALESCE(u.usage_metadata.job_run_id, u.usage_metadata.dlt_update_id) AS run_ref,
    CASE
      WHEN u.billing_origin_product = 'MODEL_SERVING'
       AND u.usage_metadata.endpoint_name = 'databricks-claude-sonnet-4-6'
       AND u.usage_metadata.warehouse_id = '559faf81d610a2a1' THEN 'Generation LLM'
      WHEN u.billing_origin_product = 'MODEL_SERVING'
       AND u.usage_metadata.endpoint_name = 'databricks-ai-summarize'
       AND u.usage_metadata.warehouse_id = '559faf81d610a2a1' THEN 'Grounding digests (ai_summarize)'
      WHEN u.billing_origin_product = 'JOBS'
       AND u.usage_metadata.job_id = '211997391364769' THEN 'Job compute'
      WHEN u.billing_origin_product = 'DLT'
       AND u.usage_metadata.dlt_pipeline_id = '4873b47b-47a7-4081-97c0-7cdf018c71a1' THEN 'SDP pipeline'
      WHEN u.billing_origin_product = 'LAKEBASE'
       AND u.usage_metadata.dlt_pipeline_id = '0245f1ce-9b6c-49c9-88ae-1942576611d7' THEN 'Lakebase sync pipeline'
      WHEN u.billing_origin_product = 'LAKEBASE'
       AND u.usage_metadata.project_id = '401d8a7c-b2ea-4d86-b169-dd7dbf47a115' THEN 'Lakebase compute + storage'
      WHEN u.billing_origin_product = 'APPS'
       AND u.usage_metadata.app_name = 'fe-bar-appeals-app' THEN 'App'
      WHEN u.billing_origin_product IN ('MODEL_SERVING', 'AI_GATEWAY')
       AND u.usage_metadata.endpoint_name = 'fe-bar-appeals-chat' THEN 'Chat endpoint (always-on)'
      WHEN u.billing_origin_product = 'VECTOR_SEARCH'
       AND u.usage_metadata.endpoint_name = 'appeals-vs-endpoint' THEN 'Vector Search endpoint (shared)'
      WHEN u.billing_origin_product = 'MODEL_SERVING'
       AND u.usage_metadata.endpoint_name IN ('databricks-claude-sonnet-4-6', 'databricks-gte-large-en')
       AND u.usage_metadata.warehouse_id IS NULL
       AND u.usage_metadata.job_id IS NULL THEN 'Unlabelled LLM calls (chat + judge)'
      WHEN u.billing_origin_product = 'GENIE'
       AND u.usage_metadata.genie.agent_id = '01f1e7ec913217158b231c3e2f18fa20' THEN 'Genie space (Agent)'
    END AS component
  FROM system.billing.usage u
  -- Build window starts 2026-11-24: first day with metered build resources
  -- (job, SDP, Lakebase project, chat endpoint, app, Genie space). Earlier VS
  -- endpoint and unlabelled-LLM usage since 2026-09-17 belongs to the earlier build.
  WHERE u.workspace_id = 7474656043998914
    AND u.usage_date >= DATE'2026-11-24'
),
-- Warehouse allocation: job-attributed statement minutes x 24 DBU/h.
warehouse_job_minutes AS (
  SELECT
    CAST(q.start_time AS DATE) AS usage_date,
    SUM(q.total_duration_ms) / 60000.0 AS job_statement_min
  FROM system.query.history q
  WHERE q.workspace_id = 7474656043998914
    AND q.compute.warehouse_id = '559faf81d610a2a1'
    AND q.query_source.job_info.job_id = '211997391364769'
  GROUP BY 1
),
warehouse_alloc AS (
  SELECT
    usage_date,
    CAST(usage_date AS TIMESTAMP) AS usage_start_time,
    'SQL' AS product,
    'ENTERPRISE_SERVERLESS_SQL_COMPUTE_US_EAST_N_VIRGINIA' AS sku_name,
    job_statement_min / 60.0 * 24.0 AS dbu,
    CAST(NULL AS STRING) AS run_ref,
    'Warehouse SQL (job statements)' AS component
  FROM warehouse_job_minutes
),
all_rows AS (
  SELECT * FROM metered WHERE component IS NOT NULL
  UNION ALL
  SELECT * FROM warehouse_alloc
),
prices AS (
  SELECT
    sku_name,
    price_start_time,
    price_end_time,
    COALESCE(pricing.effective_list.default, pricing.default) AS unit_price
  FROM system.billing.list_prices
)
SELECT
  r.usage_date,
  r.component,
  m.resource,
  r.product,
  r.sku_name AS sku,
  m.attribution,
  m.cost_type,
  m.note,
  r.run_ref,
  SUM(r.dbu) AS dbu,
  -- GENIE_FREE_USAGE has no list price (free tier) -> $0. Any other SKU with no
  -- price stays NULL so it is visible, never silently zero.
  ROUND(SUM(r.dbu * COALESCE(p.unit_price, CASE WHEN r.sku_name = 'GENIE_FREE_USAGE' THEN 0 END)), 4) AS list_usd
FROM all_rows r
JOIN component_map m
  ON m.component = r.component
LEFT JOIN prices p
  ON p.sku_name = r.sku_name
 AND r.usage_start_time >= p.price_start_time
 AND (p.price_end_time IS NULL OR r.usage_start_time < p.price_end_time)
GROUP BY ALL;


-- ---------------------------------------------------------------------
-- 2. cost_per_appeal_daily
--    appeals per day come from appeals_output.generated_at (current table
--    state). Days with cost but no appeals in the table show NULL per appeal.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW cost_per_appeal_daily
COMMENT 'Daily cost divided by appeals generated that day (appeals_output.generated_at). Fully loaded = all components; variable = generation + grounding + job + SDP + Lakebase sync. NULL where no appeals are in appeals_output for the day.'
AS
WITH cost AS (
  SELECT
    usage_date,
    SUM(list_usd) AS fully_loaded_usd,
    SUM(CASE WHEN cost_type = 'variable' THEN list_usd ELSE 0 END) AS variable_usd,
    SUM(CASE WHEN cost_type = 'fixed' THEN list_usd ELSE 0 END) AS fixed_usd,
    SUM(CASE WHEN component = 'Generation LLM' THEN list_usd ELSE 0 END) AS generation_llm_usd
  FROM cost_attribution_daily
  GROUP BY usage_date
),
appeals AS (
  SELECT CAST(generated_at AS DATE) AS usage_date, COUNT(*) AS appeals_generated
  FROM appeals_output
  GROUP BY 1
)
SELECT
  COALESCE(c.usage_date, a.usage_date) AS usage_date,
  COALESCE(a.appeals_generated, 0) AS appeals_generated,
  ROUND(COALESCE(c.fully_loaded_usd, 0), 4) AS fully_loaded_usd,
  ROUND(COALESCE(c.variable_usd, 0), 4) AS variable_usd,
  ROUND(COALESCE(c.fixed_usd, 0), 4) AS fixed_usd,
  ROUND(COALESCE(c.generation_llm_usd, 0), 4) AS generation_llm_usd,
  ROUND(c.fully_loaded_usd / NULLIF(a.appeals_generated, 0), 4) AS fully_loaded_per_appeal_usd,
  ROUND(c.variable_usd / NULLIF(a.appeals_generated, 0), 4) AS variable_per_appeal_usd,
  ROUND(c.generation_llm_usd / NULLIF(a.appeals_generated, 0), 4) AS llm_per_appeal_usd
FROM cost c
FULL OUTER JOIN appeals a
  ON a.usage_date = c.usage_date;


-- ---------------------------------------------------------------------
-- 3. cost_at_volume
--    Illustrative. Fixed $/day = the one complete day with full 24h uptime of the
--    always-on components (2026-11-25; 2026-11-24 is excluded because the chat
--    endpoint and app started partway through that day). Fixed is split into
--    own (direct) and shared VS (allocated). Variable $/appeal = measured variable $
--    / appeals over the days that have appeals in appeals_output.
--    total = fixed + variable. Genie space and unlabelled LLM ('other') are NOT
--    included here; they are shown in cost_attribution_daily.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW cost_at_volume
COMMENT 'Illustrative cost per appeal at 60/150/300/600 appeals per day = (fixed $/day / appeals per day) + measured variable $/appeal. Fixed run-rate from 2026-11-25 (first complete always-on day). Prototype run-rates at list price; production sizing and contracted rates will differ.'
AS
WITH fixed_day AS (
  SELECT
    COALESCE(SUM(CASE WHEN attribution = 'direct' AND cost_type = 'fixed' THEN list_usd END), 0) AS fixed_own_usd_per_day,
    COALESCE(SUM(CASE WHEN attribution = 'allocated' AND cost_type = 'fixed' THEN list_usd END), 0) AS fixed_shared_usd_per_day
  FROM cost_attribution_daily
  WHERE usage_date = DATE'2026-11-25'
),
variable_unit AS (
  SELECT
    SUM(c.variable_usd) / NULLIF(SUM(c.appeals_generated), 0) AS variable_usd_per_appeal,
    SUM(c.appeals_generated) AS appeals_measured
  FROM cost_per_appeal_daily c
  WHERE c.appeals_generated > 0
),
volumes AS (
  SELECT appeals_per_day FROM VALUES (60), (150), (180), (300), (600) AS v(appeals_per_day)
)
SELECT
  v.appeals_per_day,
  ROUND(f.fixed_own_usd_per_day, 2) AS fixed_own_usd_per_day,
  ROUND(f.fixed_shared_usd_per_day, 2) AS fixed_shared_vs_usd_per_day,
  ROUND(f.fixed_own_usd_per_day / v.appeals_per_day, 4) AS fixed_own_usd_per_appeal,
  ROUND(f.fixed_shared_usd_per_day / v.appeals_per_day, 4) AS fixed_shared_vs_usd_per_appeal,
  ROUND(u.variable_usd_per_appeal, 4) AS variable_usd_per_appeal,
  ROUND(f.fixed_own_usd_per_day / v.appeals_per_day + u.variable_usd_per_appeal, 4) AS total_own_usd_per_appeal,
  ROUND((f.fixed_own_usd_per_day + f.fixed_shared_usd_per_day) / v.appeals_per_day + u.variable_usd_per_appeal, 4) AS total_incl_shared_vs_usd_per_appeal,
  ROUND(u.variable_usd_per_appeal * v.appeals_per_day, 2) AS variable_usd_per_day,
  ROUND(f.fixed_own_usd_per_day + f.fixed_shared_usd_per_day + u.variable_usd_per_appeal * v.appeals_per_day, 2) AS total_incl_shared_vs_usd_per_day,
  u.appeals_measured AS variable_appeals_measured,
  'illustrative: measured prototype run-rates at list price; production sizing and contracted rates will differ' AS basis
FROM volumes v
CROSS JOIN fixed_day f
CROSS JOIN variable_unit u
ORDER BY v.appeals_per_day;
