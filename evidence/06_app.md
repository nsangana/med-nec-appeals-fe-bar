# 06 — Databricks App: fe-bar-appeals-app

Workspace `fevm-appeals-hackathon`. Captured 2026-11-26 (UTC) from the deployed app's own API routes (real Lakebase and UC data, not simulated). Source of truth for the code: `app/`.

History: earlier runs are in git history.

## Deployment

| Item | Value |
|---|---|
| App | `fe-bar-appeals-app` (id `059b0419-b956-41e1-a788-e5104b645dc9`) |
| URL | https://fe-bar-appeals-app-7474656043998914.aws.databricksapps.com |
| State | app RUNNING, compute ACTIVE |
| Active deployment | `01f1e96376b9168e824d4acf7801c9bf` SUCCEEDED ("App started successfully"), checked 2026-11-26 |
| Source path | `/Workspace/Users/<builder>/fe-bar-appeals-app` (uploaded with `workspace import-dir`; excludes node_modules, dist, .env) |
| Service principal (client id) | `059b0419-b956-41e1-a788-e5104b645dc9` |
| User API scopes | `files`, `genie`, `iam.access-control:read`, `iam.current-user:read`, `model-serving`, `sql` (OBO) |

Created with `databricks apps create --json` (no compute), started with `apps start`, deployed with `apps deploy --source-code-path`. Later resource and scope changes used `databricks apps create-update`. Bundle deploy not used.

## Resource bindings

| Resource | Target | Permission | Status |
|---|---|---|---|
| `sql-warehouse` | `559faf81d610a2a1` | CAN_USE | bound |
| `files` (volume) | `appeals_hackathon_catalog.fe_bar_appeals.appeal_pdfs` | READ_VOLUME | bound |
| `postgres` | `projects/fe-bar-appeals-lakebase/branches/production/databases/appeals` | CAN_CONNECT_AND_CREATE | bound; `LAKEBASE_ENDPOINT` from it |
| `serving-endpoint` | `fe-bar-appeals-chat` | CAN_QUERY | bound; `DATABRICKS_SERVING_ENDPOINT_NAME` valueFrom serving-endpoint |
| `genie-space` | `01f1e7ec913217158b231c3e2f18fa20` ("FE Bar – Medical Necessity Appeals") | CAN_RUN | bound; `DATABRICKS_GENIE_SPACE_ID` valueFrom genie-space |

Nothing points at `appeals_agent`, `appeals-chat-agent-endpoint`, or `<prior-prototype app>`:
`grep -rn "appeals_agent\|appeals-chat-agent-endpoint\|<prior-prototype app>" app/ --exclude-dir=node_modules` returns only the test assertion that checks they are absent (`server/worklist.test.ts`).

## Startup log (healthy start, first deployment `01f1e7eefc82…`)

```
[APP] ./.env not found. Continuing without it.   (deployed copy has no .env; env comes from app.yaml + resources)
[APP] [appkit:lakebase] Lakebase SP pool initialized
[APP] [appkit:lakebase] Lakebase OBO pool manager initialized
[APP] [appkit:server] Server running on http://0.0.0.0:8000
[APP] [appkit:server] Mode: production (static)
[BUILD] [INFO] Deployment successful
```

Errors while serving: none from Postgres or UC (no 42501). A `App did not respect SIGTERM timeout` line came from the previous instance during a redeploy.

## Captured app API responses (2026-11-26, bearer = CLI user token, platform-proxied route)

### (a) Worklist summary and top 5

`GET /api/worklist/summary`:

| total | new | at_risk | warranted | not_warranted | needs_review | not_generated | warranted_expected |
|---|---|---|---|---|---|---|---|
| 500 | 0 | 67 | 72 | 66 | 42 | 320 | $895,235.64 |

`GET /api/worklist?page_size=5` (default sort: NEW first, then priority_rank; NEW is empty on this run date):

| rank | tag | account | patient | denial | payer | days left | expected $ | recommendation | review |
|---|---|---|---|---|---|---|---|---|---|
| 1 | AT_RISK | 770000001 | Elena Marquez | CO50 | BCBS of Arizona | 8 | 24,850.00 | WARRANTED | SUBMIT (simulated) |
| 2 | AT_RISK | 770000203 | Carmen Gallagher | CO50 | Aetna | 1 | 20,096.92 | WARRANTED | ROUTE_TO_REVIEW |
| 3 | AT_RISK | 770000394 | Leonard Marquez | CO50 | BCBS of Arizona Medicare Advantage | 0 | 18,585.01 | NEEDS REVIEW | EDIT |
| 4 | AT_RISK | 770000231 | Gerald Quintero | CO50 | Humana Medicare Advantage | 10 | 18,438.19 | NOT WARRANTED | not started |
| 5 | AT_RISK | 770000233 | Alma Ostrowski | CO50 | Aetna | 4 | 17,437.31 | WARRANTED | APPROVE |

The hero (770000001, rank 1, AT_RISK, 8 days on 2026-11-26; 9 on the 2026-11-25 run) is first by priority score. The review column is the simulated reviewer state.

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
- This is a real test event in the demo data (append-only, cannot be deleted by the app). The hero shows "Routed to review" in this event; the current hero status in the worklist is SUBMIT (see (a)).

Hero history from `GET /api/cases/101/770000001/50000001` (`review.history`): ids 5 (ROUTE_TO_REVIEW, E2E), 2 (SUBMIT, simulated), 1 (APPROVE, simulated).

### (c) Case-file file paths

`GET /api/cases/101/770000001/50000001` (HTTP 200) → `files`:

