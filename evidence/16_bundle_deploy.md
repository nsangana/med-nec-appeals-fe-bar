# 16. Bundle deploy: dashboard, Genie, Lakebase, schema, volumes, model, endpoint bound; cost_views task; runbook

**Scope.** Make the FE Bar build deployable from the repo: bind every live component that a bundle can own with no
recreate, delete or material change, add the cost-view task, and write a single runbook. Workspace
`fevm-appeals-hackathon`, profile `fevm-appeals-hackathon`, bundle `med-nec-appeals-fe-bar`, CLI v1.21.0.
Date: 2026-11-26 (UTC). Synthetic data. No grants, sharing or permission changes were made. Nothing was committed.

## Result in one table

| Item | Result |
|---|---|
| Bundle validate | OK (1 warning, see "Warnings") |
| Plan before any change | 0 add, 0 change, 0 delete, 2 unchanged (the job and the SDP pipeline) |
| Plan before deploy | 0 add, 2 change (dashboard, job), 0 delete, 15 unchanged. No recreate. |
| Deploy | 0 created, 2 changed, 0 deleted, 15 unchanged |
| Plan after deploy | 0 add, 0 change, 0 delete, 17 unchanged |
| `cost_views` task (`bundle run --only cost_views`) | SUCCESS, run `37219191093878` |
| Dashboard datasets (2 of 7 checked) | Both return rows from the new views (ds_daily, ds_cpa) |
| Genie space | Byte-identical before and after deploy (same etag and update time) |
| Runbook | `scripts/deploy_all.sh`: `bash -n` OK; `--dry-run` prints 10 steps and runs nothing. NOT executed against the workspace. |

## Inventory: in bundle / via runbook / manual

