# 13 Column masks on PHI (fe_bar_appeals)

Synthetic data, prototype. Applied 2026-11-25 with `governance/05_column_masks.sql` (profile `fevm-appeals-hackathon`, warehouse `559faf81d610a2a1`). Identity for every check below: `naveen.sangana@databricks.com`, a member of workspace group `fe-bar-appeals-reviewers` (id 2120920728538263). No GRANT/REVOKE, no sharing, no job run, no bundle deploy.

## 1. Mask function

```sql
CREATE OR REPLACE FUNCTION appeals_hackathon_catalog.fe_bar_appeals.mask_phi(val STRING)
RETURNS STRING
COMMENT 'PHI column mask (synthetic demo). Returns the real value to members of workspace group fe-bar-appeals-reviewers and to the app service principal 059b0419-b956-41e1-a788-e5104b645dc9 (Genie tab). Everyone else gets ***MASKED***. Not used by the chat tool functions.'
RETURN CASE
  WHEN is_member('fe-bar-appeals-reviewers') THEN val
  WHEN current_user() = '059b0419-b956-41e1-a788-e5104b645dc9' THEN val
  ELSE '***MASKED***'
END;
```

## 2. Masks attached

```sql
ALTER TABLE appeals_hackathon_catalog.fe_bar_appeals.appeals_output ALTER COLUMN patient_name SET MASK appeals_hackathon_catalog.fe_bar_appeals.mask_phi;
ALTER TABLE appeals_hackathon_catalog.fe_bar_appeals.data_sheet_facts ALTER COLUMN patient_name SET MASK appeals_hackathon_catalog.fe_bar_appeals.mask_phi;
ALTER TABLE appeals_hackathon_catalog.fe_bar_appeals.data_sheet_facts ALTER COLUMN member_id SET MASK appeals_hackathon_catalog.fe_bar_appeals.mask_phi;
ALTER TABLE appeals_hackathon_catalog.fe_bar_appeals.data_sheet_facts ALTER COLUMN dob_text SET MASK appeals_hackathon_catalog.fe_bar_appeals.mask_phi;
```

`information_schema.column_masks` after apply:

| table_name | column_name | mask_name |
|---|---|---|
| appeals_output | patient_name | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |
| data_sheet_facts | member_id | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |
| data_sheet_facts | dob_text | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |
| data_sheet_facts | patient_name | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |

## 3. Scope: what is and is not masked, and why

| Object | Column(s) | Masked? | Reason |
|---|---|---|---|
| appeals_output | patient_name | yes | Reviewer-facing managed Delta table. No DOB/member_id columns in this table. |
| data_sheet_facts | patient_name, member_id, dob_text | yes | Managed Delta, written only by `CREATE TABLE IF NOT EXISTS` + `MERGE` (25_data_sheet_facts.sql, 40_render_pdfs.py), so the mask survives job runs. |
| encounter_grounding | patient_name, dob, member_id, claim_number | **no** | `pipeline/20_encounter_grounding.sql` line 93 does `CREATE OR REPLACE TABLE` on every job run, which would silently drop the mask. A `dob` timestamp would also need a separate mask. Also read by the chat tool `get_encounter`. |
| worklist_serving | patient_name, etc. | **no** | Source of the Lakebase synced table. Masks or filters there can break the sync. |
| gold_denial_worklist, streaming tables, MVs | patient_name | **no** | SDP-managed by the pipeline. |
| eval tables | - | **no** | Out of scope. |
| appeals_output / data_sheet_facts | claim_number, notes_verbatim | **no** | Not in the agreed PHI list. Claim numbers are needed to work an appeal. Free-text notes can contain PHI. Flagged for a compliance decision. |
| get_appeal, get_encounter, mpfs_lookup, descriptor_lookup | - | functions untouched | Never replaced. Verified by the chat endpoint still answering (section 6). |

## 4. Before / after (as Naveen, member)

Before (no masks):
```
| FACILITY_ID | PATIENT_CONTROL_NUMBER | ENCOUNTER_NBR | patient_name |
| 101 | 770000001 | 50000001 | Elena Marquez |
data_sheet_facts: patient_name=Elena Marquez, member_id=BCBSAZ-PPO-4471, dob_text=1962-03-14
```

