# 15 — Cost dashboard: "Appeals Automation Agent Insights"

How the automation cost was measured, what it is, and how it reconciles with COST_2B. Prototype on synthetic data; list price only; workspace `fevm-appeals-hackathon` (workspace_id 7474656043998914) only.

## Dashboard

| Item | Value |
|---|---|
| Name | Appeals Automation Agent Insights |
| Dashboard id | `01f1e968adcd1e3b93920b557b986458` |
| Published URL | https://fevm-appeals-hackathon.cloud.databricks.com/dashboardsv3/01f1e968adcd1e3b93920b557b986458/published |
| Draft URL | https://fevm-appeals-hackathon.cloud.databricks.com/dashboardsv3/01f1e968adcd1e3b93920b557b986458 |
| Location | owner's workspace folder (`/Users/<owner>/Appeals Automation Agent Insights.lvdash.json`) |
| Warehouse | `559faf81d610a2a1` (shared; allocation rule below) |
| Publish | published with `embed_credentials: false`. No sharing, grants or permission changes |
| Pages | Overview (KPIs, daily stacked bar, cost per appeal by day, cost at volume, component breakdown), Components (pipelines and runs, agents, app/Lakebase/VS), Method (text) |
| Date filter | Usage date range on Overview and Components |
| Source JSON | `dashboards/appeals_automation_agent_insights.lvdash.json` |

Verification: all 7 dataset SQLs were run through the SQL statements API with catalog `appeals_hackathon_catalog` and schema `fe_bar_appeals`, the same resolution that `--dataset-catalog` and `--dataset-schema` use. All succeeded. Widget field bindings and the 12-column layout were checked programmatically with no problems. The dashboard was not visually rendered; the checks are at SQL and JSON level.

## View DDL (`dashboards/cost_views.sql`, idempotent)

- `cost_attribution_daily`: grain usage_date × component × resource × product × sku × attribution × cost_type × run_ref. Columns: `usage_date, component, resource, product, sku, attribution (direct|allocated), cost_type (variable|fixed|other), note, run_ref, dbu, list_usd`.
  - Metered rows come from `system.billing.usage` (workspace 7474656043998914, `usage_date >= 2026-11-24`). A mapping table lists the build's resource IDs. Anything not listed is excluded.
  - Price is `pricing.effective_list.default` from `system.billing.list_prices`, joined on SKU and `usage_start_time` (time-correct). List price only.
  - Warehouse allocation (derived row): job-attributed statement minutes from `system.query.history` (`query_source.job_info.job_id = 211997391364769`) × 24 DBU/h (Medium serverless). This matches COST_2B.
  - Unknown price for a non-free SKU stays NULL, so it cannot be silently zero. The check returned 0 NULL prices.
- `cost_per_appeal_daily`: daily cost ÷ `appeals_output` rows by `generated_at` date. Fully loaded and variable columns, plus per-appeal columns. Per-appeal is NULL where the table has no appeals for that day.
- `cost_at_volume`: illustrative. Fixed $/day is the 2026-11-25 run-rate (the first complete always-on day). Variable $/appeal is measured. Rows for 60, 150, 180, 300 and 600 appeals/day, split own vs shared VS. The `basis` column carries the required illustrative caveat.

## Results

### Cost by component (2026-11-24 to 2026-11-26, list price)

| Component | Attribution | Cost type | DBU | List $ | % |
|---|---|---|---:|---:|---:|
| Generation LLM (claude-sonnet-4-6 via ai_query on warehouse 559faf81) | direct | variable | 533.18 | 37.32 | 32.8 |
| Chat endpoint `fe-bar-appeals-chat` (always-on) | direct | fixed | 351.94 | 24.64 | 21.7 |
| App `fe-bar-appeals-app` | direct | fixed | 20.52 | 19.50 | 17.1 |
| Vector Search endpoint `appeals-vs-endpoint` (shared) | allocated | fixed | 204.00 | 14.28 | 12.6 |
| Warehouse 559faf81, job statements (shared) | allocated | variable | 13.44 | 9.41 | 8.3 |
| Job compute `fe-bar-appeals-job` | direct | variable | 7.31 | 3.29 | 2.9 |
| Grounding digests (ai_summarize on warehouse) | direct | variable | 38.90 | 2.72 | 2.4 |
| SDP pipeline `fe-bar-appeals-sdp` | direct | variable | 3.49 | 1.57 | 1.4 |
| Unlabelled LLM calls (chat per-request + judge) | allocated | other | 5.51 | 0.39 | 0.3 |
| Lakebase synced-table pipeline | direct | variable | 0.79 | 0.36 | 0.3 |
| Lakebase compute + storage (`fe-bar-appeals-lakebase`) | direct | fixed | 0.99 | 0.25 | 0.2 |
| Genie space `01f1e7ec…` (Agent) | direct | other | 106.31 | 0.05 | 0.0 |
| **Total** | | | | **113.76** | 100 |