| Component | Live object | Where it lives now | Why |
|---|---|---|---|
| Dashboard "Appeals Automation Agent Insights" | `01f1e968adcd1e3b93920b557b986458` | **IN BUNDLE** `resources/fe_bar_appeals.dashboard.yml` (bound) | Bundle dashboard resource. `dataset_catalog`/`dataset_schema` set from variables; queries use bare names. Its draft was aligned to live (see below). |
| Genie space "FE Bar – Medical Necessity Appeals" | `01f1e7ec913217158b231c3e2f18fa20` | **IN BUNDLE** `resources/fe_bar_appeals.genie.yml` + `genie/appeals_metrics.geniespace.json` (exported from live) | Plan is a no-op. `prevent_destroy`. No `permissions` block, so the live ACL (app SP and reviewers CAN_RUN, owner CAN_MANAGE) is untouched. |
| Schema `appeals_hackathon_catalog.fe_bar_appeals` | UC schema | **IN BUNDLE** `resources/fe_bar_appeals.schema.yml` (bound) | Plan no-op. The live `owner: root` schema property is declared so the plan does not drop it. No grants. |
| Volumes `landing`, `raw_references`, `appeal_pdfs` | UC managed volumes | **IN BUNDLE** `resources/fe_bar_appeals.volumes.yml` (bound) | Plan no-op. `prevent_destroy`. |
| Job `fe-bar-appeals-job` | `211997391364769` | IN BUNDLE (existing) + new task `cost_views` | Plan: update for `cost_views` only. |
| SDP pipeline `fe-bar-appeals-sdp` | `4873b47b-47a7-4081-97c0-7cdf018c71a1` | IN BUNDLE (existing) | Plan no-op. |
| Lakebase project | `projects/fe-bar-appeals-lakebase` | **IN BUNDLE** `resources/fe_bar_appeals.lakebase.yml` (`postgres_projects`, bound) | Plan no-op. Autoscaling project (0.5 CU, 300 s suspend, PG 17). |
| Lakebase branch | `projects/fe-bar-appeals-lakebase/branches/production` | IN BUNDLE (`postgres_branches`, bound) | Plan no-op. |
| Lakebase endpoint | `.../endpoints/primary` | IN BUNDLE (`postgres_endpoints`, bound) | Plan no-op. |
| Lakebase database | `.../databases/appeals` | IN BUNDLE (`postgres_databases`, bound) | Plan no-op. Owner role is not declared (warning below). |
| Lakebase UC catalog | `catalogs/fe_bar_appeals_lakebase` | IN BUNDLE (`postgres_catalogs`, bound) | Plan no-op. |
| Synced table `fe_bar_appeals.worklist_serving` | `synced_tables/fe_bar_appeals_lakebase.fe_bar_appeals.worklist_serving` | IN BUNDLE (`postgres_synced_tables`, bound) | Plan no-op. `existing_pipeline_id` = the live pipeline `0245f1ce-…`, so the sync is not re-created. |
| Registered model `appeals_chat_agent` | UC model | IN BUNDLE (`registered_models`, bound) | Plan no-op. Versions and aliases are owned by `agent/build_and_deploy.py`. No grants. |
| VS index `med_nec_criteria_index` | on `appeals-vs-endpoint` | IN BUNDLE (`vector_search_indexes`, bound) | Plan no-op. The endpoint is shared with an earlier build, so it is NOT declared. |
| Chat endpoint `fe-bar-appeals-chat` | `fe-bar-appeals-chat` | IN BUNDLE, last and most sensitive (`model_serving_endpoints`, bound) | Plan is a strict no-op: the only `skip` fields are the derived `served_model_name` entries, `description` and `route_optimized`. Config matches live (config_version 5, two served entities, 100/0 traffic, AI Gateway inference table). |
| App `fe-bar-appeals-app` | `059b0419-b956-41e1-a788-e5104b645dc9` | **RUNBOOK** (`app/app_resources.json` + `scripts/deploy_all.sh` step 8) | NOT in the bundle. (1) `app/databricks.yml` already defines this app as its own bundle, so two bundles would own one app. (2) The live app was deployed from a manually imported workspace folder; a bundle would sync `app/` to its own path and redeploy. (3) Scope or resource changes force user re-consent. The runbook sends the full definition, since `apps update` is a full replacement. |
| Lakebase owner role `naveen-sangana`; app SP role `dbrx-apps-059b0419-…` | Postgres roles | MANUAL | Personal identity, and the SP role is created by the app's postgres binding. Not declared. |
| Lakebase grants (`app_grants.sql`) | Postgres | RUNBOOK (not run by the bundle) | Grants are out of scope for the bundle. |
| UC grants and tags (`governance/01`, `04`, `05`) | UC | RUNBOOK | No grants in the bundle. `02_reviewer_grants.sql` is not run (needs an account-level group). |
| Metric view `appeals_metrics` | UC view | RUNBOOK (`genie/00`, `genie/01` SQL) | The metric view is SQL, and the Genie space is bundle-owned. |
| Cost views (`cost_attribution_daily`, `cost_per_appeal_daily`, `cost_at_volume`) | UC views | IN JOB (`cost_views` task) | `CREATE OR REPLACE VIEW` only. |
| Chat-tool UC functions (`get_appeal`, `get_encounter`, `mpfs_lookup`, `descriptor_lookup`) | UC functions | NOT TOUCHED | Never `CREATE OR REPLACE` behind a deployed agent endpoint. |
| VS endpoint `appeals-vs-endpoint` | shared | MANUAL | Shared with an earlier build. |
| Reviewer group `fe-bar-appeals-reviewers` | workspace group | MANUAL | UC grants need an account-level group. |
| Lakebase sync pipeline `0245f1ce-…` | DLT pipeline | Managed by the synced table | Referenced through `existing_pipeline_id`, not declared. |

## Bindings (bundle deployment bind, then plan)

Each bind writes local state only. Keys are the resource keys in `resources/*.yml`.

