# Business case source register (pass 2)

Retrieval date for every entry: **2026-11-24**. Public sources only.

**Verification status key:** *Verified* = figure read on the source page or PDF itself this session. *Search summary* = figure taken from a search-engine summary because the source returned 403, a parse error, or Cloudflare; it is **not** verified at source and is labelled wherever used. Anything not listed here is not used as a number.

## Health system baseline (NPSR and revenue)

> **Note:** customer-identifying links withheld from the public artifact; on file.

Customer-identifying links (the system's own filings and financial pages, trade-press articles that name it, and tax-filing identifiers) are withheld from this public artifact. They are on file in the private Sheet. Each entry below states the source type, date and status.

### S06: Modeled health system's public FY2023 audited financial statements (NPSR)
- **Link:** withheld from public artifact; on file (private Sheet)
- **Publisher:** the health system's public municipal-disclosure filing (audited consolidated statements)
- **Date:** audited statements for years ended Dec 31, 2023 and 2022
- **Figure used:** net patient service revenue 2023 = **$9,643,407 thousand (~$9.643B)** (Input I01)
- **Status:** **Search summary only.** The filing site returned HTTP 403 to WebFetch. The figure is quoted by a search summary that cites this filing and its Consolidated Statements of Operations.
- **Population:** consolidated health system.
- **Limitations:** not opened; FY2024 audited NPSR was not retrieved (open item). The FY2023 figure is used because FY2024 is not available from a retrieved source (instruction followed).
- **Label:** public fact (search-summary; not verified at source)

### S04: Modeled health system's public financial highlights, FY2024 and FY2025 editions, retrieved 2026-11-24
- **Link:** withheld from public artifact; on file (private Sheet)
- **Publisher:** the health system
- **Figures used:** total revenues FY2024 **$15,593,202,000** (I25); FY2023 **$14,068,126 thousand** (I28, growth check only); FY2025 $15,969,658,000 (noted, not used)
- **Status:** **Search summary only.** The publisher's pages returned Cloudflare 403 (curl) and a WebFetch header-parse error. Two independent search summaries agree on the FY2024 and FY2023 totals.
- **Limitations:** consolidated per the highlights title; line items not reproduced. Not the audited NPSR line.
- **Label:** public fact (search-summary; not verified at source)

### S05: Trade-press summary of the health system's FY2024 operating results (March 2025)
- **Link:** withheld from public artifact; on file (private Sheet)
- **Publisher:** Hospital trade press (summary of the health system's March 14, 2025 report)
- **Figures used:** premium (insurance) revenue = **25.4%** of FY2024 operating revenue (I26; base of I07); FY2024 operating margin **2.3%** (I27, context only)
- **Status:** **Search summary only.** The article page returned HTTP 403.
- **Limitations:** secondary summary. The 25.4% is a revenue share, used as a proxy for the plan's share of claims (I07). Not a claim count.
- **Label:** public fact (search-summary; not verified at source)

### S02: Health plan affiliate Form 990 (TY2024, TY2023), via public nonprofit-filing database
- **Link:** withheld from public artifact; on file (private Sheet)
- **Publisher:** public nonprofit-filing database (IRS Form 990)
- **Figures used:** total revenue TY2024 $214,827,195; TY2023 $106,024,165 (I24, memo)
- **Used for:** confirms the health plan files as a separate filer, so plan premium revenue sits outside NPSR.
- **Status:** verified at source (pass 1).
- **Label:** public fact

### S01: Health system parent Form 990, via public nonprofit-filing database. **Superseded as NPSR basis.**
- **Link:** withheld from public artifact; on file (private Sheet)
- **Figures:** total revenue TY2024 $10,839,690,022; TY2023 $9,479,573,911 (pass 1, verified at source)
- **Why superseded:** a single filer entity, not the consolidated system. Cross-check: the TY2023 total revenue on this filer ($9.48B) is **below** consolidated FY2023 NPSR ($9.64B), so the filer cannot be the consolidated system. Kept for audit trail only; no model input uses it.

## Industry benchmarks (used as inputs)

### S07: Kodiak Solutions H1 2026 benchmark (via TechTarget)
- **URL:** https://www.techtarget.com/revcyclemanagement/news/366651012/Insurers-deny-less-just-to-claw-back-more-later-analysis
- **Publisher:** TechTarget (reporting Kodiak proprietary revenue-cycle data)
- **Date:** article published 2026-09-23; period H1 2026 vs H1 2025
- **Population:** 2,400 hospitals and 375,000 physicians on the Kodiak platform
- **Figures used:**
  - initial denial rate (% of claims): **10.63%** H1 2026 (12.00% H1 2025): Input I08 conservative
  - final denial write-offs: **3.07% of net revenue** H1 2026 (**3.31%** H1 2025): Input I03 base (3.07%) and upside (3.31%)
- **Status:** verified at source (article text)
- **Limitations:** vendor (Kodiak) customer base, not a random sample. Denial rate is claim-count based. The write-off denominator is "net revenue"; treated as NPSR (HFMA AR-6 defines it as net patient service revenue; the HFMA PDF was not opened). Not audited.
- **Label:** industry benchmark

### S08: Kodiak Solutions "State of the healthcare revenue cycle" 2025 (via TechTarget)
- **URL:** https://www.techtarget.com/RevCycleManagement/news/366641065/Hospitals-lost-over-48B-from-claims-denials-uncollected-bills
- **Publisher:** TechTarget (Kodiak inaugural report)
- **Date:** article published 2026-04-02
- **Population:** 2,300 hospitals and 350,000 physicians
- **Figures used:** average initial denial rate **11.6%** (2025), **11.4%** (2024). Used for I08 base (11.6%) and the I03 write-off source.
- **Corrections:** a search summary had quoted 11.81% for 2024; the article says **11.4%**. The $48.4B "lost revenue" figure combines final denials and uncollected patient bills, so it is not used as a write-off input.
- **Status:** verified at source (article text)
- **Label:** industry benchmark

### S09: Premier 2025 survey on hospital claims adjudication costs
- **URL:** https://premierinc.com/newsroom/policy/claims-adjudication-costs-providers-257-billion-18-billion-is-potentially-unnecessary-expense
- **Publisher:** Premier Inc.
- **Date:** published 2025-02-24; survey fielded Aug 8 2024 to Feb 4 2025; claims year 2023
- **Population:** 280 hospitals across 23 states, 48,000+ acute-care beds (self-reported survey)
- **Figures used:**
  - administrative cost per claim: **$43.84 (2022) to $57.23 (2023)**: cost cross-check for I16 (÷ $55/h = 0.80 / 1.04 h)
  - denial rate: "**nearly 15 percent**": I08 upside
  - overturn: **68.6%** (methodology) and **70%** (headline) of denials ultimately overturned and paid: I13 base (68.6%) and upside (70%)
- **Status:** verified at source (article text)
- **Limitations:** survey, not random; cost is administrative cost per denied claim, not time per appeal; no medical-necessity split; the two overturn figures differ (68.6 vs 70); "per claim" wording vs "per contested denial" in some summaries.
- **Label:** industry benchmark

### S10: Optum (Change Healthcare) 2024 Revenue Cycle Denials Index (PDF)
- **URL:** https://marketplace.optum.com/content/dam/change-healthcare/marketplace-assets/outcomes-and-insights/2024-denials-index.pdf
- **Publisher:** Optum (formerly Change Healthcare)
- **Date:** 2024 index; 2023 data
- **Population:** ~124 million hospital claim remits valued at $500B in charges, 1,400+ US hospitals
- **Figures used:**
  - average denial rate **12%** of claims (2023): cross-check for I08
  - **medical necessity 6.76%** of denials, 2023 average: I04 and I09 conservative and base
  - 84% of denials potentially avoidable; 22% of those not recoverable (context)
- **Status:** verified at source (PDF text; figures read from the category chart on p. 11 and the summary on p. 3)
- **Limitations:** vendor data; claim-count basis, not dollars; category definitions set by vendor. A dollar-weighted med-nec share may be higher (not verified).
- **Label:** industry benchmark

### S11: HHS OIG, Medicare Advantage denials that met Medicare coverage rules (OEI-09-18-00260)
- **URL:** https://oig.hhs.gov/oei/reports/OEI-09-18-00260.pdf
- **Publisher:** HHS Office of Inspector General
- **Date:** April 2022 (sample: June 1-7, 2019)
- **Population:** stratified random sample of 500 MA denials (250 prior-auth, 250 payment) from the 15 largest MA organizations; 430 eligible cases reviewed
- **Figures used:**
  - **13%** of MA prior-authorization denials met Medicare coverage rules: I10 conservative (13%)
  - **18%** of MA payment denials met Medicare coverage rules and MAO billing rules: I10 base (18%)
- **Status:** verified at source (PDF text)
- **Limitations:** Medicare Advantage only; one-week 2019 sample; small sample (wide confidence intervals); measures compliance with coverage rules, not appealability. It is a proxy for the clinically supportable share, applied to med-nec denials. OIG covers all denial reasons. Treat I10 as a **proxy**, not a measure.
- **Label:** industry benchmark (proxy)

### S12: KFF, Medicare Advantage insurers' 2024 prior authorization determinations
- **URL:** https://www.kff.org/medicare/medicare-advantage-insurers-made-nearly-53-million-prior-authorization-determinations-in-2024/
- **Publisher:** KFF (Jan 28, 2026)
- **Population:** 52.8M MA prior-authorization determinations in 2024 (CMS Limited Data Set)
- **Figures used:** 7.7% of requests denied (in full or part); **11.5% of denials appealed**: reference for I11 (current appeal rate); **80.7%** of appeals partially or fully overturned (context for I13/I14)
- **Status:** verified at source (article text, via WebFetch summary)
- **Limitations:** MA only; appeal counts not reported directly; denial-based appeal share is not a hospital-claim appeal rate. No hospital appeal rate is verified.
- **Label:** industry benchmark (context)

### S13: KFF, insurer-reported prior authorization metrics (2025 data)
- **URL:** https://www.kff.org/patient-consumer-protections/prior-authorization-metrics-provide-new-insights-into-insurer-practices-but-gaps-remain/
- **Publisher:** KFF (Aug 13, 2026)
- **Population:** 14 insurers (each at least 2.5% share in its segment); ~25M MA, 35M+ Medicaid managed care, ~11M ACA enrollees
- **Figures used:** **67%** of initially denied standard PA requests overturned on appeal (MA); 47% Medicaid managed care; 43% ACA Marketplace. Context for I14.
- **Status:** verified at source (article text, via WebFetch summary)
- **Limitations:** insurers report percentages, not counts (so appeal volumes are unknown); incomplete coverage (for example, 83% of one insurer's MA enrollment); first year of required reporting; individual insurers range 40%–93%.
- **Label:** industry benchmark (context)

### S14: CDI Week 2025 Industry Overview Survey (HCPro / ACDIS)
- **URL:** https://acdis.org/sites/acdis/files/cdi-week/Industry-Report-CDI-Week-2025.pdf
- **Publisher:** ACDIS / HCPro
- **Date:** 2025 (Figure 33, "Average percentage of denials in each category")
- **Population:** hospital CDI professionals (self-reported)
- **Figures used:** medical necessity **16.26%** of denials handled by CDI teams (2025); 18.03% (2024); 23.80% (2023). Upside for I04 and I09.
- **Status:** verified at source (PDF text)
- **Limitations:** share of the denials CDI teams handle, not all denials; self-reported; not claims-level. Weak; used only as the upside.
- **Label:** industry benchmark (weak)

### S15: AHA, Costs of Caring 2026 (press release, 2026-03-11)
- **URL:** https://www.aha.org/press-releases/2026-03-11-new-aha-report-hospitals-face-increased-challenges-and-financial-pressures-they-care-patients
- **Publisher:** American Hospital Association
- **Figure used (context only):** hospitals spent **$43 billion in 2025** trying to collect payments from insurers for care already delivered. Verified at source.
- **Not verified:** the "nearly $18 billion to overturn denials" split. The search claim does not appear on the press release page. Not used.
- **Label:** context only (not an input)

## Dollar weighting and per-claim value (added 2026-11-25)

### S17: MDaudit Annual Benchmark Report, 2025 Edition (average denied amounts)
- **URL:** https://19712.fs1.hubspotusercontent-na1.net/hubfs/19712/Benchmark%20Report%202025.pdf (publisher site: www.mdaudit.com)
- **Date:** 2025 edition (2025 data, with 2023–2024 comparatives)
- **Figures used:**
  - RFI / medical-necessity denials, all payers: average denied amount **$294 (2024) to $465 (2025)**, section G. Basis for I15 (Floor and Likely) at **$465**.
  - Information-needed / medical-necessity denials, professional + hospital chart: **$450 (2025)**; $286 (2024); $249 (2023). Cross-check, I35.
  - Hospital inpatient $5,390 and outpatient $565 (2025), section A. Context only (I36, I37).
- **Status:** verified at source (PDF text, downloaded and extracted this session)
- **Population:** MDaudit client base (claims-audit vendor); mixed payers and settings.
- **Limitations:** this is a **denied amount, not collectible**; no collectible haircut applied (flagged). No med-nec split by setting. The report does **not** give a dollar-share versus count-share ratio, so it cannot test the multiplier. The inpatient and outpatient mix is unknown for med-nec denials, so the $465 is not a health-system value.
- **Label:** industry benchmark (per-claim denied amount)

### S16: NYC Health Care Accountability Report 2026 (not-medically-necessary denials, dollars vs claims)
- **URL:** https://www.nyc.gov/assets/doh/downloads/pdf/about/healthcare-accountability-report-2026.pdf
- **Figure used:** "Not medically necessary" = **9% of denied dollars vs 2% of denied claims** (2024, NY-regulated plans). Ratio **4.5x**. Cited upper bound for the multiplier (I32).
- **Status:** **search summary only.** Direct fetch returned "Access Denied". Not verified at source.
- **Population:** NY-regulated plans (not hospital claims). The count share (2%) is well below Optum's 6.76%, so the ratio is not directly transferable.
- **Label:** industry benchmark (search summary; cited upper bound only)

### Multiplier basis (I29, `medcc_dollar_weight_multiplier`)
- No verified public source gives a hospital-claims dollar share for medical-necessity denials. Optum (S10) is count-only. MDaudit (S17) has no dollar-share ratio.
- The only dollar-vs-count ratio found is NYC (S16): 4.5x, unverified and not a hospital dataset.
- **Likely = 2.0x** is a judgment, labelled "assumption to validate in pilot". It is the geometric midpoint of 1.0x (no skew) and 4.5x (NYC), rounded: sqrt(1.0 x 4.5) = 2.1. Sensitivities: 1.0x, 1.5x, 3.0x, 4.5x (Model rows 59–62). Each is a formula result, not a tuned input.

### S18: COST_2B.md, prototype platform cost measured at list price
- **Source:** `docs/business_case/COST_2B.md` (workspace `system.billing.usage` at list price, usage date 2026-11-24, queried 2026-11-25).
- **Figures used:** variable cost per appeal **$0.107** (LLM $0.069); fixed own resources **$8,900/yr** ($11,300 incl. shared Vector Search); fully loaded at 60 appeals/day **$0.51**.
- **Status:** measured (prototype, synthetic workload). This is **not the health system data** and **not Databricks account data**. The health system's contracted rates and production sizing would differ.
- **Label:** prototype-measured, list price

## Not used, or not verified

| Item | Status |
|---|---|
| MGMA $25.20 per claim to rework (medical practices, 2021) | search summary only; practice setting, not used |
| Change Healthcare $118 per appealed denial (2017) | search summary only; old; not used |
| HFMA MAP Key AR-6 definition (2023 MAP Keys PDF) | definition only (search); PDF not opened |
| AKASA appeal-submission time (~10 min 18 s) | not found in open materials; not used |
| APTA 30+ min per appeal (PT practices); trade-press ASC 45-60 min letter | search only; different setting; not used |
| PubMed PMID 42326895 (OTO Open 2026, MA head and neck surgery) | abstract not retrieved; not used |
| KFF ACA Marketplace med-nec share (~6%) | search only; not used |
| FY2024 audited NPSR and FY2024 audited statements | **not retrieved**: open item for RCM |
| The health system FY2025 NPSR | not retrieved |

## Corrections made in pass 2 versus pass 1 and the search results

- The health system baseline: Form 990 total revenue ($10.84B) replaced by FY2023 NPSR ($9.64B, search summary) and FY2024 total operating revenue ($15.59B, search summary). Form 990 is a single filer.
- Kodiak 2024 denial rate: 11.4% (article), not 11.81% (search).
- Premier overturn: 68.6% (methodology) vs 70% (headline); both shown.
- AHA: $18B overturn split not verified; only the $43B total is used (context).

## Summary of what could not be verified at source

1. The health system FY2024 total operating revenue and the 25.4% premium share (the publisher's PDF and the trade-press article both blocked). Two search summaries agree on the revenue total; the trade-press summary is the only source for 25.4%.
2. FY2023 NPSR $9.64B (filing site blocked; search summary).
3. Any hospital-level appeal rate and any hospital-level staff time per appeal (no verified source).
4. Dollar-weighted medical-necessity share (only claim-count figures verified).
