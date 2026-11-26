# 06 — Databricks App: fe-bar-appeals-app (Agent E)

> **Note (2026-11-25).** The app was redeployed after the clean data-layer rerun (deployment `01f1e91de0e21f58818a94fcc05b5319`, app id `059b0419-b956-41e1-a788-e5104b645dc9`). The API responses below are from 2026-11-24 and show the earlier counts (for example 70 WARRANTED). Re-check the worklist and summary routes before quoting app numbers. The current counts are in evidence/03_lakebase.md (73 / 64 / 43).

Workspace `fevm-appeals-hackathon`. Captured 2026-11-24 (UTC). Source of truth for the code: `app/`.
Evidence is from the deployed app's own API routes (real Lakebase and UC data), not simulated.

## Deployment
| Item | Value |
|---|---|
| App | `fe-bar-appeals-app` (id `059b0419-b956-41e1-a788-e5104b645dc9`) |
| URL | https://fe-bar-appeals-app-7474656043998914.aws.databricksapps.com |
| State | app RUNNING, compute ACTIVE |
| Active deployment | `01f1e7eefc82159aac9ffabb03077418` SUCCEEDED ("App started successfully") |
| Earlier deployments | `01f1e7ed83d914e9a793520872e506aa` (first), `01f1e7ee02b3124bb39f3e1c5d143f1e` (fallback), `01f1e7ee916d185aaa2a3c6c07eec0fe` (pre UI fix) — all SUCCEEDED |
| Source path | `/Workspace/Users/<builder>/fe-bar-appeals-app` (uploaded with `workspace import-dir`; excludes node_modules, dist, .env) |
| Service principal (client id) | `059b0419-b956-41e1-a788-e5104b645dc9` |
| User API scopes | `sql`, `model-serving`, `files` (OBO) |

Created with `databricks apps create --json` (no compute), started with `apps start`, deployed with `apps deploy --source-code-path`.
`databricks apps create-update` for later resource changes (not needed yet). Bundle deploy not used.

## Resource bindings
| Resource | Target | Permission | Status |
|---|---|---|---|
| `sql-warehouse` | `559faf81d610a2a1` | CAN_USE | bound |
| `files` (volume) | `appeals_hackathon_catalog.fe_bar_appeals.appeal_pdfs` | READ_VOLUME | bound |
| `postgres` | `projects/fe-bar-appeals-lakebase/branches/production/databases/appeals` | CAN_CONNECT_AND_CREATE | bound; `LAKEBASE_ENDPOINT` from it |
| `serving-endpoint` | `fe-bar-appeals-chat` | CAN_QUERY | NOT bound: endpoint does not exist yet (app.yaml uses a literal name) |
| `genie-space` | `01f1e7ec913217158b231c3e2f18fa20` ("FE Bar – Medical Necessity Appeals") | CAN_RUN | bound 2026-11-24 by orchestrator (`apps create-update`, update SUCCEEDED); `DATABRICKS_GENIE_SPACE_ID` valueFrom genie-space; scope `dashboards.genie` added; deployment `01f1e7f10d78100c92bcc5b9220fa35d` SUCCEEDED; Genie space ACL shows app SP CAN_RUN |

Nothing points at `appeals_agent`, `appeals-chat-agent-endpoint`, or `<prior-prototype app>`:
`grep -rn "appeals_agent\|appeals-chat-agent-endpoint\|<prior-prototype app>" app/ --exclude-dir=node_modules` returns only the test
assertion that checks they are absent (`server/worklist.test.ts`).

## Startup log (healthy start, deployment 01f1e7eefc82…)
```
[APP] ./.env not found. Continuing without it.   (deployed copy has no .env; env comes from app.yaml + resources)
[APP] [appkit:lakebase] Lakebase SP pool initialized
[APP] [appkit:lakebase] Lakebase OBO pool manager initialized
[APP] [appkit:server] Server running on http://0.0.0.0:8000
[APP] [appkit:server] Mode: production (static)
[BUILD] [INFO] Deployment successful
```
Errors in the log while serving: none from Postgres or UC (no 42501). Two expected lines: a `Plugin execution failed` and
`appeals-chat upstream error: ... endpoint does not exist` at chat time (see chat below). A
`App did not respect SIGTERM timeout` line came from the previous instance during a redeploy.