| Key | Live ID bound |
|---|---|
| `fe_bar_appeals_dashboard` | `01f1e968adcd1e3b93920b557b986458` |
| `fe_bar_appeals_genie` | `01f1e7ec913217158b231c3e2f18fa20` |
| `fe_bar_appeals_schema` | `appeals_hackathon_catalog.fe_bar_appeals` |
| `fe_bar_landing` / `fe_bar_raw_references` / `fe_bar_appeal_pdfs` | `appeals_hackathon_catalog.fe_bar_appeals.{landing,raw_references,appeal_pdfs}` |
| `fe_bar_lakebase_project` | `projects/fe-bar-appeals-lakebase` |
| `fe_bar_lakebase_production` | `projects/fe-bar-appeals-lakebase/branches/production` |
| `fe_bar_lakebase_primary` | `projects/fe-bar-appeals-lakebase/branches/production/endpoints/primary` |
| `fe_bar_lakebase_appeals_db` | `projects/fe-bar-appeals-lakebase/branches/production/databases/appeals` |
| `fe_bar_lakebase_catalog` | `catalogs/fe_bar_appeals_lakebase` |
| `fe_bar_worklist_serving` | `synced_tables/fe_bar_appeals_lakebase.fe_bar_appeals.worklist_serving` |
| `fe_bar_chat_agent_model` | `appeals_hackathon_catalog.fe_bar_appeals.appeals_chat_agent` |
| `fe_bar_criteria_index` | `appeals_hackathon_catalog.fe_bar_appeals.med_nec_criteria_index` |
| `fe_bar_chat_endpoint` | `fe-bar-appeals-chat` |

The existing resources `fe_bar_appeals_job` and `fe_bar_appeals_sdp` keep their IDs from before.

## Alignment decisions (where the live object differed from the repo)

1. **Dashboard draft.** The repo JSON did not match the live draft. The live draft had edited the table widget at `layout[11]`: it added query `orders`, `rowOrder`, `spec.data` and frame title and description, and it sets `catalog` and `schema` on each dataset. Deploying the old repo file would have overwritten those UI edits. I replaced `dashboards/appeals_automation_agent_insights.lvdash.json` with the live draft. The dataset queries are unchanged and still use bare table names. After that, the plan's `serialized_dashboard` sha matched the remote.
2. **Dashboard publish (disclosed).** The Dashboard resource has no option to skip publishing, so every deploy publishes the current draft. Before this deploy the published revision was 07:13 and the draft was 07:15, so **the deploy published the 07:15 draft edits**, and the `/published` revision is now 07:33 UTC. The draft equals the content the UI already showed. Viewer permissions are unchanged.
3. **Schema `owner` property.** The live schema has the property `owner: root`. The plan wanted to drop it, so the YAML declares it to match live.
4. **`cost_views` dependencies.** The spec said "depends on bootstrap". The views read `appeals_output`, which exists only after `generate_appeals`, so the task depends on `bootstrap` and `generate_appeals`. On a clean deploy it would otherwise fail.
5. **Genie.** The live space is unchanged. The export is in `genie/appeals_metrics.geniespace.json`, and `genie/build_space.py` is superseded.

## Plan outputs

### Baseline (before any change)

```
Plan: 0 to add, 0 to change, 0 to delete, 2 unchanged
```

### Final plan before deploy (guard: no `delete` or `recreate` actions; checked by script)

```
Warning: required field "role" is not set
  at resources.postgres_databases.fe_bar_lakebase_appeals_db
  in resources/fe_bar_appeals.lakebase.yml:47:7

update dashboards.fe_bar_appeals_dashboard
update jobs.fe_bar_appeals_job

Plan: 0 to add, 2 to change, 0 to delete, 15 unchanged
```

Machine check of the same plan: `{"resources.dashboards.fe_bar_appeals_dashboard": "update", "resources.jobs.fe_bar_appeals_job": "update"}`, 15 `skip`.

### Plan after deploy

```
Warning: required field "role" is not set
  at resources.postgres_databases.fe_bar_lakebase_appeals_db
  in resources/fe_bar_appeals.lakebase.yml:47:7

Plan: 0 to add, 0 to change, 0 to delete, 17 unchanged
```

## Deploy output

```
Warning: required field "role" is not set
  at resources.postgres_databases.fe_bar_lakebase_appeals_db
  in resources/fe_bar_appeals.lakebase.yml:47:7

Uploading bundle files to /Workspace/Users/<user>/.bundle/med-nec-appeals-fe-bar/default/files...
Updated dashboards.fe_bar_appeals_dashboard
Updated jobs.fe_bar_appeals_job
Files: 63 uploaded, 2 deleted
Resources: 0 created, 2 changed, 0 deleted, 15 unchanged
```