| doc | file name | route | HTTP check (2026-11-26) |
|---|---|---|---|
| Appeal letter | `101_770000001_50000001_letter.pdf` | `/api/files/files/raw?path=101_770000001_50000001_letter.pdf` | 200, `application/pdf`, 6,938 B |
| Data sheet (deterministic) | `101_770000001_50000001_datasheet.pdf` | `/api/files/files/raw?path=101_770000001_50000001_datasheet.pdf` | 200, `application/pdf`, 11,157 B |
| AI reasoning worksheet | `101_770000001_50000001_cheatsheet.pdf` | `/api/files/files/raw?path=101_770000001_50000001_cheatsheet.pdf` | 200, `application/pdf`, 12,172 B |

Those 200s were served through the OBO files plugin using the CLI user token (the user holds READ_VOLUME as owner).

Case 770000462 (`GET /api/cases/103/770000462/50000462`, HTTP 200, 4,892 B): NEEDS REVIEW, no letter (letter is null by design), data sheet (10,329 B) and worksheet (12,219 B) present. Its `needs_review_reason` is 3,667 characters with 9 bullets. The worklist cell shows a one-line summary (see the UI section below).

## UI: long NEEDS REVIEW reason

- Worklist cell: `summarizeReason()` gives one line, clamped to 2 lines with `break-words`; the full text is in the hover `title`.
- Case file: `ReasonList` shows every item as a bulleted list (title in bold, text nodes only, no HTML from the model), in a `max-h-40 overflow-y-auto` box.
- Other long LLM text: the letter and the AI worksheet appear only in the Text tab inside a scrollable `pre` (`max-h 60vh`). They are not shown inline in the table.
- Verified through the API payload (770000462: reason 3,667 characters, 9 items) and the reason-parser unit tests (in the 73 app tests). Visual check: NOT done (see below).

## Chat (`POST /api/appeals-chat`)

The serving endpoint `fe-bar-appeals-chat` is bound and READY. The hero-claim invocation and its trace status are in `evidence/09_chatbot.md`.

## Genie

Runs as the app service principal. The `genie-space` resource is bound with CAN_RUN; the app SP has SELECT on the five space objects and USE CATALOG/SCHEMA (`governance/04_app_sp_genie_grants.sql`).

Decision: the forwarded user token did not carry the `genie` scope after scope update, redeploy and a fresh session, so the Genie tab runs as the app SP. `server/server.ts` subclasses the AppKit Genie plugin (same routes, SSE and `<GenieChat>` contract, no `asUser` wrapper). Trade-off: Genie answers in the app reflect the app's access, not per-reviewer grants. Worklist and review actions already run as the SP; PDFs and chat stay OBO.

## Tests and build (local, 2026-11-26)

- `npm run typecheck` (server + client) and `npm run lint`: clean (re-run 2026-11-26).
- `npx vitest run` in `app/`: **73 passed** (5 test files, re-run 2026-11-26).

## UX update 2026-11-26

**Letter editing is visible in the case file.** When a saved edit exists, the Letter tab shows the edited letter as a formatted preview by default, with a version chip ("Version N · edited by <reviewer> · <relative time>") and a toggle between "Original AI draft (PDF)" and "Edited letter". With no edit, the AI draft PDF shows as before.

- **Preview:** markdown is parsed into plain blocks and rendered as React text nodes. No `dangerouslySetInnerHTML`, no HTML parsing, links keep their text only. Letter typography, a letterhead placeholder, and an RE block.
- **Show changes:** word-level inline diff of the AI draft against the latest edit (dependency-free LCS), with added and removed words highlighted and a word count.
- **Download final letter (PDF):** print-to-PDF of a body-level copy of the edited letter (no server write, no new permission). File name `<account>_<encounter>_letter_v<N>.pdf` (set as the document title for the print).
- **Save edit** shows the new version immediately (optimistic), then re-reads the case. Approve and Submit say which version they apply to ("Approve version N", or "Approve AI draft" with no edit).
- Data sheet and AI worksheet tabs are unchanged.

**Agent and Genie panel.** The right-hand panel is a sticky, viewport-height sidebar (`lg:sticky lg:top-6 lg:h-[calc(100vh-3rem)]`). The message list scrolls, the composer is pinned at the bottom, and the Genie tab's `<GenieChat>` fills the same column via `className`. Single instance below lg.

**Server (read-only).** The latest-edit query returns `version`, a count of EDIT events for the same case. No Lakebase schema change, no new writes.

**Worklist filters.** Recommendation filter chips with counts, a ">= $10K expected" toggle, and an "Expected $ (high -> low)" sort. Server-side bound parameters (recommendation, min_expected) so filters span all 500 rows. Verified against Lakebase Postgres with the real SQL: total 500 = WARRANTED 72 + NOT WARRANTED 66 + NEEDS REVIEW 42 + NOT GENERATED 320; >= $10K = 107 (WARRANTED 42); expected_desc puts the hero claim ($24,850) first.

**Known limits.**
- Diffs above ~6M table cells show the middle as one replacement, so the word count is coarse for very large rewrites.
- The Approve/Submit actions do not record the version they applied to. That would need a schema change, which was out of scope.
- Print file name depends on the browser using the document title for its default PDF name (Chrome and Safari do).

## Not verified / limits

- Browser UI: NOT verified. The app URL needs an interactive SSO session, so no screenshot was taken and the layout at 1440x900 has not been checked by eye. Every check above is an API call with a bearer token, plus the local tests and build. Look at the worklist and case file once in a browser.
- Reviewer-level UC grants (OBO) are pending, see `lakebase/APP_GRANTS.md` (current grant state; reviewer UC grants need an account-level group).