Notes: the Genie figure is mostly free-tier usage (`GENIE_FREE_USAGE`, 90.2 DBU, $0 at list). Top 3 components: Generation LLM $37.32, Chat endpoint $24.64, App $19.50. LLM share of list cost is about 36%. Direct components are $89.69 of $113.76; allocated (warehouse, VS, unlabelled LLM) are $24.07 of it.

### Job runs and pipeline updates (per run)

| Day (UTC) | Job runs (job_run_id, list $) | SDP updates | Lakebase sync updates |
|---|---|---|---|
| 2026-11-24 | 4 runs, $0.37 (`1038287240919742`) + $0.12 + $0.15 + $0.18 | 9, $0.72 | 6, $0.19 |
| 2026-11-25 | 4 runs, $0.43 + $0.43 + $0.28 + $0.08 | 6, $0.46 | 3, $0.09 |
| 2026-11-26 (partial) | 7 runs, $0.06 to $0.32 | 5, $0.40 | 3, $0.08 |

The COST_2B run `1038287240919742` costs $0.3711, matching COST_2B's $0.371.

### Cost per appeal by day (view output)

| Day (UTC) | Appeals in `appeals_output` | Fully loaded $ | Variable $ | Fixed $ | Generation LLM $ | Fully loaded $/appeal | Variable $/appeal |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-11-24 | 0 | 39.40 | 18.16 | 20.98 | 12.45 | NULL | NULL |
| 2026-11-25 | 0 | 50.29 | 18.54 | 31.66 | 12.46 | NULL | NULL |
| 2026-11-26 (partial) | 180 | 24.07 | 17.97 | 6.01 | 12.41 | 0.1337 | 0.0998 |

Why 11-24 and 11-25 show no appeals: a clean-state rerun overwrote the table. Delta history (`DESCRIBE HISTORY appeals_output`, `numTargetRowsInserted`) shows **180 rows inserted on each of the three days**, so the generation volume was 180 per day. Using those history counts, the per-appeal figures would be:

| Day | Fully loaded $/appeal at 180 (history count) | Note |
|---|---:|---|
| 2026-11-24 | 0.219 | includes build-day ad hoc usage (more fixed uptime, less steady state) |
| 2026-11-25 | 0.279 | first complete 24h day; compare with the 180/day projection (0.276) |
| 2026-11-26 | 0.134 | partial day (billing to 05:30 UTC): fixed under-counted |

2026-11-26 is partial, so its fully loaded figure is not comparable. Variable cost per appeal is stable at ~$0.10 on the full-generation day.

### Cost at your volume (illustrative)

Fixed own $24.94/day (2026-11-25) and shared VS $6.72/day. Variable $0.0998/appeal (measured, 2026-11-26, 180 appeals). Illustrative: measured prototype run-rates at list price; production sizing and contracted rates will differ.

| Appeals/day | Fixed own $/appeal | Fixed shared VS $/appeal | Variable $/appeal | Total own $/appeal | Total incl. shared VS $/appeal |
|---:|---:|---:|---:|---:|---:|
| 60 | 0.4157 | 0.1120 | 0.0998 | 0.5156 | 0.6276 |
| 150 | 0.1663 | 0.0448 | 0.0998 | 0.2661 | 0.3109 |
| 180 | 0.1386 | 0.0373 | 0.0998 | 0.2384 | 0.2757 |
| 300 | 0.0831 | 0.0224 | 0.0998 | 0.1830 | 0.2054 |
| 600 | 0.0416 | 0.0112 | 0.0998 | 0.1414 | 0.1526 |

### Cross-check against COST_2B

