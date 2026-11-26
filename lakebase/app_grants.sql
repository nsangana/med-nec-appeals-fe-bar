-- Least-privilege grants for the fe-bar-appeals-app service principal (Postgres role = SP client id).
-- The role itself is created by the app's Lakebase database resource binding (dbrx-apps-<client id>).
-- Applied 2026-11-24 by the orchestrator with Naveen's approval. Idempotent (GRANT is a no-op if already held).
GRANT CONNECT ON DATABASE appeals TO "059b0419-b956-41e1-a788-e5104b645dc9";
GRANT USAGE ON SCHEMA public, fe_bar_appeals TO "059b0419-b956-41e1-a788-e5104b645dc9";
-- Worklist: synced from UC, read-only for the app
GRANT SELECT ON fe_bar_appeals.worklist_serving TO "059b0419-b956-41e1-a788-e5104b645dc9";
-- Reviewer events: append-only (no UPDATE/DELETE)
GRANT SELECT, INSERT ON public.review_actions TO "059b0419-b956-41e1-a788-e5104b645dc9";
GRANT USAGE ON SEQUENCE public.review_actions_id_seq TO "059b0419-b956-41e1-a788-e5104b645dc9";
-- Derived latest status per encounter
GRANT SELECT ON public.review_state TO "059b0419-b956-41e1-a788-e5104b645dc9";
