-- Approved by Naveen 2026-11-24: the app's Genie tab runs as the app service principal (fe-bar-appeals-app,
-- client id 059b0419-b956-41e1-a788-e5104b645dc9) because the forwarded user token did not pick up the new `genie`
-- scope. Least privilege: SELECT only on the 5 objects in the Genie space. Warehouse CAN_USE + space CAN_RUN come
-- from the app's resource bindings.
GRANT USE CATALOG ON CATALOG appeals_hackathon_catalog TO `059b0419-b956-41e1-a788-e5104b645dc9`;
GRANT USE SCHEMA ON SCHEMA appeals_hackathon_catalog.fe_bar_appeals TO `059b0419-b956-41e1-a788-e5104b645dc9`;
GRANT SELECT ON TABLE appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics TO `059b0419-b956-41e1-a788-e5104b645dc9`;
GRANT SELECT ON TABLE appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist TO `059b0419-b956-41e1-a788-e5104b645dc9`;
GRANT SELECT ON TABLE appeals_hackathon_catalog.fe_bar_appeals.appeals_output TO `059b0419-b956-41e1-a788-e5104b645dc9`;
GRANT SELECT ON TABLE appeals_hackathon_catalog.fe_bar_appeals.eval_summary TO `059b0419-b956-41e1-a788-e5104b645dc9`;
GRANT SELECT ON TABLE appeals_hackathon_catalog.fe_bar_appeals.review_state_uc TO `059b0419-b956-41e1-a788-e5104b645dc9`;
