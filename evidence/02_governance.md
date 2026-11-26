# 02 Governance evidence (FE Bar, fe_bar_appeals)

Generated 2026-11-24 10:20 UTC by genie/../governance build (agent D). Read-only queries, except the tag and cost scripts run earlier. Synthetic data; prototype.

## 1. Column tags (information_schema.column_tags)

Keys: `phi` (true) and `phi_type` (name | dob | mrn | member_id | claim_id). Applied by `governance/01_phi_tags.sql`.

| table_name | column_name | tag_name | tag_value |
|---|---|---|---|
| appeals_output | patient_name | phi | true |
| appeals_output | patient_name | phi_type | name |
| bronze_claims | CLAIMPOLICYNUMBER | phi | true |
| bronze_claims | CLAIMPOLICYNUMBER | phi_type | member_id |
| bronze_claims | CLAIM_NUMBER | phi | true |
| bronze_claims | CLAIM_NUMBER | phi_type | claim_id |
| bronze_claims | HEALTH_PLAN_ID | phi | true |
| bronze_claims | HEALTH_PLAN_ID | phi_type | member_id |
| bronze_claims | MEDICAL_RECORD_NUMBER | phi | true |
| bronze_claims | MEDICAL_RECORD_NUMBER | phi_type | mrn |
| bronze_claims | PATIENT_BIRTHDATE | phi | true |
| bronze_claims | PATIENT_BIRTHDATE | phi_type | dob |
| bronze_claims | PATIENT_NAME | phi | true |
| bronze_claims | PATIENT_NAME | phi_type | name |
| bronze_clinical_notes | PATIENT_NAME | phi | true |
| bronze_clinical_notes | PATIENT_NAME | phi_type | name |
| data_sheet_facts | claim_number | phi | true |
| data_sheet_facts | claim_number | phi_type | claim_id |
| data_sheet_facts | dob_text | phi | true |
| data_sheet_facts | dob_text | phi_type | dob |
| data_sheet_facts | member_id | phi | true |
| data_sheet_facts | member_id | phi_type | member_id |
| data_sheet_facts | patient_name | phi | true |
| data_sheet_facts | patient_name | phi_type | name |
| encounter_grounding | claim_number | phi | true |
| encounter_grounding | claim_number | phi_type | claim_id |
| encounter_grounding | dob | phi | true |
| encounter_grounding | dob | phi_type | dob |
| encounter_grounding | member_id | phi | true |
| encounter_grounding | member_id | phi_type | member_id |
| encounter_grounding | patient_name | phi | true |
| encounter_grounding | patient_name | phi_type | name |
| gold_denial_worklist | patient_name | phi | true |
| gold_denial_worklist | patient_name | phi_type | name |
| medical_records | PATIENT_NAME | phi | true |
| medical_records | PATIENT_NAME | phi_type | name |
| mednecessity_ai_agent | CLAIMPOLICYNUMBER | phi | true |
| mednecessity_ai_agent | CLAIMPOLICYNUMBER | phi_type | member_id |
| mednecessity_ai_agent | CLAIM_NUMBER | phi | true |
| mednecessity_ai_agent | CLAIM_NUMBER | phi_type | claim_id |
| mednecessity_ai_agent | HEALTH_PLAN_ID | phi | true |
| mednecessity_ai_agent | HEALTH_PLAN_ID | phi_type | member_id |
| mednecessity_ai_agent | MEDICAL_RECORD_NUMBER | phi | true |
| mednecessity_ai_agent | MEDICAL_RECORD_NUMBER | phi_type | mrn |
| mednecessity_ai_agent | PATIENT_BIRTHDATE | phi | true |
| mednecessity_ai_agent | PATIENT_BIRTHDATE | phi_type | dob |
| mednecessity_ai_agent | PATIENT_NAME | phi | true |
| mednecessity_ai_agent | PATIENT_NAME | phi_type | name |
| silver_claim_lines | CLAIMPOLICYNUMBER | phi | true |
| silver_claim_lines | CLAIMPOLICYNUMBER | phi_type | member_id |
| silver_claim_lines | CLAIM_NUMBER | phi | true |
| silver_claim_lines | CLAIM_NUMBER | phi_type | claim_id |
| silver_claim_lines | HEALTH_PLAN_ID | phi | true |
| silver_claim_lines | HEALTH_PLAN_ID | phi_type | member_id |
| silver_claim_lines | MEDICAL_RECORD_NUMBER | phi | true |
| silver_claim_lines | MEDICAL_RECORD_NUMBER | phi_type | mrn |
| silver_claim_lines | PATIENT_BIRTHDATE | phi | true |
| silver_claim_lines | PATIENT_BIRTHDATE | phi_type | dob |
| silver_claim_lines | PATIENT_NAME | phi | true |
| silver_claim_lines | PATIENT_NAME | phi_type | name |
| silver_clinical_notes | PATIENT_NAME | phi | true |
| silver_clinical_notes | PATIENT_NAME | phi_type | name |
| worklist_serving | patient_name | phi | true |
| worklist_serving | patient_name | phi_type | name |