After:
```
| FACILITY_ID | PATIENT_CONTROL_NUMBER | ENCOUNTER_NBR | patient_name |
| 101 | 770000001 | 50000001 | Elena Marquez |

appeals_output: n_real_names=180, distinct_names=164, n_masked=0
data_sheet_facts: n=450, masked_names=0, masked_member=0
```

Row counts are unchanged (appeals_output 180, data_sheet_facts 450).

## 5. Test results

**(a) Member path (Naveen): PASS.** The hero row returns the real name. Zero `***MASKED***` values in appeals_output or data_sheet_facts.

**(b) Non-member path: PARTIAL, logic only.** No identity outside the group could be exercised, because that needs a grant or a credential for another principal, and no new grants were allowed. What was checked:
```
| member_reviewers | member_fake | masked_branch_value |
| true | false | ***MASKED*** |
```
`is_member('fe-bar-appeals-app-nonexistent-group')` returns false and the non-member branch returns `***MASKED***`. The same CASE branch runs for a real non-member, but this is not an end-to-end test.

Probe of the MERGE path (scratch table `zz_mask_probe`, dropped afterwards): a MERGE into a masked target updated 1 row, and the member read returned the real value. This shows the job's MERGEs into `appeals_output` / `data_sheet_facts` still work.

**(c) Genie benchmarks (run as Naveen through the Genie Conversation API, graded by value containment; `genie/run_benchmarks.py` was not used because it overwrites evidence/07).** All three PASS:
```
B03 | What is the status of the claim for Elena Marquez? | COMPLETED | expected 1 row, all values present | Elena Marquez, BCBS of Arizona, CO50, AT_RISK, 8, 24850.0, WARRANTED
B01 | How much appealable revenue is at deadline risk this week by payer? | COMPLETED | expected 8 rows, all values present | PASS
B04 | What share of appeals were routed to NEEDS REVIEW, and why? | COMPLETED | expected 42 rows, all values present | PASS
```
Caveat: B03 reads `gold_denial_worklist`, which is not masked, so it passes whatever the mask does. The app-SP path was **not** exercised. The Genie tab runs as the app SP (`059b0419-…`), and that identity's credentials are not available here. The SP exemption relies on `current_user()` returning the SP application id. That is the documented behaviour for service principals but was not confirmed by a run.

**(d) Chat endpoint `fe-bar-appeals-chat`: PASS.** Same hero question before and after (keys 101 / 770000001 / 50000001). Both answers return WARRANTED, the procedure, BCBS of Arizona, deadline 2026-12-04 with 8 days remaining, and the top 3 evidence items. The answer contains the patient name, and also the DOB, because `get_encounter` reads the unmasked `encounter_grounding` (see limitations).

**(e) Lakebase sync: PASS (read-only).** `worklist_serving` Delta count 500 and synced count 500, with 0 masked names. Synced-table status `SYNCED_TABLE_ONLINE_NO_PENDING_UPDATE`, pipeline `0245f1ce-9b6c-49c9-88ae-1942576611d7`. The job was not run. Worklist patient names come from `gold_denial_worklist`, which is not masked, and the sync MERGE reads only key and output columns from `appeals_output`, so the sync is unaffected by the mask.

## 6. Job and chat behaviour

- Job compute is serverless for both the SDP pipeline and the Python tasks (`resources/*.yml`). The docs' dedicated-access-mode limit does not apply.
- The job runs as Naveen (member), so its reads of `appeals_output` / `data_sheet_facts` return real values. Generation and grounding behaviour is unchanged by this evidence. The job itself was not run, so it's a reasoned claim plus the MERGE probe.
- Docs check: MERGE is blocked only for policies with nesting, aggregations, windows, limits or non-deterministic functions. The mask has none of these. Verified by the probe above.

## 7. Limitations and open items (read these before calling it "protected")

