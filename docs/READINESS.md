# Phase 5 readiness report (self-assessment, 2026-11-25) — for Naveen's review

Basis: `~/Downloads/Getting Started FE Bar.pdf` (4 domains rated Below / Meets / Exceeds; build must be an integrated
Lakeflow → UC → Lakebase → ML/GenAI → Genie Agent → App journey with text-readable execution evidence; deck leads with the
outcome and frames value for the executive sponsor and domain owner). Ratings are my estimate, not the evaluator's.

## Domain self-rating
| Domain | Self-rating | Evidence | What would raise it |
|---|---|---|---|
| **Product** | Exceeds (likely) | All six stages real and connected around one hero claim (`evidence/EVIDENCE.md` trace): Auto Loader + SDP expectations (01), job-as-code DAB with 10 tasks, 3 clean runs (08), UC tags + lineage + least-privilege grants (02), Lakebase synced table + native review log + UC catalog registration (03), `ai_query`/`ai_parse_document`/`ai_summarize` + Vector Search + LangGraph agent endpoint (04, 09), Genie Agent + metric view with benchmarks (07), AppKit app with OBO + SP split (06) | Column mask / row filter for a reviewer persona (P1); account-level reviewer group so `governance/02` can be applied |
| **Industry** | Meets → Exceeds | CARC CO50/55/57/150/186 scope, payer-routed criteria, appeal windows from public regulations (180/65/60), MPFS coding context, sourced business case (Kodiak, Optum, Premier, OIG, KFF), RCM KPIs per persona | The health system financials are search summaries (PDF/filing site blocked); BCBS criteria file is a secondary summary (cited to AZ Blue's public docs); dollar-weighted med-nec share unsourced (labelled) |
| **Build + AI Mindset** | Exceeds (if README §6 is in Naveen's words) | Text evidence for every stage; 51 Python + 24 app tests; code review with fixes (`docs/CODE_REVIEW.md`, `evidence/12`); eval vs designed ground truth 97.2% accuracy, **0% unsafe**; measured cost per appeal from `system.billing`; incremental generation + grounding cache; decisions & trade-offs in README | `mlflow.genai.evaluate` with groundedness scorers + tracing (P1, cut first per plan); README §6 rewritten by Naveen |
| **Customer Skills** | Meets (deck) — roleplay not yet prepared | Deck leads with the outcome, quantifies value in the buyers' KPIs for 4 roles, tiers with caveats, 90-day pilot + ask, architecture in appendix (`docs/deck/DECK.md`) | Roleplay rehearsal (separate follow-up, out of scope here); PDF export |

## Failure-mode check (from the FE Bar doc)
| Failure mode | Status |
|---|---|
| Internal problem, not a customer problem | ✅ Customer problem: provider revenue-cycle medical-necessity denials, grounded in a real discovery conversation (roles only) |
| Layers present but not connected | ✅ One data flow, one hero claim traced through every layer (EVIDENCE.md); review state flows back to UC and into Genie |
| Narrative opens on architecture | ✅ README §1 and deck slides 1–3 lead with the outcome; architecture is README §3 / deck appendix |

## Reproducibility
Clean data-layer reset (approved scope): landing + PDFs cleared, job tables emptied, SDP full refresh (update
`7642a160…`), then 3 full job runs (`317191832078218`, `107638099811940`, `813247927527653`) all SUCCESS → 60/120/180 appeals,
no re-generation of unchanged rows. Finding: SDP full refresh fails on an *empty* landing dir (Auto Loader schema inference);
the job is unaffected because the generator runs first.

## Attestation walkthrough (Naveen confirms each himself)
1. **"The submission is your own work."** Built in this Claude Code session (`e2e3204c-874a-4e35-bf06-2aa699e64087`) with AI
   assistance, which the FE Bar explicitly allows. Naveen made the decisions listed in `docs/SESSION_LOG.md` / HANDOFF §4.
   It extends his own earlier prototype (allowed: "You can use something you already built for a customer"). **Action:** rewrite
   README §6 "How I used AI" in your own words.
2. **"Not generated from go/solution-builder."** No Solution Builder output was used. (A `solution-builder-*` app exists in the
   shared workspace; it is unrelated and was not touched.)
3. **"You understand the consequences for misrepresentation."** Yours to confirm.
Cheating list — none apply: no one else's code, no Solution Builder, not shared, not another FE's submission, no human proxy,
not run for another person, no assessment-bypassing skill.

## Pre-commit scan (done)
- No tokens/secrets (pattern scan clean); `.gitignore` added (`*.jsonl`, `.env`, node_modules, dist, `.databricks`).
- Stray session transcript moved out of the repo; builder email + local paths redacted from docs/evidence.
- Old schema/resource names appear only in SPEC's do-not-touch list and the app test asserting their absence.
- Stale old-prototype diagrams removed.

## Open risks / blockers (decisions for Naveen)
1. **Customer-identifying content.** The FE Bar doc: "Scrub or synthesize any customer datasets, records, or customer-identifying
   content before pushing." The FAQ is silent; Builder Culture: "never publish customer-specific schemas, names or credentials".
   **DECIDED 2026-11-25: anonymized** to "a large multi-state nonprofit health system (HQ Arizona)" in repo and deck, neutral styling;
   public payer/regulatory facts kept. Record: `docs/deck/NAMING_CHECK.md`.
2. README §6 must be in Naveen's words (attestation).
3. Private EMU repo: connect GitHub on the submission form (the doc says submission is blocked if it can't read the repo).
4. The health system baseline financials are search summaries; BCBS criteria file is a secondary summary — both disclosed.
5. Reviewer UC grants need an account-level group; Genie-in-app runs as the app SP (per-user governance trade-off, documented).
6. Business-case "Likely" tier rests on an unsourced 2.0× dollar weighting (labelled; pilot validates).
7. Chat endpoint always-on (~$13.5/day) by choice.

## Final checkpoint (needs Naveen's explicit OK)
- Naming decision: anonymized 2026-11-25 (applied to repo + deck; see `docs/deck/NAMING_CHECK.md`).
- Deck PDF export → `docs/deck/` (+ DECK.md already in repo).
- `gh repo create naveen-sangana_data/med-nec-appeals-fe-bar --private`, fresh `git init`, first commit + push with the required
  attribution line, after showing the full file list + diff summary.
