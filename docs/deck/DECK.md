# Automate the Appeal. Recover the Revenue. – Medical Necessity Appeals POV (v2)

Text map of the v2 Google Slides deck (FE Bar POV), on the Databricks template. Source of truth for every number: `docs/business_case/DECK_NUMBERS.md` and the evidence files cited per slide.

- **Live deck (v2, My Drive, personal):** https://docs.google.com/presentation/d/1ifQeN8ZteE6FDAed7J9tcDzQS-TmGHNn8HcmGo58vco/edit
- **PDF (19 pages):** `docs/deck/FE_Bar_Medical_Necessity_Appeals_POV.pdf`.
- **Structure:** 12-slide main story (cover to the ask; slides 7–8 are the platform overview and its detailed reference architecture) plus 7 appendix slides (A–G). Narrative: stakes → scorecards → problem with hero denial → workflow with hero thread → platform → demo (payoff) → proof → pilot → ask.
- **Speaker notes:** on every slide. Each main-story slide (2–11) ends with a one-line transition to the next slide.
- **Architecture slide (slide 7):** built from `docs/deck/ARCH_SLIDE_SPEC.json` (geometry scaled 4:3 horizontally, 1.1× vertically; text 1.2×). Slide 8 is the detailed reference architecture (dark layered layout) added by the builder.
- **Synthetic-data rule:** all patients, payers, claims, notes and reviewer actions are synthetic; the hero patient is "a fictional patient". No customer name. No health-system-internal account data.
- **QA:** all 18 slides thumbnailed and checked for overflow and overlap; text grep for the customer name = 0. The formatting validator was not run in this pass.

## Slide list and role

