# FE Bar medical-necessity appeals: business case model (PASS 2, three tiers, Checkpoint 2b costs)

Status: **DRAFT for Naveen's review. Not for the deck.** Retrieval date 2026-11-24 (costs measured 2026-11-24 usage, queried 2026-11-25). Sources in `SOURCES.md` (each row tagged verified / search summary / measured). The Sheet mirrors this file: `Inputs` → `Model`, formulas only. Sheet: https://docs.google.com/spreadsheets/d/1rHqmmLWK1FPXBLosbTqQcNnEuabjqXslimmLAV7400g/edit. Deck figures: `DECK_NUMBERS.md`.

## Changes vs pass 1

1. **Tiers renamed.** Conservative / Base / Upside are now **Floor / Likely / Ceiling**.
   - **Floor** = the sourced base from the previous revision (count-weighted med-nec 6.76%, write-off 3.07%, eligibility 18%, denial rate 11.6%, overturn 68.6% to 72%).
   - **Likely** = Floor plus `medcc_dollar_weight_multiplier` (I29) = **2.0x**.
   - **Ceiling** = the sourced upside rates (top-down $8.7M).
2. **Dollar weighting (new, I29).** The multiplier converts the count-based med-nec share into a share of write-off **dollars**. It applies to the top-down pool only. No public hospital-claims dollar share was found. Likely = 2.0x is a labelled assumption (geometric midpoint of 1.0x and the NYC 4.5x, search summary only). Sensitivities at 1.0x, 1.5x, 3.0x and 4.5x are in Model rows 59–62.
3. **Eligibility capped at sourced values.** I10 = 18% in every tier (OIG payment-denial share). The unsourced 50% is removed, which removes the $27M bottom-up upside. The 13% OIG prior-auth share is a sensitivity (Model row 65).
4. **Bottom-up per-claim value replaces NPSR ÷ all claims.** I15 is now the **med-nec denied amount**: $465 per denied claim (MDaudit 2025, all payers, S17) in Floor and Likely; the all-claims average ($804, NPSR ÷ claims, I15a) in Ceiling. Both are shown. $465 is a **denied amount, not collectible**; no collectible haircut is applied, so it is an upper bound for the floor.
5. **Costs now measured (COST_2B.md, S18).** Variable $0.107 per appeal (Ceiling $0.069, LLM-only). Fixed platform $8,900/yr own resources (Floor $11,300 incl. shared Vector Search). Both are labelled prototype-measured, list price. Production sizing at the health system volume is **not** in the tiers.
6. **Implementation and run costs have one-line rationales.** Pilot on one payer/CARC for 12 weeks at 2.0 FTE blended = 960 h × $150/h = $144,000 (Floor $216,000, +50% overrun). Run = 0.5 FTE ops × $120k loaded = $60,000 (Floor 0.75 FTE = $90,000).
7. **Carried from the previous revision:** NPSR anchor FY2023 ($9.64B, search summary); hypothesis replay uses H01–H03; capacity is net of baseline hours; bottom-up uses incremental wins only.

## Bottom line

- **Likely top-down is $4.3M/yr** (Floor $2.2M, Ceiling $8.7M). Likely sits inside the $4–6M target, and nothing was tuned to reach it. **The Likely result depends almost entirely on the unsourced 2.0x multiplier.** The sensitivity is $3.3M at 1.5x and $6.5M at 3.0x.
- **Likely bottom-up is $1.2M/yr** (Floor $1.2M, Ceiling $9.7M). It does not converge with Likely top-down (ratio 0.27). The cause is the $465 med-nec denied amount, which is already med-nec specific and so is not scaled by the multiplier. Scaling it too gives $2.3M, still well below top-down.
- **Ceiling methods converge** (top-down $8.7M, bottom-up $9.7M, ratio 1.13). The Ceiling bottom-up uses the unsourced 85% improved appeal rate and the NPSR-implied $804 value, so treat that agreement with caution.
- **The $12.8M hypothesis is still not supported.** At Floor rates it needs a dollar multiplier of **5.9x**, above the highest public ratio found (4.5x, NYC, search summary). At Ceiling rates it needs 1.5x more than the ceiling. Recommended deck wording on Naveen's review: "illustrative incremental recovery of about $4M a year (range $2M–$9M), pending RCM validation of the dollar weighting and appeal eligibility."
- **Economics stay positive in all tiers.** Total annual cost (platform + run) is $70k–$102k at health-system-scale volume. Fully loaded cost per appeal is $1.30 / $1.05 / $0.32 (Floor / Likely / Ceiling). Payback is under three months in every tier.
- **Capacity is about 1 FTE net in Floor and Likely** and about 11 FTE in Ceiling. Capacity depends on appeal volume rising, not only on faster review.

