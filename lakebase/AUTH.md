# Lakebase auth for the FE Bar app

Project `fe-bar-appeals-lakebase`, branch `production`, database `appeals`, endpoint `primary`.

## Two identities, two jobs

| Access | Identity | Mechanism |
|---|---|---|
| Lakebase Postgres (worklist read, review_actions insert, review_state read) | **App service principal** (`fe-bar-appeals-app` SP) | Postgres role mapped to the SP, OAuth token minted by the SP (`LAKEBASE_OAUTH_V1`). Token lasts ~1 h; the app must refresh it (new token per pool connection / on auth failure). |
| Genie tab (Genie Conversation API) | **App service principal** | CAN_RUN on the space + SELECT on its 5 objects (governance/04_app_sp_genie_grants.sql). OBO was not possible: the forwarded user token never carried the `genie` scope. |
| UC SQL warehouse queries, UC volume files (PDFs), chat | **Signed-in user (OBO)** | Databricks Apps user-token forwarding. Governed by the user's UC grants, so PHI column masks and least-privilege apply per reviewer. |

Rule of thumb: anything the reviewer writes or reads in the worklist goes to Lakebase through the SP. Anything
that reads governed UC data (letters/PDFs, chat, Genie) goes through the user's OBO token.

## App SP role (apply after the app exists)

The SP client ID is only known once `fe-bar-appeals-app` is created, so the role is pending. The orchestrator runs:

```bash
export DATABRICKS_AUTH_STORAGE=plaintext
APP_SP_CLIENT_ID=<from: databricks apps get fe-bar-appeals-app -o json | jq -r .service_principal_client_id>
databricks postgres create-role projects/fe-bar-appeals-lakebase/branches/production \
  --role-id "$APP_SP_CLIENT_ID" \
  --json "{\"spec\": {\"identity_type\": \"SERVICE_PRINCIPAL\", \"postgres_role\": \"$APP_SP_CLIENT_ID\", \"auth_method\": \"LAKEBASE_OAUTH_V1\"}}" \
  --profile fevm-appeals-hackathon
```

No `membership_roles`, so the role starts with no admin rights.

## Grants (least privilege; run as the project owner, against database `appeals`)

Replace `<APP_SP_CLIENT_ID>` with the SP client ID (quoted identifier, as in the SQL below). Run with `psql`
connected as `<builder email>` (see `setup_lakebase.sh` for the connect pattern).

```sql
-- Connect + schema usage
GRANT CONNECT ON DATABASE appeals TO "<APP_SP_CLIENT_ID>";
GRANT USAGE ON SCHEMA public, fe_bar_appeals TO "<APP_SP_CLIENT_ID>";

-- Worklist (synced, read-only for the app)
GRANT SELECT ON fe_bar_appeals.worklist_serving TO "<APP_SP_CLIENT_ID>";

-- Reviewer events: append-only. No UPDATE/DELETE granted.
GRANT SELECT, INSERT ON public.review_actions TO "<APP_SP_CLIENT_ID>";
GRANT USAGE ON SEQUENCE public.review_actions_id_seq TO "<APP_SP_CLIENT_ID>";  -- needed for the identity column on INSERT

-- Derived review state (view runs with owner rights, so only the view needs SELECT)
GRANT SELECT ON public.review_state TO "<APP_SP_CLIENT_ID>";
```

Do not grant on the `appeals` database's other schemas. Do not grant `DATABRICKS_SUPERUSER` to the app.
Note: `review_state` exists only after the synced table is online (`setup_lakebase.sh` applies it then). Grant it
after that point.

Verify (as the SP role, with its OAuth token): `SELECT count(*) FROM fe_bar_appeals.worklist_serving;` succeeds,
`UPDATE public.review_actions SET note = 'x';` fails with permission denied.

## Notes
- Synced table: Postgres owns `fe_bar_appeals.worklist_serving`. Only reads, indexes and DROP are allowed on it
  from Postgres; the app must never write to it.
- Token refresh: generate with `databricks postgres generate-database-credential <endpoint>` for dev. In the app,
  the SP's OAuth token is minted through the Databricks SDK client. Don't put tokens in env files or the repo.
- Connection: host `ep-icy-field-d2gk8ye7.database.us-east-1.cloud.databricks.com` (pooled host also in endpoint status),
  port 5432, db `appeals`, sslmode=require, user = SP client ID (the Postgres role name).