| Item | COST_2B | This view | Difference and reason |
|---|---:|---:|---|
| LLM generation $/appeal | 0.069 | 0.0689 (12.41 ÷ 180) | Matches. Same 0.988 DBU/appeal at $0.07/DBU. |
| Grounding $/appeal | 0.0056 (0.335 ÷ 60) | 0 (2026-11-26) | Digests were fully cached on 11-26; COST_2B ran a cold cache. |
| Warehouse $/appeal | 0.0285 (1.71 ÷ 60) | 0.0213 (3.84 ÷ 180) | Measured from job statement minutes (0.076 min/appeal) rather than a 6.1-min estimate. |
| Job + SDP + Lakebase sync $/appeal | 0.0100 | 0.0096 | Close. |
| Variable $/appeal (total) | ~0.11 | 0.0998 | Explained by the grounding cache and the warehouse share. |
| Fixed own $/day | 24.4 | 24.94 (11-25) | Chat $13.44 + app $11.40 + Lakebase ~$0.10. COST_2B used the same run-rates. |
| Fixed incl. shared VS $/day | 31.1 | 31.66 (11-25) | VS $6.72. |
| Fully loaded $/appeal at 60/day, own | 0.51 | 0.5156 | Matches. |
| Fully loaded $/appeal at 60/day, incl. shared VS | 0.62 | 0.6276 | Matches. |

Lakebase price: the list price for `ENTERPRISE_DATABASE_SERVERLESS_COMPUTE` is $0.52 by default but $0.26 effective from 2026-07-01. The view uses the effective list price, which is what COST_2B used.

## Method (the dashboard's Method page carries the same text)

- **Sources**: `system.billing.usage` for this workspace only, joined to `system.billing.list_prices` (`pricing.effective_list.default`, time-correct on usage start). List price only: no discounts and no committed-use rates.
- **Direct**: the billing record carries a build-owned ID (job_id, dlt_pipeline_id, app_name, endpoint_name, Lakebase project_id, Genie agent_id), or the foundation-model call is tagged with this build's warehouse.
- **Allocated**: a shared resource. The SQL warehouse is uptime-billed and shared, so only job-attributed statement minutes × 24 DBU/h are charged (COST_2B's rule). Idle uptime and other users' statements are not allocated. The VS endpoint is shared with an earlier build, so 100% of its uptime from 2026-11-24 is shown as an upper bound.
- **Unlabelled LLM** (chat per-request tokens and the genai_evaluate judge): foundation-model rows with no caller tag. Classed as allocated/other. They may include other workspace users of the same FM endpoints. Billing does not split them by caller.
- **Variable vs fixed**: variable scales with appeals (generation, grounding, job, job warehouse share, SDP, Lakebase sync). Fixed is always-on uptime (app, chat endpoint, Lakebase compute and storage, VS endpoint). Other is Genie per-question usage and unlabelled LLM.
- **Reading cost per appeal**: fixed cost is spread over volume, so cost per appeal falls as volume rises. Variable cost per appeal stays at about $0.10.

## Exclusions

- Other builds in this workspace: their endpoints (including `appeals-chat-agent-endpoint`, about 9,282 DBU since 2026-10-25), apps, jobs, Genie spaces (including `01f1dec4…`), Lakebase projects and VS indexes.
- Genie Code (`GENIE_CODE`) and `GENIE_ONE` usage, which are workspace-wide.
- Other warehouses, their statements and idle warehouse uptime.
- `ai_parse_document` calls, networking, storage and predictive-optimization usage.
- VS sync pipeline `d3859637…` (0.27 DBU on 11-24, not mapped to this index).
- Usage before 2026-11-24. The view starts there because that is the first day with metered build resources.

## Caveats

1. **Billing lag.** Complete through 2026-11-25 (UTC). 2026-11-26 is partial (billing to 05:30 UTC). Billing can lag a few hours.
2. **Appeal counts.** `appeals_output` holds only the current table state, so 11-24 and 11-25 have no appeals. Delta history shows 180 per day. The per-day appeal counts in the view should be read with that in mind.
3. **Warehouse allocation** is an estimate: 24 DBU/h × job statement minutes, not billed uptime. The warehouse is 94, 46 and 42 DBU/day in total; the job share is 2.3, 5.6 and 5.5 DBU/day.
4. **VS** is an upper bound (100% of a shared endpoint).
5. **Partial day**: fixed cost on 2026-11-26 is under-counted until billing closes.
6. **List price**, not contracted rates. Fixed run-rate is from one complete day (2026-11-25). Production sizing will change the fixed base.
7. Views were created in `appeals_hackathon_catalog.fe_bar_appeals`. No grants, sharing, bundle or job changes.
