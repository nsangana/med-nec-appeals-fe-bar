# 13 Column masks on PHI (fe_bar_appeals)

Synthetic data, prototype. Applied 2026-11-25 with `governance/05_column_masks.sql` and hardened 2026-11-26 (session_user(), `mask_phi_ts` for the DOB timestamp, and `encounter_grounding` added). Profile `fevm-appeals-hackathon`, warehouse `559faf81d610a2a1`. Identity for the member checks: the builder, a member of workspace group `fe-bar-appeals-reviewers`. No GRANT/REVOKE, no sharing, no bundle deploy.

History: earlier runs are in git history.

## 1. Mask functions (current, `DESCRIBE FUNCTION EXTENDED`, 2026-11-26)

```sql
CREATE OR REPLACE FUNCTION appeals_hackathon_catalog.fe_bar_appeals.mask_phi(val STRING)
RETURNS STRING
RETURN CASE
  WHEN is_member('fe-bar-appeals-reviewers') THEN val
  WHEN session_user() = '059b0419-b956-41e1-a788-e5104b645dc9' THEN val
  ELSE '***MASKED***'
END;
```

`mask_phi_ts` is the same CASE for TIMESTAMP values (DOB in `encounter_grounding`). The function comment states that identity checks (`is_member`, `session_user`) run as the INVOKER inside masks, per the Databricks docs for functions that check user context.

## 2. Masks attached (`information_schema.column_masks`, 2026-11-26)

| table_name | column_name | mask_name |
|---|---|---|
| appeals_output | patient_name | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |
| data_sheet_facts | dob_text | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |
| data_sheet_facts | member_id | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |
| data_sheet_facts | patient_name | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |
| encounter_grounding | dob | appeals_hackathon_catalog.fe_bar_appeals.mask_phi_ts |
| encounter_grounding | member_id | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |
| encounter_grounding | patient_name | appeals_hackathon_catalog.fe_bar_appeals.mask_phi |

## 3. Scope: what is and is not masked, and why

| Object | Column(s) | Masked? | Reason |
|---|---|---|---|
| appeals_output | patient_name | yes | Reviewer-facing managed Delta table. No DOB or member_id columns in this table. |
| data_sheet_facts | patient_name, member_id, dob_text | yes | Managed Delta, written by `CREATE TABLE IF NOT EXISTS` + `MERGE`, so the mask survives job runs. |
| encounter_grounding | patient_name, member_id, dob | yes | Rebuilt by `CREATE OR REPLACE TABLE` in stage 20. Masks are retained when the column names are unchanged (verified below). Also read by the chat tool `get_encounter`. |
| worklist_serving | patient_name, etc. | no | Source of the Lakebase synced table. Masks or filters there can break the sync. |
| gold_denial_worklist, streaming tables, MVs | patient_name | no | SDP-managed by the pipeline. |
| eval tables | - | no | Out of scope. |
| appeals_output / data_sheet_facts / encounter_grounding | claim_number, notes_verbatim | no | Not in the agreed PHI list. Claim numbers are needed to work an appeal. Free-text notes can contain PHI. Flagged for a compliance decision. |
| get_appeal, get_encounter, mpfs_lookup, descriptor_lookup | - | functions untouched | Never replaced. |

## 4. Member path (builder, re-queried 2026-11-26)

| Check | Result |
|---|---|
| `is_member('fe-bar-appeals-reviewers')` | true |
| `appeals_output` rows with `***MASKED***` in `patient_name` | 0 of 180 |
| `data_sheet_facts` rows with a masked `patient_name` or `member_id` | 0 of 450 |
| `encounter_grounding` rows with a masked `patient_name` or `member_id` | 0 of 450 |
| Hero row in `encounter_grounding` (PCN 770000001) | Elena Marquez, BCBSAZ-PPO-4471, 1962-03-14T00:00:00.000Z (real values) |

Row counts are unchanged by the masks (appeals_output 180, data_sheet_facts 450, encounter_grounding 450).

## 5. Test results

**(a) Member path: PASS.** The hero row returns real values in every masked table, and no masked value appears in the reviewer view (table in section 4).

**(b) Non-member path: PARTIAL, logic only.** No second identity could be exercised, because that needs a grant or a credential for another principal, and no new grants were allowed. What was checked:

