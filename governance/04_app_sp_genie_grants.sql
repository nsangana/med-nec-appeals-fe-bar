-- Approved by Naveen 2026-11-24: the app's Genie tab runs as the app service principal (fe-bar-appeals-app,
-- client id 059b0419-b956-41e1-a788-e5104b645dc9) because the forwarded user token did not pick up the new `genie`
-- scope. Least privilege: SELECT only on the 5 objects in the Genie space. Warehouse CAN_USE + space CAN_RUN come
-- from the app's resource bindings.
-- Parameters (SQL task): :catalog and :schema. Every statement after this point resolves unqualified
-- object names against them (the session keeps the USE settings for the whole file).
USE CATALOG IDENTIFIER(:catalog);
USE SCHEMA IDENTIFIER(:schema);
-- Note: a one-part schema name in ON SCHEMA resolves against the USE CATALOG catalog (IDENTIFIER takes one
-- constant only, so the catalog.schema concatenation is not allowed there).

GRANT USE CATALOG ON CATALOG IDENTIFIER(:catalog) TO `059b0419-b956-41e1-a788-e5104b645dc9`;
GRANT USE SCHEMA ON SCHEMA IDENTIFIER(:schema) TO `059b0419-b956-41e1-a788-e5104b645dc9`;
GRANT SELECT ON TABLE appeals_metrics TO `059b0419-b956-41e1-a788-e5104b645dc9`;
GRANT SELECT ON TABLE gold_denial_worklist TO `059b0419-b956-41e1-a788-e5104b645dc9`;
GRANT SELECT ON TABLE appeals_output TO `059b0419-b956-41e1-a788-e5104b645dc9`;
GRANT SELECT ON TABLE eval_summary TO `059b0419-b956-41e1-a788-e5104b645dc9`;
GRANT SELECT ON TABLE review_state_uc TO `059b0419-b956-41e1-a788-e5104b645dc9`;