## `cost_views` task (only this task)

```
Warning: required field "role" is not set
  at resources.postgres_databases.fe_bar_lakebase_appeals_db
  in resources/fe_bar_appeals.lakebase.yml:47:7

Run URL: https://fevm-appeals-hackathon.cloud.databricks.com/jobs/211997391364769/runs/37219191093878?o=7474656043998914

2026-11-25 23:33:39 "fe-bar-appeals-job" RUNNING
2026-11-25 23:33:57 "fe-bar-appeals-job" TERMINATED SUCCESS
SQL Task Output:
{}
```

## Dashboard datasets re-run against the new views

Queries are the dashboard's own SQL, with the table names qualified for the check (the dashboard does the same through `dataset_catalog` and `dataset_schema`).

| Dataset | Result |
|---|---|
| `ds_daily` (`cost_attribution_daily`) | Rows returned, for example 2026-11-25 App, Lakebase, Chat endpoint and VS lines (`list_usd` non-null) |
| `ds_cpa` (`cost_per_appeal_daily`) | Rows returned for 2026-11-24 to 2026-11-26 (2026-11-26: 180 appeals, fully loaded $0.2166 per appeal) |

## Chat endpoint and Genie, unchanged

- Chat endpoint: `state` READY, `config_version` 5 (unchanged by this work). Lakebase project 0.5 CU min and max, ACTIVE.
- Genie space: `serialized_space` byte-identical before and after deploy; etag `b39a6cd5ba1d…` unchanged. No benchmark re-run was needed.

## Runbook (`scripts/deploy_all.sh`)

`bash -n`: OK. `--dry-run` output (prints only; nothing executed):

```
== 0. Context
   repo=<repo> profile=fevm-appeals-hackathon warehouse=559faf81d610a2a1 dry_run=1 user=<current user>

== 1. Bundle validate + deploy (first pass)
+ databricks bundle validate -p fevm-appeals-hackathon
+ databricks bundle deploy -p fevm-appeals-hackathon

== 2. Lakebase project, database and DDL
+ bash lakebase/setup_lakebase.sh

== 3. Data layer: full job run (bootstrap, generator, SDP, grounding, appeals, cost_views, lakebase_sync, eval)
   Long-running; the job is PAUSED on its schedule, so this manual run is the only one.
+ databricks bundle run fe_bar_appeals_job -p fevm-appeals-hackathon

== 4. Lakebase synced table, then apply the review_state view
+ bash lakebase/create_synced_table.sh
+ bash lakebase/setup_lakebase.sh

== 5. Governance: PHI tags and column masks (02 is NOT run: needs an account-level group)
+ python3 tools/run_sql.py -f governance/01_phi_tags.sql
+ python3 tools/run_sql.py -f governance/05_column_masks.sql

== 6. Genie metric view, then redeploy so the bundle-managed Genie space sees it
+ python3 tools/run_sql.py -f genie/00_cost_assumptions.sql
+ python3 tools/run_sql.py -f genie/01_appeals_metrics.sql
   The space itself is in the bundle (genie/appeals_metrics.geniespace.json); genie/build_space.py is superseded.
+ databricks bundle deploy -p fevm-appeals-hackathon

== 7. Chat agent: one-time serverless run of agent/build_and_deploy.py (agents.deploy creates the endpoint)
+ databricks workspace mkdirs /Workspace/Users/<current user>/fe-bar-appeals/agent
+ databricks workspace import /Workspace/Users/<current user>/fe-bar-appeals/agent/build_and_deploy --file agent/build_and_deploy.py --format SOURCE --language PYTHON --overwrite
+ databricks jobs submit -p fevm-appeals-hackathon --timeout 60m --json {"run_name":"fe-bar-appeals-agent-deploy","environments":[{"environment_key":"agent","spec":{"client":"2","dependencies":["mlflow[databricks]>=3.1","databricks-agents"]}}],"tasks":[{"task_key":"agent_deploy","environment_key":"agent","notebook_task":{"notebook_path":"/Workspace/Users/<current user>/fe-bar-appeals/agent/build_and_deploy"}}]}
+ databricks bundle deploy -p fevm-appeals-hackathon

== 8. App: workspace import, create if missing, full definition (scopes + resources), deploy
   create fe-bar-appeals-app if missing (apps get check runs for real)
   stage (no node_modules, dist or .env): rsync app/ -> temp dir
+ rsync -a --exclude node_modules --exclude dist --exclude client/dist --exclude .env --exclude .env.* --exclude *.pyc <repo>/app/ <temp dir>/
+ databricks workspace import-dir <temp dir> /Workspace/Users/<current user>/fe-bar-appeals-app -p fevm-appeals-hackathon --overwrite
+ databricks apps update fe-bar-appeals-app -p fevm-appeals-hackathon --json @app/app_resources.json
+ databricks apps start fe-bar-appeals-app -p fevm-appeals-hackathon
+ databricks apps deploy fe-bar-appeals-app -p fevm-appeals-hackathon --source-code-path /Workspace/Users/<current user>/fe-bar-appeals-app
   Bindings: lakebase/APP_GRANTS.md (sql-warehouse, files, postgres, genie-space, serving-endpoint) are in app/app_resources.json.

== 9. Governance 04: app SP SELECT on the 5 Genie objects
+ python3 tools/run_sql.py -f governance/04_app_sp_genie_grants.sql

== 10. Final bundle plan (must show no deletes or recreates)
+ databricks bundle plan -p fevm-appeals-hackathon

== Done
   Runbook complete. Re-run is safe; check the plan output above before any destructive change.
```