## 2. Table tags (information_schema.table_tags)

`synthetic=true` on all base and output tables. Deviation: the workspace tag policy for `data_classification` allows only `u-nnpi`, `cui`, `pii`, so `synthetic` is used as the key. The policy was not changed.

| table_name | tag_name | tag_value |
|---|---|---|
| appeals_chat_agent_payload | product | ai-gateway |
| appeals_output | synthetic | true |
| bronze_claims | synthetic | true |
| bronze_clinical_notes | synthetic | true |
| cost_assumptions | synthetic | true |
| data_sheet_facts | synthetic | true |
| denial_strategy | synthetic | true |
| encounter_grounding | synthetic | true |
| eval_case_labels | synthetic | true |
| gold_denial_worklist | synthetic | true |
| med_nec_criteria | synthetic | true |
| medical_records | synthetic | true |
| mednecessity_ai_agent | synthetic | true |
| mpfs_indicator_descriptors | synthetic | true |
| mpfs_indicator_listing | synthetic | true |
| review_state_uc | synthetic | true |
| silver_claim_lines | synthetic | true |
| silver_clinical_notes | synthetic | true |
| worklist_serving | synthetic | true |

## 3. Current SHOW GRANTS on the schema (read-only; principals redacted)

Snapshot at generation time. The schema-level grant row `USE SCHEMA` to a group ID appeared after the first snapshot. Agent D ran no GRANT or REVOKE; the grant's origin is unconfirmed and needs review by the orchestrator. Individual user principals are redacted.

| Principal | ActionType | ObjectType | ObjectKey |
|---|---|---|---|
| <user-redacted> | ALL PRIVILEGES | CATALOG | appeals_hackathon_catalog |
| <user-redacted> | EXTERNAL USE SCHEMA | CATALOG | appeals_hackathon_catalog |
| <user-redacted> | MANAGE | CATALOG | appeals_hackathon_catalog |
| <user-redacted> | READ METADATA | CATALOG | appeals_hackathon_catalog |
| 852bd824-1020-495c-a7bd-a8a936f2d21b | READ METADATA | METASTORE | metastore_aws_us_east_1 |
| 059b0419-b956-41e1-a788-e5104b645dc9 | USE SCHEMA | SCHEMA | appeals_hackathon_catalog.fe_bar_appeals |
| 29d3b98e-b968-4882-b54b-ae42cafd9cb6 | READ METADATA | METASTORE | metastore_aws_us_east_1 |
| 22204953-12c2-4c38-b92b-f1ae7655e921 | READ METADATA | METASTORE | metastore_aws_us_east_1 |
| account users | READ METADATA | METASTORE | metastore_aws_us_east_1 |
| <user-redacted> | ALL PRIVILEGES | CATALOG | appeals_hackathon_catalog |
| <user-redacted> | MANAGE | CATALOG | appeals_hackathon_catalog |
| <user-redacted> | READ METADATA | METASTORE | metastore_aws_us_east_1 |

## 4. Proposed reviewer grants: `governance/02_reviewer_grants.sql`