## Captured app API responses (caller = Naveen's CLI user token as bearer; this is the platform-proxied route)

### (a) Worklist, top 5 (`GET /api/worklist?page_size=5`, default sort = NEW first, then priority_rank)
Total 500 encounters. NEW = 20, AT_RISK = 75 (summary route).
| rank | tag | account | patient | denial | payer | days left | expected $ | recommendation | review |
|---|---|---|---|---|---|---|---|---|---|
| 77 | NEW | 770000064 | Leonard Lindqvist | CO50 | Aetna | 179 | 15,435.33 | NOT WARRANTED | Not started |
| 93 | NEW | 770000056 | Victor Whitcombe | CO50 | BCBS of Arizona Medicare Advantage | 64 | 13,545.98 | WARRANTED | Not started |
| 109 | NEW | 770000143 | Lucia Tadesse | CO50 | Cigna | 179 | 12,226.33 | NOT WARRANTED | Not started |
| 125 | NEW | 770000462 | Helen Abernathy | CO55 | Aetna | 179 | 8,989.80 | NEEDS REVIEW | Not started |
| 139 | NEW | 770000005 | Carmen Fairbanks | CO55 | Cigna | 179 | 8,265.84 | NOT WARRANTED | Not started |

The hero (770000001, rank 1, AT_RISK, 9 days) is not in the top 5 by design: NEW items sort first.
`GET /api/worklist/summary`: total 500, new 20, at_risk 75, warranted 23, not_warranted 22, needs_review 15, warranted expected $336,319.43.

### (b) Review-action round trip on the hero claim (101 / 770000001 / 50000001)
`POST /api/review-actions` `{"facility_id":"101","account":"770000001","encounter_nbr":"50000001","action":"ROUTE_TO_REVIEW","note":"E2E round trip from fe-bar-appeals-app build (hero claim)"}`
→ HTTP 201
```json
{"ok":true,"action_id":"5","action":"ROUTE_TO_REVIEW","reviewer":"<builder email>",
 "created_at":"2026-11-24 10:00:14.539825+00","status":"ROUTE_TO_REVIEW","status_label":"Routed to review",
 "submitted_at":"2026-11-24 09:14:31.159563+00"}
```
- Reviewer identity came from the `x-forwarded-email` request header (the platform sets it), so it is not sent in the body.
- The row is an append-only INSERT into `public.review_actions` by the app SP; the status is read back from `public.review_state`.
- Validation check: `{"action":"EDIT"}` without `edited_letter` → HTTP 400 (`EDIT requires edited_letter`).
- This is a real test event in production demo data. The hero now shows "Routed to review" (append-only, cannot be deleted by the app). `submitted_at` 09:14 is from C's earlier test rows (SUBMIT).

Hero history from `GET /api/cases/101/770000001/50000001` (`review.history`): ids 5 (ROUTE_TO_REVIEW, E2E), 2 (SUBMIT, simulated), 1 (APPROVE, simulated).

### (c) Case-file file paths
`GET /api/cases/101/770000001/50000001` (HTTP 200, 2,122 B) → `files`:
| doc | file name | route | HTTP check |
|---|---|---|---|
| Appeal letter | `101_770000001_50000001_letter.pdf` | `/api/files/files/raw?path=101_770000001_50000001_letter.pdf` | 200, `application/pdf`, 6,957 B, 1 page |
| Data sheet (deterministic) | `101_770000001_50000001_datasheet.pdf` | `/api/files/files/raw?path=101_770000001_50000001_datasheet.pdf` | 200, 11,156 B |
| AI reasoning worksheet | `101_770000001_50000001_cheatsheet.pdf` | `/api/files/files/raw?path=101_770000001_50000001_cheatsheet.pdf` | 200, 12,108 B |

Those 200s were served through the OBO files plugin using my CLI user token (I hold READ_VOLUME as owner).

Case 770000462 (`GET /api/cases/103/770000462/50000462`, 200, 4,104 B): NEEDS REVIEW, no letter (letter is null by design), data sheet and worksheet present.
Its `needs_review_reason` is 2,874 characters with 8 bullets. The worklist cell shows the one-line summary (see the UI fix below).