## (a) Inputs

Labels: **public fact** / **industry benchmark** / **assumption to validate with the health system's RCM** / **prototype-measured**. Row numbers match the `Inputs` tab. Verification detail is in `SOURCES.md`.

| Row | ID | Input | Unit | Floor | Likely | Ceiling | Label | Source |
|---|---|---|---|---|---|---|---|---|
| 2 | I01 | NPSR anchor, FY2023 audited | $M | 9,643.4 | 9,643.4 | 9,643.4 | public fact (search summary; filing site 403) | S06 |
| 3 | I02 | NPSR hypothesis (comparison only) | $M | 12,800 | 12,800 | 12,800 | assumption (hypothesis) | none |
| 4 | I03 | Final denial write-off, % of NPSR | % | 3.07% | 3.07% | 3.31% | industry benchmark | S07, S08 |
| 5 | I04 | Med-nec share of denials, COUNT basis | % | 6.76% | 6.76% | 16.26% | industry benchmark (Ceiling: weak survey) | S10, S14 |
| 6 | I05 | Recovery of med-nec write-off (derived) | % | 10.8% | 10.8% | 16.7% | derived (formula) | I13, I14 |
| 7 | I06 | Annual provider claims, all payers | count | 12,000,000 | 12,000,000 | 12,000,000 | assumption | none |
| 8 | I07 | Share of claims adjudicated by health plan (excluded) | % | 25.4% | 25.4% | 20% | assumption (proxy: premium share) | S05 |
| 9 | I08 | Initial denial rate, hospital claims | % | 11.6% | 11.6% | 15% | industry benchmark | S08, S09 |
| 10 | I09 | Med-nec share of denials, bottom-up (count) | % | 6.76% | 6.76% | 16.26% | industry benchmark | S10, S14 |
| 11 | I10 | Appeal-eligible share of med-nec denials | % | 18% | 18% | 18% | benchmark proxy, capped at sourced max | S11 |
| 12 | I11 | Current appeal rate among eligible | % | 50% | 50% | 50% | assumption | context S12 |
| 13 | I12 | Improved appeal rate among eligible | % | 75% | 75% | 85% | assumption (**Ceiling 85% unsourced**) | none |
| 14 | I13 | Baseline overturn rate | % | 68.6% | 68.6% | 70% | industry benchmark | S09 |
| 15 | I14 | Improved overturn rate | % | 72% | 72% | 75% | assumption (lift) | context S12, S13 |
| 16 | I15 | Med-nec denied value per denied claim | $ | 465 | 465 | 804 | benchmark (denied amount, not collectible) / Ceiling = NPSR-implied | S17 |
| 17 | I16 | Admin hours per appeal, baseline | hours | 1.04 | 1.04 | 1.50 | benchmark cross-check / Ceiling assumption | S09 |
| 18 | I17 | Admin hours per appeal, post | hours | 0.50 | 0.50 | 0.35 | assumption | none |
| 19 | I18 | Productive hours per admin FTE per year | hours | 1,800 | 1,800 | 1,800 | assumption | none |
| 20 | I19 | Loaded cost per admin hour (avoidance only) | $/hr | 55 | 55 | 55 | assumption | none |
| 21 | I20 | variable_cost_per_appeal_usd | $ | 0.107 | 0.107 | 0.069 | **prototype-measured, list price** (Ceiling = LLM-only) | COST_2B (S18) |
| 22 | I21 | annual_fixed_platform_cost_usd | $/yr | 11,300 | 8,900 | 8,900 | **prototype-measured, list price** (Floor incl. shared VS) | COST_2B (S18) |
| 23 | I22 | One-time implementation cost | $ | 216,000 | 144,000 | 144,000 | assumption (rationale below) | none |
| 24 | I23 | Annual run cost (people) | $/yr | 90,000 | 60,000 | 60,000 | assumption (rationale below) | none |
| 25 | I24 | The health system's health plan affiliate revenue FY2024 (memo) | $ | — | 214,827,195 | — | public fact | S02 |
| 26 | I25 | The health system total operating revenue FY2024 (memo) | $M | 15,593.2 | 15,593.2 | 15,593.2 | public fact (search summary; PDF 403) | S04 |
| 27 | I26 | Premium share of FY2024 operating revenue (memo) | % | 25.4% | 25.4% | 25.4% | public fact (search summary; 403) | S05 |
| 28 | I27 | FY2024 operating margin (memo) | % | 2.3% | 2.3% | 2.3% | public fact (search summary) | S05 |
| 29 | I28 | The health system total operating revenue FY2023 (memo) | $M | 14,068.1 | 14,068.1 | 14,068.1 | public fact (search summary) | S04 |
| 30–32 | H01–H03 | Hypothesis: 2.5% write-off, 20% med-nec, 20% recovery | % | — | 2.5% / 20% / 20% | — | assumption (replay only) | none |
| 33 | **I29** | **medcc_dollar_weight_multiplier** (dollar share ÷ count share) | x | 1.0 | **2.0** | 1.0 | **assumption to validate in pilot** (range 1.5–3.0) | S16, S17 |
| 34 | I15a | Average collectible per claim, all claims (NPSR ÷ claims) | $ | 804 | 804 | 804 | derived (formula) | I01, I06 |
| 35 | I30 | Multiplier sensitivity, low | x | — | 1.5 | — | assumption (sensitivity) | none |
| 36 | I31 | Multiplier sensitivity, high | x | — | 3.0 | — | assumption (sensitivity) | none |
| 37 | I32 | Cited multiplier bound (NYC: 9% of $ vs 2% of claims) | x | — | 4.5 | — | search summary, unverified | S16 |
| 38 | I33 | Eligibility sensitivity, OIG prior-auth share | % | — | 13% | — | benchmark (sensitivity) | S11 |
| 39 | I34 | MDaudit med-nec average denied amount, all payers, 2025 | $ | — | 465 | — | benchmark, verified (denied amount) | S17 |
| 40 | I35 | MDaudit info-needed / med-nec chart, 2025 | $ | — | 450 | — | benchmark, verified (chart; cross-check) | S17 |
| 41 | I36 | MDaudit hospital inpatient denied amount, 2025 | $ | — | 5,390 | — | context only | S17 |
| 42 | I37 | MDaudit hospital outpatient denied amount, 2025 | $ | — | 565 | — | context only | S17 |

