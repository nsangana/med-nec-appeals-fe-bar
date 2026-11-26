# Steering log — how the builder directed the AI (2026-11-24 → 26)

Built with Claude Code (session `e2e3204c-874a-4e35-bf06-2aa699e64087`) orchestrating coordinated sub-agents against a
shared `docs/SPEC.md` + `docs/FINDINGS.md`. This log records **the builder's directions and course corrections** and what
changed because of them. The AI proposed options and did the execution; the decisions below were the builder's.
Customer = a fictional, anonymized large multi-state nonprofit health system. People are referred to by role.

## A. Solution

| # | Builder direction / correction | What the AI had proposed or done | Result |
|---|---|---|---|
| 1 | Wrote the plan of record (refined prompt): 6 connected FE Bar stages, text evidence, public sources + synthetic data, new repo + new schema, existing build untouched, checkpoints | — | `docs/SPEC.md` contract; parallel build agents; old schema/repo never modified |
| 2 | "Fan out sub-agents, don't go into rabbit holes, no slop" | — | Shared SPEC + append-only FINDINGS; each agent briefed with read-first files, hard rules, ≤N-line report; orchestrator verified every claim |
| 3 | Supplied the discovery-call context and the earlier prototype as reference | — | Customer requirements distilled (roles only): **deterministic data sheet**, automated morning worklist, no manual prompts, chat for follow-up → data sheet built in plain SQL, worklist tags (NEW/AT_RISK/PAST_DUE) |
| 4 | "Decide appeal windows from public information" (no customer-specific numbers) | Proposed 180/65/60 placeholders | Verified against 29 CFR 2560.503-1, Medicare.gov / 42 CFR 422.582, A.R.S. §36-2903.01 |
| 5 | Use only the public PDFs + xlsx from the reference volume | Copied only public references; curated CSV + old parquet excluded | Caseload 100% from the seeded generator |
| 6 | Chose the reviewer group (`fe-bar-appeals-reviewers`), later "workspace group is fine — I'm not account admin" | AI found UC grants need an account group | Workspace group for app/Genie ACLs; column masks via `is_member` |
| 7 | Approved app permissions and Genie/app ACLs explicitly (grants were never applied without a named approval) | Permission checks blocked unapproved grants | Least-privilege grants recorded in `evidence/02` |
| 8 | Reported real UI defects while verifying: NEEDS REVIEW text overflow; case-file pop-up unusable | — | Reason summarised in the cell + full list in the case file; dialog rebuilt (width cap, 92vh, tabs, fixed editor) |
| 9 | Reported chat 403 and Genie "invalid scope" errors from the live app | — | Endpoint bound with CAN_QUERY; Genie scope + redeploy; finally Genie runs as the app SP (builder approved the trade-off) |
| 10 | Asked "are we using legacy AI Gateway or model serving?" | — | Documented: hosted FMAPI endpoints for `ai_query`; one custom agent endpoint; AI Gateway inference tables |
| 11 | Asked to re-sync the worklist and grant all required app permissions | — | Lakebase grants for the app SP; data-sheet column carried into the synced table |
| 12 | Chose **anonymize** for the customer (FE Bar: scrub customer-identifying content) | AI recommended anonymize | Code, prompts, Genie, metric view, app title, docs, deck neutral; repo/bundle renamed `med-nec-appeals-fe-bar`; appeals regenerated |
| 13 | Caught the SQL failure in the generation task after the prompt change | — | Apostrophe fix + `genai/test_sql_quotes.py` regression guard |
| 14 | Approved the one-time deploy so the chat model drops the old name (v2) | — | Chat v2 live; v1 removed (builder approved cleanup) |
| 15 | Chose data-layer reset (not full schema drop) to prove reproducibility | AI laid out options | Clean rerun: landing → SDP full refresh → 3 job runs, 60/120/180 incremental |
| 16 | Revoked the broad `account users` EXECUTE grant (least privilege) | AI surfaced it | Revoked; chat verified |
| 17 | Kept the chat endpoint always-on (demo responsiveness over ~$13.5/day) | AI recommended scale-to-zero | Documented as a deliberate cost trade-off |
| 18 | Asked "is my build ready? would you change the architecture?" then chose to harden: **column masks, quote metric, MLflow tracing + eval** | AI ranked value-for-effort options | 7 PHI masks; `genai_evaluate` task with LLM judge; per-quote metrics |
| 19 | (Orchestrator caught, builder accepted) judge context must mirror the generation prompt | First judge run showed 83.3% groundedness | Judge sees what the model saw → 98.3%; drift test added |
| 20 | Wanted the evidence to show how the AI was steered (this file) | — | `docs/STEERING_LOG.md`, referenced from README §6 |
| 21 | Questioned the value of letter edits that don't update the PDF, and the chat/Genie panel needing a scroll to type; weighed effort vs demo impact and chose the no-new-permission option | Edited letter shown as a formatted preview with version chip, word-level "show changes" vs the AI draft, browser-generated final-letter PDF, "Approve version N"; sticky viewport-height chat/Genie panel with pinned input. Server-written PDFs deferred to the pilot (would need a volume write grant) |
| 22 | Reported the assistant/Genie panel still needed scrolling after the first fix; asked for recommendation and expected-$ filters; asked for parallel agents | Root cause found (panel started below the fold); rebuilt as a full-height sidebar. Filters built by two parallel agents (server query / client chips) against a shared contract; verified on Lakebase |