Status: **PENDING, NOT EXECUTED.** Placeholder group `fe-bar-appeals-reviewers`. ADDENDUM 3: the workspace-level group exists, but UC GRANTs need an account-level group, and workspace ACLs (app CAN_USE, Genie CAN_RUN) await Naveen's approval. Scope: USE CATALOG and USE SCHEMA; SELECT on gold_denial_worklist, appeals_output, worklist_serving and the appeals_metrics view; READ VOLUME on appeal_pdfs; EXECUTE on get_appeal, get_encounter, mpfs_lookup, descriptor_lookup. Nothing on bronze, landing or eval labels.

## 5. Lineage (system.access.table_lineage, last 30 days, fe_bar_appeals to fe_bar_appeals, table level)

Source: `governance/03_lineage.sql`. Pipeline edges from bronze to gold, grounding, appeals_output, worklist_serving, and review_state_uc into the metric view appear once system lineage is written. Lineage latency is minutes to hours, so an empty hop at generation time means lag, not absence.

| source_table_full_name | target_table_full_name | edge_events | last_seen |
|---|---|---|---|
| appeals_hackathon_catalog.fe_bar_appeals.appeals_output | appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics | 66 | 2026-11-24T10:10:51.741Z |
| appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist | appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics | 66 | 2026-11-24T10:10:51.741Z |
| appeals_hackathon_catalog.fe_bar_appeals.review_state_uc | appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics | 47 | 2026-11-24T10:10:51.741Z |
| appeals_hackathon_catalog.fe_bar_appeals.appeals_output | appeals_hackathon_catalog.fe_bar_appeals.appeals_output | 2 | 2026-11-24T10:03:59.498Z |
| appeals_hackathon_catalog.fe_bar_appeals.data_sheet_facts | appeals_hackathon_catalog.fe_bar_appeals.appeals_output | 3 | 2026-11-24T10:06:40.310Z |
| appeals_hackathon_catalog.fe_bar_appeals.encounter_grounding | appeals_hackathon_catalog.fe_bar_appeals.appeals_output | 2 | 2026-11-24T10:03:59.498Z |
| appeals_hackathon_catalog.fe_bar_appeals.encounter_grounding | appeals_hackathon_catalog.fe_bar_appeals.data_sheet_facts | 2 | 2026-11-24T09:49:39.875Z |
| appeals_hackathon_catalog.fe_bar_appeals.med_nec_criteria | appeals_hackathon_catalog.fe_bar_appeals.data_sheet_facts | 2 | 2026-11-24T09:49:39.875Z |
| appeals_hackathon_catalog.fe_bar_appeals.denial_strategy | appeals_hackathon_catalog.fe_bar_appeals.encounter_grounding | 6 | 2026-11-24T09:48:59.840Z |
| appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist | appeals_hackathon_catalog.fe_bar_appeals.encounter_grounding | 6 | 2026-11-24T09:48:59.840Z |
| appeals_hackathon_catalog.fe_bar_appeals.med_nec_criteria | appeals_hackathon_catalog.fe_bar_appeals.encounter_grounding | 6 | 2026-11-24T09:48:59.840Z |
| appeals_hackathon_catalog.fe_bar_appeals.medical_records | appeals_hackathon_catalog.fe_bar_appeals.encounter_grounding | 6 | 2026-11-24T09:48:59.840Z |
| appeals_hackathon_catalog.fe_bar_appeals.mednecessity_ai_agent | appeals_hackathon_catalog.fe_bar_appeals.encounter_grounding | 6 | 2026-11-24T09:48:59.840Z |
| appeals_hackathon_catalog.fe_bar_appeals.mpfs_indicator_descriptors | appeals_hackathon_catalog.fe_bar_appeals.encounter_grounding | 6 | 2026-11-24T09:48:59.840Z |
| appeals_hackathon_catalog.fe_bar_appeals.mpfs_indicator_listing | appeals_hackathon_catalog.fe_bar_appeals.encounter_grounding | 6 | 2026-11-24T09:48:59.840Z |
| appeals_hackathon_catalog.fe_bar_appeals.mednecessity_ai_agent | appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist | 2 | 2026-11-24T09:40:04.916Z |
| appeals_hackathon_catalog.fe_bar_appeals.med_nec_criteria | appeals_hackathon_catalog.fe_bar_appeals.med_nec_criteria_index | 1 | 2026-11-24T09:14:23.065Z |
| appeals_hackathon_catalog.fe_bar_appeals.silver_clinical_notes | appeals_hackathon_catalog.fe_bar_appeals.medical_records | 2 | 2026-11-24T09:40:00.554Z |
| appeals_hackathon_catalog.fe_bar_appeals.silver_claim_lines | appeals_hackathon_catalog.fe_bar_appeals.mednecessity_ai_agent | 2 | 2026-11-24T09:40:01.669Z |
| appeals_hackathon_catalog.fe_bar_appeals.bronze_claims | appeals_hackathon_catalog.fe_bar_appeals.silver_claim_lines | 4 | 2026-11-24T09:39:56.650Z |
| appeals_hackathon_catalog.fe_bar_appeals.bronze_clinical_notes | appeals_hackathon_catalog.fe_bar_appeals.silver_clinical_notes | 4 | 2026-11-24T09:39:56.331Z |
| appeals_hackathon_catalog.fe_bar_appeals.appeals_output | appeals_hackathon_catalog.fe_bar_appeals.worklist_serving | 6 | 2026-11-24T10:01:38.028Z |
| appeals_hackathon_catalog.fe_bar_appeals.data_sheet_facts | appeals_hackathon_catalog.fe_bar_appeals.worklist_serving | 2 | 2026-11-24T10:01:38.028Z |
| appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist | appeals_hackathon_catalog.fe_bar_appeals.worklist_serving | 6 | 2026-11-24T10:01:38.028Z |