| non_member | non_member_sees |
|---|---|
| false | ***MASKED*** |

The non-member branch of the CASE returns `***MASKED***` for `is_member = false`. This is not an end-to-end test as a real non-member.

Probe of the MERGE path (scratch table `zz_mask_probe`, dropped afterwards): a MERGE into a masked target updated 1 row, and the member read returned the real value. This shows the job's MERGEs into masked tables still work.

**(c) Genie benchmarks: PASS (14 of 14), run as the builder.** The Genie Conversation API run is in evidence/07 (2026-11-26). Those answers were not run as the app service principal.

**(d) Chat endpoint `fe-bar-appeals-chat`: PASS on the hero question (2026-11-26).** The current answer gives WARRANTED, CPT 27447-RT, BCBS of Arizona, the three dated clinical facts and the deadline 2026-12-04 (8 days remaining). The answer text contains no patient name and no DOB. The chat endpoint's own identity against the masks is not tested (see limitations).

**(e) Lakebase sync.** `worklist_serving` is not masked by design, so the synced table carries patient names from `gold_denial_worklist`. The sync reads key and output columns from `appeals_output`, so the mask does not affect it.

**Mask retention through stage 20 (2026-11-26).** The `grounding` job task was run on its own (stage 20 does `CREATE OR REPLACE TABLE encounter_grounding`): TERMINATED SUCCESS. `information_schema.column_masks` afterwards still lists `dob → mask_phi_ts`, `member_id → mask_phi` and `patient_name → mask_phi` on `encounter_grounding`.

## 6. Job and chat behaviour

- Job compute is serverless for both the SDP pipeline and the Python tasks (`resources/*.yml`).
- The job runs as the builder (a member), so its reads of masked tables return real values. The 2026-11-26 job runs are in evidence/08.
- MERGE is blocked only for policies with nesting, aggregations, windows, limits or non-deterministic functions. The mask has none of these. Verified by the probe above.

## 7. Limitations and open items (read these before calling it "protected")

1. **Definer-rights question on `is_member` (most important, unverified).** The Databricks docs say filters run with definer's rights except for functions that check user context, and name `SESSION_USER` and `IS_ACCOUNT_GROUP_MEMBER`. `is_member` is not named in that list, though it is a user-context check. The table owner is a group member. If `is_member` were evaluated with the owner's rights, every reader would see real values. Closing this needs a non-member identity to run one SELECT. **Action: have a non-member run `SELECT patient_name FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_output LIMIT 3` after a grant is approved. Expect `***MASKED***`.**
2. **SP exemption not run as the SP.** The Genie tab runs as the app SP (`059b0419-…`), and the `session_user()` branch for it was not exercised with that identity. Verify the Genie tab in the app and check that names are not masked.
3. **Chat identity not tested.** `get_encounter` reads the masked `encounter_grounding`. What the chat endpoint's identity sees through that function was not run as a non-member, so the answer text is the only evidence here.
4. **Lakebase copies stay unmasked.** `worklist_serving` (synced) and the Postgres `public.review_actions` / `review_state` views carry patient names. Reviewer access to these is controlled by app CAN_USE, so the mask does not apply there by design.
5. **Other PHI paths not masked:** the appeal PDFs in volume `appeal_pdfs` (they show patient names), `gold_denial_worklist.patient_name` (SDP-managed), and `claim_number` and `notes_verbatim` in `data_sheet_facts` and `encounter_grounding`.
6. **The pending `governance/02_reviewer_grants.sql` would expose unmasked PHI.** It grants reviewers SELECT on `gold_denial_worklist` and `worklist_serving`, which are not masked. Do not run it as written without a decision on those objects.
7. **Job identity dependency.** Pipeline 40 renders data-sheet PDFs from `data_sheet_facts`. If the job identity ever changes to a non-member, the PDFs would contain `***MASKED***` names. Keep the job's identity in the group or add its SP to the exemption.
8. **Mask function is fixed per the spec.** The group name and SP id are hardcoded. Changing either means `CREATE OR REPLACE` on `mask_phi` (and `mask_phi_ts`), and the masks follow automatically.
9. **Group-membership change not made.** The alternative of adding the SP to `fe-bar-appeals-reviewers` was not used. That needs the builder's approval.