## B. Business case

| # | Builder direction / correction | Result |
|---|---|---|
| 1 | Treat the $12.8M hypothesis as something to validate, not defend | Sourced model: hypothesis **not supported** (NPSR basis overstated; count-weighted med-nec share) |
| 2 | Re-authenticated web search so the second pass could use real sources | Kodiak, Optum, Premier, HHS OIG, KFF, MDaudit verified at source |
| 3 | Asked "what would appeal more to an exec?" → chose three tiers (Floor / Likely / Ceiling), drop the unsourced $27M | Headline range $2M–$4M with ceiling ~$8.7M; ROI framed as payback within a quarter (one-time pilot included) |
| 4 | Set the personas: VP Revenue Cycle, CDAIO, CFO, Director of Denial Management; $12.8M only as a placeholder | `docs/STAKEHOLDERS.md`; Genie questions and deck KPIs per persona |

## C. Deck

| # | Builder direction / correction | Result |
|---|---|---|
| 1 | Personas and KPI framing per executive | Value per role on the deck |
| 2 | Iterated the title: rejected "Paid for the Care…" ("doesn't sound well"); reframed the solution as RCM-ops automation that **also** recovers revenue | Title chosen by the builder: **"Automate the Appeal. Recover the Revenue."** |
| 3 | Clarified the customer is fictional | Kept generic health-system framing; no invented brand name |
| 4 | Asked for a presenter intro with his name and title | Name on the cover (builder's later instruction) |
| 5 | "Would you present this to an exec? It looks unpolished" + supplied a reference deck whose intro slide sets the bar | v2 rebuild on the reference template, every slide thumbnail-checked |
| 6 | Proposed an exec-digestible reference-architecture slide (inspired by the Databricks reference-architecture tool), without lengthening the deck | One native-shape architecture slide replaces the text-heavy "unified platform" slide |
| 7 | Structure: **name at the bottom of the cover; slide 2 = agenda; POC ask at the end, after the demo and value** | Final slide order follows this |
| 8 | Approved using his gcloud Google token for Slides/Drive API calls so every slide could be rendered and visually QA'd | v2 deck rebuilt on the reference Databricks template (18 slides, main story 12); orchestrator reviewed thumbnails and requested 3 copy fixes before sign-off |
| 9 | Asked whether the deck flows or feels disjointed; approved the narrative pass | Main story 12 → 11 slides with chained headlines; problem slide's sources aligned with the architecture slide (payer medical-necessity criteria, not contracts); one hero denial threaded problem → workflow → demo; ROI table moved to Appendix A; speaker-note transitions on every slide |

## D. Where the AI was told "no" or slowed down (guardrails)
- Grants, group creation, sharing, deploy jobs and token use were blocked by the permission checker until the builder approved them by name; the AI never worked around a denial.
- Sub-agents could not accept relayed approvals; the orchestrator surfaced each one to the builder.
- The AI stopped rather than ship an unverified deck when it could not render thumbnails.