**Implementation and run cost rationale (I22, I23).**
- One-time (Likely and Ceiling $144,000): pilot on one payer/CARC for 12 weeks at 2.0 FTE blended (0.5 Databricks SA, 1.0 health-system RCM analyst, 0.5 the health system's IT) = 960 h × $150/h. Floor adds a 50% overrun ($216,000).
- Run (Likely and Ceiling $60,000): 0.5 FTE ops and reviewer support × $120k loaded. Floor uses 0.75 FTE ($90,000). Platform run cost is in I21.
- Both are assumptions to validate with the health system. Neither is benchmarked.

## (b) Top-down: NPSR → write-off → med-nec dollars → recovery

| Step | Formula | Floor | Likely | Ceiling |
|---|---|---|---|---|
| NPSR anchor ($M) | I01 | 9,643.4 | 9,643.4 | 9,643.4 |
| Final denial write-off ($M) | I01 × I03 | 296.1 | 296.1 | 319.2 |
| Med-nec write-off ($M) | × I04 × I29 | 20.0 | **40.0** | 51.9 |
| Recovery share (derived) | I05 | 10.8% | 10.8% | 16.7% |
| **Incremental recovery ($M/yr)** | × I05 | **2.17** | **4.33** | **8.65** |

The $12.8M hypothesis replay (Model row 7) is still $12.8M at its own inputs. Holding the Floor pool and recovery share, $12.8M needs a multiplier of **5.9x** (12.8 ÷ 2.17). Ceiling needs 1.5x more than its $8.65M result (Model row 50 gives the share of pool needed).

## (c) Bottom-up: denied claims × eligibility × appeal rate × overturn × value

| Step | Formula | Floor | Likely | Ceiling |
|---|---|---|---|---|
| External claims | I06 × (1 − I07) | 8,952,000 | 8,952,000 | 9,600,000 |
| Denied claims | × I08 | 1,038,432 | 1,038,432 | 1,440,000 |
| Med-nec denials | × I09 (count) | 70,198 | 70,198 | 234,144 |
| Appeal-eligible | × I10 | 12,636 | 12,636 | 42,146 |
| Current wins | eligible × I11 × I13 | 4,334 | 4,334 | 14,751 |
| Improved wins | eligible × I12 × I14 | 6,823 | 6,823 | 26,868 |
| Incremental wins | improved − current | 2,489 | 2,489 | 12,117 |
| Appeals processed (improved) | eligible × I12 | 9,477 | 9,477 | 35,824 |
| **Incremental recovery ($M/yr)** | incremental wins × I15 | **1.16** | **1.16** | **9.74** |

The multiplier is **not** applied to bottom-up counts or to the $465 value (already med-nec specific). Applying it to the value as well gives Likely $2.32M (Model row 63).

**Reconciling the methods.** Floor bottom-up ÷ top-down = 0.53. Likely = 0.27. Ceiling = 1.13. In Floor, incremental wins split into an overturn-rate effect of 215 (9%) and an appeal-volume effect of 2,274 (91%). The volume effect (I11 → I12, 50% → 75%) is unsourced. The gap between Likely methods is the dollar weighting: top-down scales the pool by 2.0x and bottom-up does not.

## (d) Scenario results

| Method | Floor | Likely | Ceiling | Driven by |
|---|---|---|---|---|
| Top-down incremental recovery | $2.17M | **$4.33M** | $8.65M | write-off (Kodiak), med-nec (Optum; ACDIS ceiling), overturn (Premier), **multiplier (Likely: unsourced 2.0x)** |
| Bottom-up incremental recovery | $1.16M | **$1.16M** | $9.74M | eligibility (OIG proxy), appeal-volume lift (unsourced), value $465 (Floor/Likely) or $804 (Ceiling) |
| Sensitivity: top-down at 1.5x / 3.0x / 4.5x (Likely) | — | $3.25M / $6.50M / $9.75M | — | multiplier range |
| Sensitivity: bottom-up at eligibility 13% (OIG PA) | $0.84M | $0.84M | $7.03M | eligibility proxy |

Net benefit, top-down (recovery − annual cost): Floor **$2.06M**, Likely **$4.26M**, Ceiling **$8.58M**. Net benefit, bottom-up: Floor $1.06M, Likely $1.09M, Ceiling $9.67M.

## (e) Capacity

| Metric | Floor | Likely | Ceiling |
|---|---|---|---|
| Net admin hours saved per year (baseline on current appeals − post on processed) | 1,832 | 1,832 | 19,071 |
| FTE equivalents saved (÷ 1,800 h) | 1.0 | 1.0 | 10.6 |
| FTE needed after automation (processed × I17 ÷ 1,800) | 2.6 | 2.6 | 7.0 |
| Appeals per FTE, baseline (1,800 ÷ I16) | 1,731 | 1,731 | 1,200 |
| Appeals per FTE, post (1,800 ÷ I17) | 3,600 | 3,600 | 5,143 |
| Labour cost per appeal, baseline (I16 × I19) | $57.20 | $57.20 | $82.50 |

Capacity is excluded from net benefit to avoid double-counting.

## (f) Platform cost per appeal, net benefit, ROI and payback

`cost_per_appeal_usd` (derived) = (variable + fixed platform cost) ÷ appeals processed. This is the **health-system-scale model** with the prototype fixed cost. It is not production sizing.

| Metric | Floor | Likely | Ceiling |
|---|---|---|---|
| variable_cost_per_appeal_usd (I20, prototype-measured) | $0.107 | $0.107 | $0.069 |
| annual_fixed_platform_cost_usd (I21, prototype-measured) | $11,300 | $8,900 | $8,900 |
| **cost_per_appeal_usd, fully loaded (derived)** | **$1.30** | **$1.05** | **$0.32** |
| Run cost (I23) | $90,000 | $60,000 | $60,000 |
| Total annual cost (platform + run) | $102,314 | $69,914 | $71,372 |
| One-time implementation (I22) | $216,000 | $144,000 | $144,000 |
| ROI, top-down (net ÷ annual cost) | 20.2x | 61.0x | 120.2x |
| ROI, bottom-up | 10.3x | 15.6x | 135.4x |
| Payback, top-down (months) | 1.3 | 0.4 | 0.2 |
| Payback, bottom-up (months) | 2.5 | 1.6 | 0.2 |
| Cost to collect (annual cost ÷ bottom-up recovery) | 8.8% | 6.0% | 0.7% |
| Admin cost per appeal after (I17 × I19 + cost per appeal) | $28.80 | $28.55 | $19.57 |

Checkpoint 2b: the variable and fixed costs are now **measured** (prototype, list price). The ROI and payback figures are still model outputs. They are not meaningful as a CFO case until the implementation and run costs are validated with the health system.

## (g) CFO confidence

### What drives variance
1. **Dollar multiplier (I29).** Likely top-down moves from $2.2M (1.0x) to $9.8M (4.5x). The 2.0x is an assumption, not a source.
2. **Appeal eligibility (I10).** Capped at 18%. The OIG range is 13% to 18%. At 13%, bottom-up Floor falls from $1.16M to $0.84M.
3. **Per-claim value (I15).** $465 (MDaudit denied amount, not collectible) vs $804 (NPSR ÷ claims). The bottom-up result scales linearly with this.
4. **Med-nec share (I04).** 6.76% (Optum, count) to 16.26% (ACDIS, survey). This is the Ceiling driver.
5. **Appeal-volume lift (I12).** Unsourced. It is 91% of Floor bottom-up value.

### Five assumptions the health system's RCM must validate first
1. **Dollar weighting of med-nec denials** (I29): the ratio of med-nec share of denied dollars to share of claims. This is the largest single driver of Likely top-down. Pull denial dollars by CARC from the denial-management system.
2. **Appeal eligibility** (I10): timely, post-service, clinically supportable med-nec denials. Current 18% is an OIG MA proxy.
3. **Current appeal and overturn rates, by payer and CARC** (I11, I13): the baseline that defines any lift.
4. **Average collectible value per med-nec denied claim** (I15): the MDaudit $465 is denied, not collectible; the health system collectible may be higher or lower.
5. **Admin hours per appeal today** (time study, I16/I17), plus annual claim count and health-plan claim share (I06, I07).

### Verdict on the $12.8M hypothesis: **NOT SUPPORTED. REVISED.**
- **NPSR is overstated** in the hypothesis: $12.8B is above the FY2024 non-premium operating revenue ceiling of $11.6B. The implied premium share would be 17.9% against the reported 25.4%. Evidence: S04, S05 (search summaries), S06 (search summary).
- **Med-nec share is overstated** on count: 20% vs 6.76% (Optum). The dollar weighting can lift the dollar share above count, but not to the hypothesis level without evidence.
- **Recovery share** at 20% is above the derived 10.8%.
- **Net:** $12.8M needs a 5.9x dollar multiplier at Floor rates. The highest public ratio found is 4.5x (NYC, search summary). At Ceiling rates it needs ~1.5x more.

**Recommended deck wording (for Naveen's decision):** "illustrative incremental recovery of about $4M a year (range $2M–$9M), pending RCM validation of the dollar weighting and appeal eligibility." Bottom-up Likely ($1.2M) is below the headline and should be shown.

## (h) KPI map (persona → KPI → model output)

| Persona | KPI | Model output | Status |
|---|---|---|---|
| VP of Revenue Cycle | Final denial write-off $ | Top-down write-off, row 4 | Benchmark-anchored (Kodiak) |
| VP of Revenue Cycle | Overturn rate | Rows 14–15 (I13 Premier, I14) | Baseline benchmarked; lift assumed |
| VP of Revenue Cycle | Appeal eligibility | Row 13; I10 | Proxy (OIG); key open item |
| VP of Revenue Cycle | Recoverable revenue | Rows 6 and 17 | Likely top-down $4.3M; bottom-up $1.2M |
| VP of Revenue Cycle | Days to appeal / on-time filing % | Not modelled | Gap; needs RCM deadline data |
| VP of Revenue Cycle | Cost to collect | Row 42 | Derived |
| CDAIO | Cost per appeal | Row 32 (I20, I21) | Prototype-measured inputs; model output |
| CDAIO | AI accuracy / unsafe rate | Not a financial output | Prototype, synthetic data (see DECK_NUMBERS.md) |
| CFO | Incremental revenue recovery | Rows 6 and 17; sensitivities rows 59–65 | Range |
| CFO | Net financial benefit | Rows 35 and 36 | Assumption-driven beyond top-down |
| CFO | ROI, payback | Rows 37–40 | Placeholder implementation and run costs |
| CFO | Operating margin | Rows 55–56 | Context only |
| Director of Denial Management | Appeal preparation time | I16 / I17; net hours row 21 | Cross-check only; time study needed |
| Director of Denial Management | Appeals processed per employee | Rows 24–25 | Derived |
| Director of Denial Management | Backlog reduction | Not modelled | Gap |
| Director of Denial Management | Admin cost per appeal | Row 43; labour cross-check row 57 | Derived |

## Open issues

- **Sheet write blocked for the Sources tab and one note.** The Sheet's Sources tab does not yet have rows S16–S18, and the Inputs note on I35 (row 40) still says "Model row 64 uses I34". Both need a Sheet write that the automatic permission check blocked this session. The Inputs and Model values are already correct. **Needs Naveen to approve or re-run.**
- **The multiplier (I29) is an assumption.** The 1.5x–3.0x range and the 2.0x base are judgments. The NYC 4.5x is a search summary that did not open at source.
- **Likely top-down and bottom-up disagree (0.27).** The gap is the dollar weighting: top-down scales the pool and bottom-up does not. Resolve with denial-dollar data, not by tuning either input.
- **Bottom-up value (I15) is a denied amount, not collectible.** The $465 is a vendor client sample, mixed across payers and settings.
- **Health system financials are search summaries only** (PDF and filing site blocked). FY2024 audited NPSR not retrieved.
- **No hospital appeal rate or time-per-appeal benchmark** verified. I11, I12 and I17 are assumptions. Ceiling I12 (85%) is unsourced.
- **Cost inputs are prototype-measured** (list price, synthetic workload). Production sizing at the health system volume is a separate assumption and is not in the tiers.
- **Checkpoint 2b:** the variable and fixed platform costs are measured. The health system contracted rates would differ.
