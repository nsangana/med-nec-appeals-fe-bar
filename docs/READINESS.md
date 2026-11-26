# Readiness report (self-assessment, final state) — for Naveen's review

Basis: the FE Bar getting-started guide (PDF; 4 domains rated Below / Meets / Exceeds; build must be an integrated
Lakeflow → UC → Lakebase → ML/GenAI → Genie Agent → App journey with text-readable execution evidence; deck leads with the
outcome and frames value for the executive sponsor and domain owner). Ratings are my estimate, not the evaluator's.

## Domain self-rating
| Domain | Self-rating | Evidence | What would raise it |
|---|---|---|---|
| **Product** | Exceeds | All six stages real and connected around one hero claim (`evidence/EVIDENCE.md` trace): Auto Loader + SDP expectations (01); job-as-code DAB with 12 tasks, three full 10-task runs before `genai_evaluate` was added (08); UC tags, lineage, least-privilege grants and **column masks on 7 PHI columns** with workspace-group + app-SP exemption and retention verified (02, 13); Lakebase synced table + native review log + UC catalog registration (03); `ai_query` / `ai_parse_document` / `ai_summarize` + Vector Search + LangGraph agent endpoint (04, 09); Genie Agent + metric view, 14 of 14 (07); AppKit app with OBO + SP split (06); MLflow GenAI judge on stored generations (14) | Reviewer UC grants applied once an account-level group exists (`lakebase/APP_GRANTS.md`) |
| **Industry** | Meets → Exceeds | CARC CO50/55/57/150/186 scope, payer-routed criteria, appeal windows from public regulations (180/65/60), MPFS coding context, sourced business case (Kodiak, Optum, Premier, OIG, KFF), RCM KPIs per persona | The health system financials are search summaries (PDF/filing site blocked); BCBS criteria file is a secondary summary (cited to AZ Blue's public docs); dollar-weighted med-nec share unsourced (labelled) |
| **Build + AI Mindset** | Exceeds (if README §6 is in Naveen's words) | Text evidence for every stage; **79 Python + 73 app tests**; code review with fixes (`docs/CODE_REVIEW.md`, `evidence/12`); eval vs designed ground truth 97.2% accuracy (175 of 180), **0% unsafe**; LLM judge on 60 rows (groundedness 98.3%, no fabricated evidence 96.7%, label match 95.0%); measured cost per appeal from `system.billing`; incremental generation + grounding cache; decisions & trade-offs in README | Judge on all 180 rows (blocked by the $5 cost cap; estimate about $7.2); README §6 rewritten by Naveen |
| **Customer Skills** | Meets (deck v2 + app) — roleplay not yet prepared | Deck v2 ("Automate the Appeal. Recover the Revenue.") leads with the outcome: 12-slide main story plus appendix, quantifies value in the buyers' KPIs for 4 roles, tiers with caveats, 90-day pilot + ask, PDF exported (`docs/deck/`); app with a worklist, case file and assistant sidebar (`docs/deck/DECK.md`) | Roleplay rehearsal (separate follow-up, out of scope here) |

## Failure-mode check (from the FE Bar doc)
| Failure mode | Status |
|---|---|
| Internal problem, not a customer problem | ✅ Customer problem: provider revenue-cycle medical-necessity denials, grounded in a real discovery conversation (roles only) |
| Layers present but not connected | ✅ One data flow, one hero claim traced through every layer (EVIDENCE.md); review state flows back to UC and into Genie |
| Narrative opens on architecture | ✅ README §1 and deck slides 1–3 (cover, agenda, value headline) lead with the outcome; architecture is README §3 / deck appendix |

## Reproducibility
Clean data-layer reset (approved scope): landing + PDFs cleared, job tables emptied, SDP full refresh (update
`7642a160…`), then three full job runs (`317191832078218`, `107638099811940`, `813247927527653`), all SUCCESS → 60/120/180 appeals,
no re-generation of unchanged rows. Those runs were 10 tasks each; `genai_evaluate` and `cost_views` were added afterwards, so the job now has 12.
Finding: SDP full refresh fails on an *empty* landing dir (Auto Loader schema inference); the job is unaffected because the
generator runs first.

## Attestation walkthrough (Naveen confirms each himself)
1. **"The submission is your own work."** Built in this Claude Code session (`e2e3204c-874a-4e35-bf06-2aa699e64087`) with AI
   assistance, which the FE Bar explicitly allows. Naveen made the decisions listed in `docs/SESSION_LOG.md` §2.
   It extends his own earlier prototype (allowed: "You can use something you already built for a customer"). README §6 "How I used AI"
   is written in his own words.
2. **"You understand the consequences for misrepresentation."** Yours to confirm.
Cheating list — none apply: no one else's code, not shared, not another FE's submission, no human proxy,
not run for another person, no assessment-bypassing skill.

## Pre-commit scan (done)
- No tokens/secrets (pattern scan clean); `.gitignore` added (`*.jsonl`, `.env`, node_modules, dist, `.databricks`).
- Stray session transcript moved out of the repo; builder email + local paths redacted from docs/evidence.
- Old schema/resource names appear only in SPEC's do-not-touch list and the app test asserting their absence.
- Stale old-prototype diagrams removed.
- Customer-name scan over tracked files: 0 hits.

## Publication (done)
- Private EMU repo `naveen-sangana_data/med-nec-appeals-fe-bar` (full history).
- Public mirror `nsangana/med-nec-appeals-fe-bar` (clean snapshot of the final tree).
- Naming decision: anonymized 2026-11-25 (repo, deck and speaker notes; see `docs/deck/NAMING_CHECK.md`).

## Open risks / blockers (decisions for Naveen)
1. **README §6 must be in Naveen's words (attestation).** It is still marked DRAFT and is not edited here.
2. **Reviewer UC grants need an account-level group.** `governance/02_reviewer_grants.sql` is written but not applied. Until then the reviewer OBO path relies on grants the group does not hold (`lakebase/APP_GRANTS.md`). Everything else for the app and Genie is applied.
3. **Non-member column-mask path is verified at logic level only.** The member path reads real values; a non-member read has not been run against a non-member principal. Lakebase copies, appeal PDFs and SDP-managed tables are unmasked (`evidence/13_column_masks.md` §5).
4. **Customer-identifying history.** The customer-name token appears in two older EMU commits in the private repo's history. The public mirror is a clean snapshot without that history. Decide whether the private repo's history needs rewriting before submission; the file tree is clean.
5. **Roleplay prep.** The deck and app are ready to present; the rehearsal is not done.
6. The health system baseline financials are search summaries; BCBS criteria file is a secondary summary; both are disclosed.
7. Business-case "Likely" tier rests on an unsourced 2.0× dollar weighting (labelled; pilot validates).
8. Chat endpoint always-on (about $13.5/day) by choice; the scale-to-zero decision is open.
9. Submission form: confirm it can read the private EMU repo (the FE Bar doc says submission is blocked if it cannot).