## Lineage status

- Recorded: bronze_claims and bronze_clinical_notes, to silver, to gold (`gold_denial_worklist`), to `encounter_grounding`, to `appeals_output`, to `worklist_serving`, plus review_state_uc and appeals_output into `appeals_metrics`.
- Not yet recorded at generation time: `eval_summary` and `eval_results` (writes by the evaluation job appear as NULL-source entries only) and the review_state_uc refresh from Lakebase (recorded as `fe_bar_appeals_lakebase.public.review_state` into review_state_uc).
- Re-check the query in `governance/03_lineage.sql` after the final run.

## Workspace ACL: Genie space (applied 2026-11-24 with Naveen's approval)
Genie space `01f1e7ec913217158b231c3e2f18fa20` ("FE Bar – Medical Necessity Appeals"), additive `permissions update`:

| Principal | Permission |
|---|---|
| fe-bar-appeals-reviewers (workspace group) | CAN_RUN |
| app service principal (fe-bar-appeals-app) | CAN_RUN |
| space owner | CAN_MANAGE |
| admins | CAN_MANAGE |

Note: `fe-bar-appeals-reviewers` is a workspace-level group. UC table/volume/function grants (`governance/02_reviewer_grants.sql`)
need an account-level group and remain pending. (Current as of 2026-11-25: inside the app, Genie now runs as the app service principal — see `governance/04_app_sp_genie_grants.sql`; in the Genie UI itself it still runs as the user, so a reviewer there needs UC SELECT on the
space's tables to get answers.

## Workspace ACL: app (applied 2026-11-24 with Naveen's approval)
`fe-bar-appeals-app`: `fe-bar-appeals-reviewers` → CAN_USE (additive `apps update-permissions`). Data access inside the app stays
OBO (user's UC grants) for SQL/files/chat; Genie tab runs as the app SP (scope issue, decision 2026-11-25); worklist + review actions go through the app SP to Lakebase (see lakebase/AUTH.md).

## Least-privilege cleanup (2026-11-25, Naveen approved)
Revoked `EXECUTE` on `get_appeal`, `get_encounter`, `mpfs_lookup`, `descriptor_lookup` from `account users` (granted by an
earlier bootstrap version; `pipeline/00_bootstrap.py` no longer grants). `SHOW GRANTS` afterwards: no EXECUTE for `account users`
(only the metastore-wide READ METADATA inherited from the metastore). Chat endpoint re-tested after the revoke: still answers.