| # | Title | Role in arc |
|---|---|---|
| 1 | Automate the Appeal. Recover the Revenue. | Cover (presenter: Naveen Sangana, Sr. Solutions Architect, Databricks) |
| 2 | Agenda: how a daily worklist recovers revenue already earned | Agenda (6 items) |
| 3 | $2M–$4M a year of earned revenue, at about 50¢ an appeal | Stakes: value headline |
| 4 | Every revenue-cycle leader's scorecard moves when appeals are filed on time | Stakes: scorecards by role |
| 5 | Today, each appeal is rebuilt by hand from three systems, and deadlines slip | Problem + hero intro (fictional patient, CO50, $24,850, 9 days) |
| 6 | Each morning, new denials arrive with a letter ready for approval | Workflow + hero thread (ranked #1) |
| 7 | One governed platform replaces three disconnected systems | Platform (ARCH spec) |
| 8 | Double click into the architecture and components of the solution | Platform detail: reference architecture by layer (sources → ingest, agentic AI, governance, Lakebase → serve → teams and outcomes) |
| 9 | Demo: one denial moves from worklist to approved appeal | Demo = payoff of the hero thread |
| 10 | Accurate on synthetic data; the dollars are projected | Demonstrated vs projected |
| 11 | A 90-day pilot on one payer and one code tests the value range | Pilot scope and criteria |
| 12 | We ask you to approve the pilot and name who will run it | The ask |
| 13 | Appendix A: Value method and tiers | Appendix |
| 14 | Appendix B: One job graph, governed stages, and a person approving every letter | Appendix: architecture |
| 15 | Appendix C: Patient data stays governed; reviewer grants pending | Appendix: governance |
| 16 | Appendix D: Lakeflow expectations dropped six defective claim lines before the worklist | Appendix: data quality |
| 17 | Appendix E: Proof is on synthetic data, not health system outcomes | Appendix: limitations |
| 18 | Appendix F: The value range rests on sourced rates and five inputs to validate | Appendix: value method inputs |
| 19 | Appendix G: Each benchmark has a public source; health system financials are unverified | Appendix: sources |

## Slide → source map

| # | Figures on the slide | Source |
|---|---|---|
| 1 | Title, approved subtitle, presenter line | Brief; SPEC.md |
| 2 | Agenda only | Slide order |
| 3 | $2.17M / $4.33M / $8.65M; payback 1.3 months (2.5 bottom-up); 20.2× annual return on run cost; year 1 about 6×; $0.51 per appeal | DECK_NUMBERS §1, §1b, §3, §6; COST_2B.md |
| 4 | Role KPIs; 97.2%; $0.51; $2.17M–$8.65M; payback 1.3 months | STAKEHOLDERS.md; DECK_NUMBERS §1, §3, §6 |
| 5 | Three source systems (denials and claims; clinical notes EHR; payer medical-necessity criteria); CARCs CO50, CO55, CO57, CO150, CO186; hero: CO50, $24,850 expected, 9 days | CUSTOMER_CONTEXT.md §1; SPEC.md; evidence/01 (hero gold row) |
| 6 | Step descriptions; 500 denials, rank 1 of hero; NEW, AT_RISK tags; outcome tags | evidence/01, evidence/08 |
| 7 | Platform stages; 835/837 files; 97% accurate; $2M–$4M; ~50¢ | ARCH_SLIDE_SPEC.json; DECK_NUMBERS §1, §6 |
| 8 | 835/837; CARC CO50/55/57/150/186; Genie 14/14, 5 governed objects; 538 / 532 / 500; Lakebase 500 rows; 97%, 0% unsafe; $2M–$4M; ~50¢ | evidence/01, 03, 07, 11; DECK_NUMBERS §1, §6 |
| 9 | Rank 1 of 500; $24,850 of $58,400; 9 days; AT_RISK; KL 4; KOOS 31/100; ~7 months NSAIDs; 12 PT visits | evidence/01, evidence/09, docs/SPEC.md |
| 10 | 97.2%, 175 of 180; 98.3% groundedness; 96.7%; 14 of 14 Genie; $0.51 / $0.11; 85.3% / 54.7%; outcome counts | DECK_NUMBERS §6, §6b; evidence/11, evidence/07, evidence/14 |
| 11 | Pilot measures; 68.6% benchmark; +3.4 points (assumption) | DECK_NUMBERS §4; MODEL.md I14 |
| 12 | Scope, validate-before-finance, day-90 decision, owners (roles only) | MODEL.md (five assumptions); STAKEHOLDERS.md |
| 13 | Top-down, bottom-up, return, payback, basis; $465; $12.8M hypothesis; placeholder costs | DECK_NUMBERS §1, §2, §4, §5 |
| 14 | Job graph (main path of the 12-task job); stage table; 32 PHI-tagged columns; 60 per run | resources/fe_bar_appeals.job.yml; evidence/01, 02, 04, 06, 07, 08, 09 |
| 15 | PHI masks on 7 columns; reviewer grants pending; model data-use item | evidence/02, evidence/13, lakebase/APP_GRANTS.md, lakebase/AUTH.md, data/SOURCES.md |
| 16 | Rows in/out per layer; six drops; two warnings | evidence/01 (update 7642a160…) |
| 17 | 180 of 450; 5 misclassified; criteria gap; no clinician review | evidence/11_eval_180.md; MODEL.md open issues |
| 18 | Tiers and returns; five inputs; exclusions; weighting $3.25M–$6.50M | DECK_NUMBERS §1, §2; MODEL.md (a)–(c), (g) |
| 19 | Source list and status | docs/business_case/SOURCES.md; DECK_NUMBERS §4, §5 |

Speaker notes carry the tell-show-tell structure from the v1 notes. The name "Elena Marquez" is replaced with "the fictional patient" in notes.

## Number traceability (every figure on the slides)

| Figure on slides | Value | Label | Where it comes from |
|---|---|---|---|
| Headline range | $2M–$4M a year | model output (Floor to Likely) | DECK_NUMBERS.md §1 (Floor 2.17, Likely 4.33); headline wording chosen by Naveen 2026-11-25; payback and year-1 in DECK_NUMBERS §1b |
| Floor, top-down | $2.17M a year | model output, sourced rates | DECK_NUMBERS.md §1; MODEL.md (b) |
| Likely, top-down | $4.33M a year | model output; 2.0× dollar weighting is an assumption | DECK_NUMBERS.md §1; sensitivities 1.5×–3.0× = $3.25M–$6.50M (§1 rows 59–61) |
| Ceiling, top-down | $8.65M a year | model output, sourced upside | DECK_NUMBERS.md §1; MODEL.md (b) |
| Bottom-up cross-check | $1.16M (floor, likely); $9.74M (ceiling) | model output | DECK_NUMBERS.md §1 |
| Average denied amount | $465 | industry benchmark (denied amount, not collectible) | DECK_NUMBERS.md §4 (S17 MDaudit 2025) |
| Annual return on run cost, top-down | 20.2× / 61.0× / 120.2× | model output; placeholder one-time and run costs | DECK_NUMBERS.md §1 (row 37) |
| Payback, top-down | 1.3 / 0.4 / 0.2 months | model output; placeholder costs | DECK_NUMBERS.md §1 (row 40) |
| Payback, bottom-up (Floor) | 2.5 months | model output; placeholder costs | DECK_NUMBERS.md §1 (row 39) and §1b |
| Year-1 return incl. pilot (Floor) | about 6× (5.8 unrounded) | model output; placeholder costs | DECK_NUMBERS.md §1b: ($2.17M − $0.102M − $0.216M) ÷ $0.318M |
| One-time cost (ROI basis) | $216K floor; $144K likely/ceiling | assumption to validate with the health system's RCM | DECK_NUMBERS.md §1 (Inputs I22) |
| Run cost (ROI basis) | $90K floor; $60K a year likely/ceiling | assumption to validate with the health system's RCM | DECK_NUMBERS.md §1 (Inputs I23) |
| Cost per appeal, fully loaded | $0.51 (60 a day, prototype) | prototype-measured, list price | DECK_NUMBERS.md §6; docs/business_case/COST_2B.md §C |
| Variable cost per appeal | $0.11 | prototype-measured, list price | COST_2B.md §A/§C |
| Capacity | 1.0 FTE equivalent (floor, likely) | model output | DECK_NUMBERS.md §3 (row 22) |
| Accuracy | 97.2%; 175 of 180 | prototype, synthetic data | evidence/11_eval_180.md (run f7047f94…, run_ts 2026-11-26T03:09:43Z); DECK_NUMBERS.md §6 |
| Unsafe rate | 0% | prototype, synthetic data | evidence/11_eval_180.md; DECK_NUMBERS.md §6 |
| Outcome counts | 72 WARRANTED / 66 NOT WARRANTED / 42 NEEDS REVIEW (of 180) | prototype, synthetic data | evidence/11_eval_180.md; DECK_NUMBERS.md §6 |
| Quote check | 85.3% normalised; 54.7% verbatim (180 rows); judge run 89.7% / 58.7% (60 rows) | prototype, synthetic data; metric only | DECK_NUMBERS.md §6 and §6b; evidence/11; evidence/14 |
| Groundedness | 98.3% (59 of 60) | prototype, synthetic data; LLM judge | DECK_NUMBERS.md §6b; evidence/14 §4 |
| No fabricated evidence | 96.7% (58 of 60) | prototype, synthetic data; LLM judge | DECK_NUMBERS.md §6b; evidence/14 §4 |
| PHI masks | 7 columns (name, member ID, DOB); masked outside the reviewer group and app SP | prototype governance state; non-member path logic-only | evidence/13_column_masks.md |
| Genie Agent benchmarks | 14 of 14 | prototype, synthetic data | evidence/07_genie.md |
| Records and expectations | 538 bronze, 532 silver, 500 gold; 6 dropped defects | prototype, synthetic data | evidence/01_lakeflow_pipeline.md |
| PHI-tagged columns | 32 across 11 tables | prototype governance state | evidence/02_governance.md §1 (recounted from the tag table) |
| Hero claim | rank 1; 9 days; AT_RISK; $24,850 expected of $58,400 billed | synthetic | evidence/01 (hero gold row); docs/SPEC.md |
| Hero evidence | NSAIDs ~7 months; 12 PT visits; injection ~3 weeks relief; KL grade 4; KOOS 31/100 | synthetic | evidence/09_chatbot.md; docs/SPEC.md |
| Overturn baseline | 68.6% (public benchmark) | industry benchmark (Premier) | DECK_NUMBERS.md §4 (S09) |
| Overturn lift | +3.4 points | assumption (base case) | MODEL.md input I14 (72% vs 68.6%) |
| Medical-necessity share | 6.76% (claim count); 16.26% (ceiling only) | industry benchmark | DECK_NUMBERS.md §4 (S10, S14) |
| Appeal eligibility proxy | 13% / 18% | industry benchmark (MA, 2019 sample) | DECK_NUMBERS.md §4 (S11) |
| Denial rate; write-off | 10.63% (H1 2026); 3.07% write-off; 11.6% (2025) | industry benchmark | DECK_NUMBERS.md §4 (S07, S08) |
| Hypothesis (once) | $12.8M; $12.8B revenue base; 20% share; 20% recovery | hypothesis tested and revised (not a result) | DECK_NUMBERS.md §2 and §5 rule; Appendix A (slide 13) only |
| Non-premium ceiling | $11.6B | model output | DECK_NUMBERS.md §5; not shown as a number on the slides |
| Appeal windows | 180 / 65 / 60 days | public rules; provider contracts vary | docs/business_case/SOURCES.md; data/SOURCES.md |

**Figures deliberately left off the slides:** the health system FY2023 NPSR, FY2024 revenue and premium share (search summaries only, DECK_NUMBERS §5 rule); the bottom-up upside from the pass-2 model (depends on unsourced eligibility; not in DECK_NUMBERS.md); the $1.05 health-system-scale cost figure (model only); the $67,929 synthetic lost-to-deadline figure (not in DECK_NUMBERS.md).

## Open items and known issues

- **Headline:** "$2M–$4M a year ... paying back the pilot within a quarter, even at the floor" (Naveen's wording). The multiple is labelled "annual return on run cost" everywhere; year-1 incl. pilot at floor is about 6× (DECK_NUMBERS §1b).
- **Appendix B model data use:** resolved with a public citation (docs.databricks.com Model Serving data protection; paid accounts; residency via Databricks Geos). Not verified: that the Claude endpoint carries the same terms as general Foundation Model APIs. Confirm against the health system's contract before real data. Quotes were taken through a text-extraction fetch; re-check in a browser.
- **Reference URLs (Appendix G and data/SOURCES.md):** 3 of 4 verified. Medicare.org explainer is the matching document (not a CMS document). CMS 2025 indicators: CSV from the CMS dataset is a near-match (99.7% of codes; the xlsx may be a later revision). Noridian descriptors verified. **BCBS criteria file is a secondary summary (not an AZ Blue publication); the underlying AZ Blue Provider Operating Guide section 11 and benefit-book definition are cited in data/SOURCES.md and Appendix F.**
- **Cost per appeal:** $0.51 is fully loaded at 60 appeals a day on the prototype. It rises at lower volume because the fixed cost is spread over fewer appeals; the deck does not show a volume curve.
- **Bottom-up gap:** the $465 average denied amount (all payers) may skew to professional claims. The value-method appendix labels this as a possibility that the pilot resolves.
- **Eval evidence:** the per-class table and the five misclassifications are in `evidence/11_eval_180.md`; Appendix D uses them.
- **Generator:** the laterality defect is fixed in the regenerated run (no laterality misses remain). Open: the five WARRANTED misses are three SCS trial charts and two bariatric cases; one bariatric case's payer criteria document is not in the criteria corpus (a genuine criteria gap). Not regenerated.
- **Customer naming: DECIDED 2026-11-25, anonymized.** Customer name, logo and branding removed from the deck, text and speaker notes. Record: `docs/deck/NAMING_CHECK.md`.
- **Reviewer grants:** Appendix C says UC grants are pending (account-level group needed). Nothing on the slides claims they are in place.
- **Genie in the app:** answers run as the app service principal, a trade-off approved for the demo. The appendix slides carry this caveat.
- **Hardening:** column masks on 7 PHI columns (`evidence/13`) and the GenAI judge (`evidence/14`) are on the slides; the job graph shows `genai_evaluate`. Stage-20 mask retention was verified on 2026-11-26. The non-member mask path is still logic-level only.
- **Export:** v2 PDF (19 pages) at `docs/deck/FE_Bar_Medical_Necessity_Appeals_POV.pdf`.
- **Cover slide:** the deck title is the cover title; the approved subtitle sits under it. Every content slide has an assertion title.