## UI fix: long NEEDS REVIEW reason (reported by Naveen, 770000462)
- Worklist cell: `summarizeReason()` gives one line, clamped to 2 lines with `break-words`; the full text is in the hover `title`.
  Actual output for 770000462: `8 open items · FDA device approval/clearance pathway undocumented` (65 characters).
- Case file: `ReasonList` shows all 8 items as a bulleted list (title in bold, text nodes only, no HTML from the model), in a `max-h-40 overflow-y-auto` box.
- Other long LLM text: the letter and the AI worksheet (`appeal_letter` ~6.6k chars max, `cheat_sheet` ~11.7k chars max) appear only in
  the Text tab inside a scrollable `pre` (`max-h 60vh`). They are not shown inline in the table.
- Verified through the API payload (reason length 2,874; 8 items) and the parser unit tests (22 passing). Visual check: NOT done (see below).

## Chat (`POST /api/appeals-chat`)
HTTP 502 `{"error":"Agent endpoint error (404): The given endpoint does not exist ..."}`.
Expected until `fe-bar-appeals-chat` exists. The route surfaces the upstream failure (it used to return an empty answer; fixed).

## Genie
Not wired. Set `DATABRICKS_GENIE_SPACE_ID` and add the `genie-space` resource to enable it (`app/README.md` "Genie wiring").

## Tests and build (local)
- `npm run typecheck` (server + client): clean. `npm run lint`: clean (0 errors, 0 warnings). `npm run build`: clean.
- `npx vitest run`: 22 tests pass (`server/worklist.test.ts` 17: SQL parameters, ORDER BY whitelist, review-action validation, row mapping, PDF URLs; `client/src/lib/reason.test.ts` 5: reason parsing).

## Not verified / limits
- Browser UI: NOT verified. The app URL needs an interactive SSO session. I could not drive the app in a browser as Naveen, so I did not screenshot it.
  Every check above is an API call with a bearer token, plus the build. Look at the worklist and case file once in a browser.
- Grants: the orchestrator applied `lakebase/app_grants.sql` (verified by the 201 above). Reviewer-level UC grants (OBO) are pending, see `lakebase/APP_GRANTS_PENDING.md`.
- Chat endpoint and Genie space resources: pending (endpoint does not exist yet; Genie space not created).


## Fix log (orchestrator, 2026-11-24)
- Genie tab returned `Forbidden: Invalid scope, required scopes: genie`. Added user API scope `genie` (kept `dashboards.genie`) via `apps create-update` (SUCCEEDED). Effective scopes: dashboards.genie, files, genie, iam.access-control:read, iam.current-user:read, model-serving, sql. Users must reload/re-consent so their forwarded token carries the new scope.
- Chat returned 403 (app SP had no CAN_QUERY): bound `serving-endpoint` resource fe-bar-appeals-chat CAN_QUERY; app.yaml `DATABRICKS_SERVING_ENDPOINT_NAME` valueFrom serving-endpoint; redeployed.
- Follow-up: still Forbidden after adding `genie`, because "Apps that are already running continue to run with their existing scopes" (Databricks Apps auth docs). Removed deprecated `dashboards.genie`, kept `genie`, redeployed (deployment `01f1e7f715241614b4c14e7c694b059e` SUCCEEDED). Effective scopes: files, genie, iam.access-control:read, iam.current-user:read, model-serving, sql.
- Genie auth decision (Naveen, 2026-11-24): the forwarded user token still lacked `genie` after scope update + redeploy + fresh session, so the Genie tab now runs as the **app service principal**. `server/server.ts` subclasses the AppKit Genie plugin (same routes/SSE/<GenieChat> contract, no `asUser` wrapper). SP grants: SELECT on the 5 space objects + USE CATALOG/SCHEMA (`governance/04_app_sp_genie_grants.sql`, verified with SHOW GRANTS); CAN_RUN on the space via the genie-space resource. Typecheck/lint/22 tests/build pass; deployment `01f1e7fb1d38144b9945d132b923a60e` SUCCEEDED. Trade-off: Genie answers in the app reflect the app's access, not per-reviewer grants; worklist/review actions already run as the SP; PDFs + chat stay OBO.
