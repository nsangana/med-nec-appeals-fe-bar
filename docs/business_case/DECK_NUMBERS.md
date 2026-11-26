# Deck numbers: single source of truth (FE Bar Health System POV)

Every $, %, count and ratio the deck uses is listed here, once, with its label and source. If a number is not in this file, do not put it in the deck. Model outputs come from `MODEL.md` and the Sheet (https://docs.google.com/spreadsheets/d/1rHqmmLWK1FPXBLosbTqQcNnEuabjqXslimmLAV7400g/edit). Retrieval date 2026-11-24; prototype metrics from the regenerated 180-row eval (run `f7047f94…`, run_ts 2026-11-26T03:09:43Z; see `evidence/11_eval_180.md`).

**Labels:** `public fact` · `industry benchmark` · `assumption to validate with the health system's RCM` · `model output` · `prototype, synthetic data` (never a health-system result).

**Verification status:** `verified` = read at source this session. `search summary` = source blocked (403 or parse error); use only after checking. **Do not put a search-summary figure on a slide without confirming it.**

## 1. Headline financials (model outputs, all illustrative)

Tiers: **Floor** = sourced base; **Likely** = Floor × dollar multiplier 2.0x (assumption); **Ceiling** = sourced upside rates.

| Number | Floor | Likely | Ceiling | Label | Source / status |
|---|---|---|---|---|---|
| Top-down incremental recovery, $M/yr | 2.17 | **4.33** | 8.65 | model output (Likely multiplier is an assumption) | MODEL.md (b); Model row 6 |
| Bottom-up incremental recovery, $M/yr | 1.16 | 1.16 | 9.74 | model output | MODEL.md (c); Model row 17 |
| Bottom-up, if med-nec value also × 2.0, Likely, $M | — | 2.32 | — | sensitivity | Model row 63 |
| Top-down at dollar multiplier 1.5x / 3.0x / 4.5x, Likely, $M | — | 3.25 / 6.50 / 9.75 | — | sensitivity | Model rows 59–61 |
| Net benefit, top-down, $M/yr | 2.06 | 4.26 | 8.58 | model output | Model row 35 |
| Net benefit, bottom-up, $M/yr | 1.06 | 1.09 | 9.67 | model output | Model row 36 |
| Total annual cost (platform + run), $ | 102,314 | 69,914 | 71,372 | model output | Model row 34 |
| One-time implementation, $ | 216,000 | 144,000 | 144,000 | assumption to validate with the health system's RCM | Inputs I22 |
| Annual run cost (people), $ | 90,000 | 60,000 | 60,000 | assumption to validate with the health system's RCM | Inputs I23 |
| Annual return on run cost, top-down (net ÷ annual cost) | 20.2x | 61.0x | 120.2x | model output | Model row 37 |
| Annual return on run cost, bottom-up (net ÷ annual cost) | 10.3x | 15.6x | 135.4x | model output | Model row 38 |
| Payback, top-down, months | 1.3 | 0.4 | 0.2 | model output | Model row 40 |
| Payback, bottom-up, months | 2.5 | 1.6 | 0.2 | model output | Model row 39 |
| Cost to collect (annual cost ÷ bottom-up recovery) | 8.8% | 6.0% | 0.7% | model output | Model row 42 |
| Recovery as margin points on FY2024 operating revenue (top-down), bps | 1.4 | 2.8 | 5.5 | model output; context | Model row 55 |

**Returns and payback** rest on a one-time cost and run cost that are placeholders with rationale (see Inputs I22, I23). Show them only with that caveat. "Annual return on run cost" = net benefit ÷ total annual cost (platform + run, Model row 34). It is not a return on the one-time cost; use the year-1 figure below for that.

### 1b. Payback and year-1 return, Floor (added 2026-11-25)

Floor values from Model rows 34, 35, 36, 39, 40 and Inputs I22. Recomputed from the inputs on 2026-11-25; all match MODEL.md (f).

| Number | Value | Label | Formula | Source / status |
|---|---|---|---|---|
| Payback, top-down, months (Floor) | 1.3 (1.25 unrounded) | model output, placeholder costs | one-time ÷ (net benefit top-down ÷ 12) = 0.216 ÷ (2.0677 ÷ 12) | Model row 40 |
| Payback, bottom-up, months (Floor) | 2.5 (2.45 unrounded) | model output, placeholder costs | 0.216 ÷ (1.0577 ÷ 12) | Model row 39 |
| Year-1 return incl. pilot, top-down (Floor) | **about 6×** (5.8 unrounded) | model output, placeholder costs | ($2.17M − $0.102M − $0.216M) ÷ $0.318M = 1.852 ÷ 0.318 | recomputed; MODEL.md (f) gives the inputs |
| Annual return on run cost, top-down (Floor) | 20.2× | model output | net ÷ annual cost = 2.0677 ÷ 0.102314 | Model row 37 |

Rules for the deck: payback is "within a quarter, even at the floor" (both methods are under 3 months); the year-1 figure is always shown with its formula or footnote; do not present any of these as a return on the health system's actual cost.

## 2. Sensitivities to show (not headline)

| Number | Value | Label | Source |
|---|---|---|---|
| Bottom-up at eligibility 13% (OIG prior-auth share), Floor, $M | 0.84 | model output | Model row 65 |
| Bottom-up at all-claims value $804 instead of $465, Floor, $M | 2.00 | model output | Model row 64 |
| Top-down with no dollar weighting (1.0x), Floor, $M | 2.17 | model output | Model row 62 |
| Dollar multiplier needed for $12.8M at Floor rates | **5.9x** | model output | MODEL.md (b); 12.8 ÷ 2.17 |

## 3. Capacity and cost-per-appeal (model outputs)

| Number | Floor | Likely | Ceiling | Label | Source |
|---|---|---|---|---|---|
| Net admin hours saved per year | 1,832 | 1,832 | 19,071 | model output | Model row 21 |
| FTE equivalent saved | 1.0 | 1.0 | 10.6 | model output | Model row 22 |
| Appeals per FTE, baseline | 1,731 | 1,731 | 1,200 | assumption (I16) | Model row 24 |
| Appeals per FTE, post | 3,600 | 3,600 | 5,143 | assumption (I17) | Model row 25 |
| cost_per_appeal_usd, fully loaded, health-system-scale model | $1.30 | $1.05 | $0.32 | model output (prototype-measured inputs) | Model row 32 |
| Admin cost per appeal after (labour + platform) | $28.80 | $28.55 | $19.57 | model output | Model row 43 |
| Labour cost per appeal, baseline (Premier cross-check $57.23) | $57.20 | $57.20 | $82.50 | benchmark cross-check / assumption | Model row 57 |

## 4. Public benchmarks (cited on the appendix slide)

| Number | Value | Label | Source | Status |
|---|---|---|---|---|
| Initial denial rate, hospital claims, 2025 | 11.6% | industry benchmark | S08 Kodiak 2025 (techtarget 2026-04-02) | verified |
| Initial denial rate, H1 2026 | 10.63% | industry benchmark | S07 Kodiak H1 2026 (techtarget 2026-09-23) | verified |
| Initial denial rate, "nearly 15 percent" | ~15% | industry benchmark | S09 Premier 2025 (280 hospitals, 2023 claims) | verified |
| Final denial write-off, % of net revenue, H1 2026 | 3.07% | industry benchmark | S07 Kodiak (3.31% in H1 2025) | verified |
| Med-nec share of denials, count, 2023 average | 6.76% | industry benchmark | S10 Optum 2024 Denials Index | verified |
| Med-nec share of CDI-handled denials, 2025 | 16.26% | industry benchmark (weak, self-reported) | S14 ACDIS CDI Week 2025 | verified |
| Denials that met Medicare coverage rules: prior auth / payment | 13% / 18% | industry benchmark (MA only, 2019 sample) | S11 HHS OIG OEI-09-18-00260 | verified |
| Share of MA denials appealed, 2024 | 11.5% | industry benchmark (MA) | S12 KFF (2026-01-28) | verified |
| Share of MA appeals overturned, 2024 | 80.7% | industry benchmark (MA) | S12 KFF | verified |
| Share of initially denied MA standard PA overturned on appeal, 2025 | 67% | industry benchmark (MA; 14 insurers) | S13 KFF (2026-08-13) | verified |
| Share of denials ultimately overturned and paid, hospitals, 2023 | 68.6% (methodology) / 70% (headline) | industry benchmark | S09 Premier | verified; use 68.6% |
| Admin cost per claim to adjudicate/contest, 2022 → 2023 | $43.84 → $57.23 | industry benchmark | S09 Premier | verified |
| Average denied amount, RFI / med-nec denials, all payers, 2025 | $465 (up from $294 in 2024) | industry benchmark (denied amount, not collectible) | S17 MDaudit 2025 | verified |
| Average denied amount, hospital inpatient / outpatient, 2025 | $5,390 / $565 | industry benchmark (context) | S17 MDaudit 2025 | verified |
| Hospitals' spend collecting from insurers, 2025 | $43 billion | industry benchmark (context) | S15 AHA Costs of Caring 2026 | verified (the $18B overturn split is NOT verified; do not use) |

## 5. Health system public figures (use with care)

| Number | Value | Label | Source | Status |
|---|---|---|---|---|
| FY2023 net patient service revenue | $9.64B | public fact | S06 Health system audited FY2023 (public filing) | **search summary**: filing site 403 |
| FY2024 total operating revenue | $15.59B | public fact | S04 Health system FY2024 highlights | **search summary**: PDF 403 |
| Premium (health plan) share of FY2024 operating revenue | 25.4% | public fact | S05 Trade-press summary of health system report | **search summary**: 403 |
| FY2024 operating margin | 2.3% | public fact | S05 | **search summary** |
| Form 990 total revenue (single filer, do NOT use as NPSR) | $10.84B | public fact, superseded | S01 public nonprofit-filing database | verified; not NPSR |
| FY2024 non-premium operating revenue ceiling (memo) | $11.6B | model output | Model row 46 | derived from two search summaries |
| Implied premium share in the $12.8B hypothesis | 17.9% | model output | Model row 47 | derived |

**Rule:** the $12.8M figure appears only as "reference placeholder, to be validated". Never present it as a result.

## 6. Prototype metrics (synthetic data, not the health system results)

All labelled **prototype, synthetic data**. Sources are repo evidence files, not the health system data.

| Number | Value | Label | Source |
|---|---|---|---|
| Encounters evaluated, latest eval run | 180 | prototype, synthetic data | `evidence/11_eval_180.md` (run `f7047f94…`, run_ts 2026-11-26T03:09:43Z) |
| Accuracy vs generator ground truth | **97.2%** (0.9722; 175 of 180) | prototype, synthetic data | `evidence/11_eval_180.md`, latest eval |
| Unsafe rate (approved where it should not be) | **0.0%** | prototype, synthetic data | `evidence/11_eval_180.md` |
| Parse failures | 0 | prototype, synthetic data | `evidence/11_eval_180.md` |
| Quote-verified rate, normalised / strict verbatim | 85.3% / 54.7% | prototype, synthetic data | `evidence/11_eval_180.md` |
| Appeals by recommendation: WARRANTED / NOT WARRANTED / NEEDS REVIEW | **72 / 66 / 42** (of 180) | prototype, synthetic data | `evidence/08_job_run.md` (run 3); Lakebase worklist agrees (`evidence/03_lakebase.md`) |
| Letters generated (WARRANTED only) | 72 | prototype, synthetic data | `evidence/04_genai_generation.md` |
| End-to-end job runs | 3 of 3 runs SUCCESS, 10 of 10 tasks each (60 → 120 → 180 appeals), before `genai_evaluate` was added (job now 12 tasks) | prototype, synthetic data | `evidence/08_job_run.md` |
| Variable platform cost per appeal (LLM $0.069 of $0.107) | $0.11 ($0.107 unrounded) | prototype-measured, list price | `docs/business_case/COST_2B.md` (S18) |
| Fixed platform cost, own resources, per year | $8,900 (incl. shared VS: $11,300) | prototype-measured, list price | COST_2B.md |
| Fully loaded cost per appeal at prototype scale (60/day, own resources) | **$0.51** | prototype-measured, list price | COST_2B.md |
| Fully loaded at 60/day incl. shared VS / with chat scale-to-zero | $0.62 / ~$0.29 | prototype-measured, list price | COST_2B.md |

## 6b. GenAI evaluation (MLflow, LLM judge, 60 rows) and quote framing

Source: `evidence/14_mlflow_genai_eval.md` (job run `263358598052015`, judge `databricks-claude-sonnet-4-6`, 60 most recent generations). All labelled **prototype, synthetic data** and **LLM judge**.

| Number | Value | Label | Source |
|---|---|---|---|
| Groundedness (built-in RetrievalGroundedness) | **98.3%** (59 of 60) | prototype, synthetic data; LLM judge | evidence/14 §4 |
| No fabricated evidence (Guidelines judge) | **96.7%** (58 of 60) | prototype, synthetic data; LLM judge | evidence/14 §4 |
| Determination matches designed label (deterministic) | 95.0% (57 of 60) | prototype, synthetic data | evidence/14 §4 (3 WARRANTED→NEEDS REVIEW) |
| Unsafe calls in the same 60 rows | 0 | prototype, synthetic data | evidence/14 §4 |
| Quote verified, per quote, **normalised** (judge run) | **89.7%** (593 of 661 spans) | prototype, synthetic data; metric only | evidence/14 §4 |
| Quote verified, per quote, strict verbatim (judge run) | 58.7% (388 of 661 spans) | prototype, synthetic data; metric only | evidence/14 §4 |
| Judge cost estimate, 60 rows | $2.41 (measured billing pending) | estimate | evidence/14 §7 |
| Judge cost estimate, full 180 rows (not run) | about $7.2, above the $5 cap | estimate | evidence/14 §7 |

**Quote framing (use in this order).**
1. Lead with per-quote **normalised**: 89.7% on the 60-row judge run; 85.3% on the 180-row deterministic eval (`evidence/11_eval_180.md`).
2. Then the strict figure: 58.7% (judge run) and 54.7% (180 rows).
3. Explain the strict gap: PDF-extraction artefacts in the criteria text (for example fused footnote digits and bullet glyphs) and genuine paraphrase. The cause is described in `evidence/04_genai_generation.md` (quote verification) and `evidence/14_mlflow_genai_eval.md`.
4. Pair the quote figures with groundedness 98.3% and unsafe 0%.
5. Do not show the row-level strict pass (0%, because one unverified span fails a row) as a quote metric.

**Caveats for the slide:** list prices, not the health system contracted rates. Warehouse and pipeline costs are allocations. The eval labels are generator ground truth on synthetic data.

## 7. Headline (current)

- **Business outcome (cover subtitle, set by Naveen 2026-11-26):** "Recover legitimate healthcare revenue, prevent avoidable write-offs and reduce the administrative burden of medical necessity appeals through timely, clinically grounded, AI-assisted appeal preparation."
- **Headline (value slide):** "An expected $2M–$4M a year of earned revenue, paying back the pilot within a quarter." The per-appeal cost is no longer in the headline: $0.51 is platform cost only, and reviewer time to approve and file is separate (Naveen, 2026-11-26).
- Support for "within a quarter": top-down payback 1.3 months and bottom-up 2.5 months at Floor (section 1b). Any multiple is labelled "annual return on run cost" (net ÷ annual cost, excludes the one-time cost). Year-1 return including the pilot at Floor is about 6×. Do not present 20.2× as a return on the pilot.
- Basis: $2.17M (Floor, top-down) to $4.33M (Likely, top-down) per year; $0.51 per appeal (prototype fully loaded, 60/day, COST_2B); 20.2× annual return on run cost, top-down, at Floor (Model row 37).
- The tier table shows **Ceiling $8.65M** (top-down, sourced upside rates) and **bottom-up as a lower cross-check** (Floor and Likely $1.16M; Ceiling $9.74M). Show both, with the bottom-up cross-check in the table, not hidden.
- Caveats that must travel with the headline: the Likely $4.33M depends on the unsourced 2.0x dollar multiplier (sensitivity $3.25M at 1.5x and $6.50M at 3.0x). Payback and ROI rest on placeholder implementation and run costs. Cost per appeal is prototype list-price, not the health system contracted rates.
- Cost per appeal: **$0.51** (prototype, 60/day) is the deck figure, always labelled **platform cost per appeal**; it excludes reviewer time. The health-system-scale model's $1.30 (Floor) / $1.05 (Likely) are platform cost for the model; labour plus platform is about $57 → $29 per appeal at Floor (§3).
