-- =====================================================================================
-- PROPOSED ONLY. NOT EXECUTED. PENDING Naveen's choice of the reviewer group.
-- Placeholder principal: `fe-bar-appeals-reviewers`. ADDENDUM 3: a WORKSPACE-level group with this name exists.
-- UC GRANTs need an account-level group, so this file stays pending. Workspace ACLs (app CAN_USE, Genie CAN_RUN)
-- wait for Naveen's approval. The Genie space is NOT shared with this group.
-- Do not run until Naveen names the group. Replace the placeholder everywhere, then run as the
-- schema owner. This file is kept as a reviewable least-privilege proposal.
--
-- Least-privilege scope: read the worklist, the generated appeals and the appeal PDFs, and call the
-- lookup functions. No bronze, no landing volume, no eval labels, no encounter_grounding (the LLM
-- input bundle), no cost or review-state internals.
-- Open point for the decision: PHI columns (patient_name, member_id, claim_id, dob) stay visible to
-- this group by design, because reviewers work the appeal. Confirm with RCM and compliance.
-- =====================================================================================

-- Navigation
GRANT USE CATALOG ON CATALOG appeals_hackathon_catalog TO `fe-bar-appeals-reviewers`;
GRANT USE SCHEMA ON SCHEMA appeals_hackathon_catalog.fe_bar_appeals TO `fe-bar-appeals-reviewers`;

-- Read the worklist, the generated appeals and the metric view (used by the Genie space)
GRANT SELECT ON TABLE appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist TO `fe-bar-appeals-reviewers`;
GRANT SELECT ON TABLE appeals_hackathon_catalog.fe_bar_appeals.appeals_output TO `fe-bar-appeals-reviewers`;
GRANT SELECT ON TABLE appeals_hackathon_catalog.fe_bar_appeals.worklist_serving TO `fe-bar-appeals-reviewers`;
GRANT SELECT ON VIEW appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics TO `fe-bar-appeals-reviewers`;

-- Appeal PDFs (letters, cheat sheets, data sheets). Read only.
GRANT READ VOLUME ON VOLUME appeals_hackathon_catalog.fe_bar_appeals.appeal_pdfs TO `fe-bar-appeals-reviewers`;

-- UC functions used by the app and the chatbot. Lookups only. Nothing on bronze, landing or eval labels.
GRANT EXECUTE ON FUNCTION appeals_hackathon_catalog.fe_bar_appeals.get_appeal TO `fe-bar-appeals-reviewers`;
GRANT EXECUTE ON FUNCTION appeals_hackathon_catalog.fe_bar_appeals.get_encounter TO `fe-bar-appeals-reviewers`;
GRANT EXECUTE ON FUNCTION appeals_hackathon_catalog.fe_bar_appeals.mpfs_lookup TO `fe-bar-appeals-reviewers`;
GRANT EXECUTE ON FUNCTION appeals_hackathon_catalog.fe_bar_appeals.descriptor_lookup TO `fe-bar-appeals-reviewers`;