1. **Definer-rights question on `is_member` (most important, unverified).** The Databricks "Manually apply row filters and column masks" page says: "All filters run with definer's rights except for functions that check user context (for example, the SESSION_USER and IS_ACCOUNT_GROUP_MEMBER functions) which run as the invoker." `is_member` is not named in that list. The table owner is Naveen, who is a group member. If `is_member` were evaluated with the owner's rights, every reader would see real values. The mask would then fail open for reviewers and non-reviewers alike. The `current_user()` branch is user-context and is documented as invoker-evaluated, so it is not affected. Closing this needs a non-member identity to run one SELECT on `appeals_output`. That needs a grant, so it is not done here. **Action: have a non-member run `SELECT patient_name FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_output LIMIT 3` after a grant is approved. Expect `***MASKED***`.**
2. **SP exemption not run as the SP.** See (c). Verify the Genie tab in the app after the next app redeploy and check that names are not masked.
3. **`encounter_grounding` is not masked.** Job task `20_encounter_grounding.sql` does `CREATE OR REPLACE TABLE` on every run and would drop the mask. The chat tool `get_encounter` therefore returns patient_name, DOB and member context to anyone who can call the chat endpoint. **The Databricks-side fix is to change stage 20 to `CREATE TABLE IF NOT EXISTS` + `MERGE`, or re-apply the mask after each rebuild. Either is a pipeline change, not made here.**
4. **Lakebase copies stay unmasked.** `worklist_serving` (synced) and the Postgres `public.review_actions` / `review_state` views carry patient names. Only the app SP reads Postgres, and reviewer access is controlled by app CAN_USE, so the mask does not apply there by design.
5. **Other PHI paths not masked:** the appeal PDFs in volume `appeal_pdfs` (they show patient names), `gold_denial_worklist.patient_name` (SDP-managed), `claim_number` and `notes_verbatim` in `data_sheet_facts`, and `claim_number` / `dob` in `encounter_grounding`.
6. **The pending `governance/02_reviewer_grants.sql` would expose unmasked PHI.** It grants reviewers SELECT on `gold_denial_worklist` and `worklist_serving`, which are not masked. Do not run it as written without a decision on those objects.
7. **Job identity dependency.** Pipeline 40 renders data-sheet PDFs from `data_sheet_facts`. If the job identity ever changes to a non-member, the PDFs would contain `***MASKED***` names. Keep the job's identity in the group or add its SP to the exemption.
8. **Mask function is fixed per the spec.** The group name and SP id are hardcoded. Changing either means `CREATE OR REPLACE` on `mask_phi`, and the masks follow automatically.
9. **Group-membership change not made.** The alternative of adding the SP to `fe-bar-appeals-reviewers` was not used. That needs Naveen's approval.


## Hardening update (2026-11-26, orchestrator)

- `mask_phi` now uses `session_user()` (docs recommend it over `current_user()`); new `mask_phi_ts` for TIMESTAMP DOB.
- `encounter_grounding` masked too (`patient_name`, `member_id`, `dob`): docs state masks are retained when a table is replaced if column names are unchanged, so the stage-20 rebuild keeps them.
- Docs basis for invoker evaluation (Manually apply row filters and column masks): "All filters run with definer's rights except for functions that check user context (for example, the `SESSION_USER` and `IS_ACCOUNT_GROUP_MEMBER` functions) which run as the invoker." `is_member()` is a user-context check; it is not named explicitly, so the non-member path is verified at logic level only (no second identity without new grants).
- Chat tool functions unchanged (last_altered 2026-11-24).

Active masks:

| table_name | column_name | mask_name |
|---|---|---|
| appeals_output | patient_name | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |
| data_sheet_facts | dob_text | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |
| data_sheet_facts | member_id | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |
| data_sheet_facts | patient_name | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |
| encounter_grounding | dob | appeals_hackathon_catalog.fe_bar_appeals.mask_phi_ts |
| encounter_grounding | member_id | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |
| encounter_grounding | patient_name | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |

Reviewer (member) view of the hero row in encounter_grounding:

| patient_name | member_id | dob |
|---|---|---|
| Elena Marquez | BCBSAZ-PPO-4471 | 1962-03-14T00:00:00.000Z |

Non-member branch (logic check):

| non_member | non_member_sees |
|---|---|
| false | ***MASKED*** |



## Mask retention verified (2026-11-26)
Ran only the `grounding` job task (stage 20 does `CREATE OR REPLACE TABLE encounter_grounding`): TERMINATED SUCCESS. `information_schema.column_masks` afterwards still lists `dob → mask_phi_ts`, `member_id → mask_phi`, `patient_name → mask_phi` on `encounter_grounding`. Masks survive the rebuild (matches the docs on REPLACE TABLE).