Not run against the workspace (by instruction). Each step is idempotent. Known clean-workspace caveats are written in the script header: the chat endpoint needs agent v2 registered, so the first deploy can fail on that one resource; the runbook warns and continues, and the second deploy creates it.

## Warnings and notes

- `required field "role" is not set` on `postgres_databases.fe_bar_lakebase_appeals_db`. The owner role is personal (`naveen-sangana`). It is not declared, and the plan treats the database as no-op. Declaring it would put a personal role id in the repo.
- `bundle validate` also recommended one schema per file. The schema and the volumes are now in separate files (`.schema.yml`, `.volumes.yml`).
- The deploy reported `Files: 63 uploaded, 2 deleted`. Those are files in the bundle's own workspace sync folder (no resources deleted). The deploy summary reports 0 deleted resources.
- A `.databricks/` state directory was updated by the bind and deploy. It is gitignored.

## Files changed

- `resources/fe_bar_appeals.dashboard.yml` (new), `resources/fe_bar_appeals.genie.yml` (new), `resources/fe_bar_appeals.schema.yml` (new), `resources/fe_bar_appeals.volumes.yml` (new), `resources/fe_bar_appeals.lakebase.yml` (new), `resources/fe_bar_appeals.models.yml` (new), `resources/fe_bar_appeals.endpoint.yml` (new)
- `resources/fe_bar_appeals.job.yml` (added the `cost_views` task)
- `dashboards/appeals_automation_agent_insights.lvdash.json` (replaced with the live draft; see decision 1)
- `genie/appeals_metrics.geniespace.json` (new, exported from live)
- `app/app_resources.json` (new; the full app definition for the runbook)
- `scripts/deploy_all.sh` (new runbook)
- `README.md` ("Running it" replaced; "Repo layout" updated)
- `evidence/16_bundle_deploy.md` (this file), `evidence/EVIDENCE.md` (row 21)

## Not done / open

- The app is not in the bundle (decision above). Its redeploy would need the scope re-consent check.
- The chat endpoint and Lakebase are bundle-owned now. Any future config change must go through `bundle plan` first, since a served-entity or traffic edit changes the live agent.
- The dashboard publish happens on every deploy (no switch). Publish only after reviewing the draft.


## Update 2026-11-26 — parameterized bundle
- Default-only resources moved to `targets/default/{lakebase,endpoint,models}.yml`; delete protection for schema/volumes/dashboard/Genie moved to `targets/default/guards.yml` (live-only).
- New `smoke` target (isolated schema) proven end to end and destroyed: see `evidence/17_bundle_clean_run.md`.
- Final live plan: 0 add / 0 change / 0 delete, 17 unchanged.
