# Data sources (FE Bar)

Retrieval date for everything below: 2026-11-24.

## Public reference files (raw_references volume)

The four files live in `appeals_hackathon_catalog.fe_bar_appeals.raw_references`. Each was copied with `fs cp` (read-only) and
checked against the public page on 2026-11-25. Status: **3 of 4 verified at source; the BCBS file is a secondary summary, with its underlying AZ Blue public sources listed.**

| File | What it is (from first page / name) | Source URL | Retrieved / check |
|---|---|---|---|
| `BCBS_Med_Nec_Criteria.pdf` | **Secondary summary** (not an AZ Blue publication): a compiled summary of BCBS Arizona's medical-necessity vs experimental/investigational definitions (Commercial, MA, Exchange, DSNP) with footnoted policy references | No public page matches the file verbatim. **Underlying public AZ Blue sources it summarises:** (1) 2025 AZ Blue Provider Operating Guide, Section 11 *Medical Policies and Prior Authorization* (criteria sources EviCore/MCG/ASH/NCCN; InterQual→MCG on 2023-11-01): https://edge.sitecorecloud.io/bluecross-6f8ea2ea/media/project/bcbs-az/azblue/data/media/files/providers/e-learning/11-medical-policies-and-prior-authorization-provider-operating-guide.pdf ; (2) AZ Blue benefit-book definition *"Medical necessity definition, guidelines, and criteria"* (e.g. 2026 HMO EverydayHealth Prosano benefit book): https://edge.sitecorecloud.io/bluecross-6f8ea2ea/media/project/bcbs-az/benefit-books-and-sbcs/individual-plan-documents/on-exchange-2026/benefit-books/hmo-everydayhealth-prosano-base-on-exchange-benefit-book.pdf | 2026-11-25: underlying sources located via search (not opened at source); footnote-to-source mapping not verified. Treat the file as a summary, and cite AZ Blue's own documents in the deck/README. |
| `Definition_of_Med_Nec.pdf` | "What Does 'Medically Necessary' Mean?" (last updated 2025-09-27), quoting CMS bullets | https://www.medicare.org/articles/what-does-medically-necessary-mean/ . **Publisher is Medicare.org (non-government), not CMS.** Title, "Last updated September 27, 2025", the CMS bullets and the "Not Medically Necessary Services and Supplies" section all match the file. | 2026-11-25: verified |
| `2025_MPFS_Indicator_Listing.xlsx` | CMS 2025 Part B MPFS indicator listing (19,116 code rows after load; header "2025 Part B Medicare Physician Fee Schedule Indicators") | https://catalog.data.gov/dataset/indicators-for-2025 (CMS, updated 2025-07-23); CSV resource https://pfs.data.cms.gov/sites/default/files/data/indicators2025-06-10-2025.csv . **Near-match, not byte-identical:** after stripping the `*` change flags, 19,028 of 19,082 unique code/modifier pairs in the xlsx appear in the CSV (99.7%); status (S) agrees on 19,033 of 19,061 shared rows (99.9%) and global (GLB) on 19,053 (99.96%). The xlsx is probably a later revision. | 2026-11-25: near-match (verified to the same dataset family) |
| `MPFS_Indicator_Descriptors_-_JE_Part_B_-_Noridian.pdf` | Noridian JE Part B MPFS indicator descriptors (a print of the web page; the first-page image shows the NOTE-#, PROCEDURE/MOD, LIMITING CHARGE rows) | https://med.noridianmedicare.com/web/jeb/fees-news/fee-schedules/mpfs/mpfs-indicator-descriptors (page title "MPFS Indicator Descriptors - JE Part B - Noridian", last updated Jul 25, 2025; descriptor tables match) | 2026-11-25: verified |

## Regulatory sources for appeal windows

Copied from docs/SPEC.md ADDENDUM 2 (2026-11-24). These are the publicly sourced appeal windows used by the generator
(`generator/catalog.py`, `PAYER_LIMITS`). Caveats are reproduced as written.

| PAYER_TYPE | Days | Public basis (retrieved 2026-11-24) | Caveat |
|---|---|---|---|
| COMMERCIAL | 180 | 29 CFR 2560.503-1(h)(3)(i): group health plans must allow "at least 180 days following receipt of a notification of an adverse benefit determination" (https://www.law.cornell.edu/cfr/text/29/2560.503-1); ACA 45 CFR 147.136 adopts it | Member-appeal floor used as a proxy; provider contract appeal windows vary and are often shorter (assumption to validate with RCM) |
| MEDICARE_ADVANTAGE | 65 | Medicare.gov: "must file an appeal within 65 days from the date on the initial denial notice" (https://www.medicare.gov/providers-services/claims-appeals-complaints/appeals/medicare-health-plans); 42 CFR 422.582 | Some online copies of 422.582 still say 60 days (pre-2019 text); contracted-provider disputes follow the plan contract |
| MEDICAID (AHCCCS, AZ) | 60 | A.R.S. §36-2903.01(B)(4): claim grievance "within sixty days after the date of the denial of a timely claim submission" (or 12 months from DOS / eligibility posting, whichever is later) (https://www.azleg.gov/ars/36/02903-01.htm) | Modelled conservatively as 60 days from denial (the 12-month alternative isn't modelled); other states' Medicaid windows are out of scope; only AHCCCS is generated |

Only one Medicaid payer is generated: `AHCCCS Medicaid`.

## Synthetic caseload (not a public source)

The 500-encounter caseload, its ~1,000 clinical notes, and the `eval_case_labels` ground truth are SYNTHETIC. They come
from the seeded generator in `generator/` (seed `20261124`, `n_encounters=500`, as_of `2026-11-24`). All names,
addresses, member ids, tax ids and facility names are fictional. Payer names are generic routing labels. The hero
claim (Elena Marquez) is fixed by the SPEC. Regenerate with `python -m generator --seed 20261124 --n 500 --as-of 2026-11-24`.

## Model data use (Appendix B, deck slide 13)

Retrieved 2026-11-25 from docs.databricks.com. Quotes were taken through a text-extraction fetch, so re-check the wording in a browser before quoting it externally.

- Model Serving data protection, https://docs.databricks.com/aws/en/machine-learning/model-serving/ : "For all paid accounts, Model Serving does not use user inputs submitted to the service" and "or outputs from the service to train any models or improve any Databricks services." Scope: paid accounts only. Foundation Model APIs run on Model Serving.
- Same page, Data retention: Databricks "may temporarily process and store inputs and outputs for the purposes of preventing, detecting, and mitigating abuse"; inputs and outputs are "isolated from those of other customers" and "stored in the same region as your workspace for up to thirty (30) days."
- Same page, residency: "Foundation Model APIs is a Databricks Designated Service, meaning it adheres to data residency boundaries as implemented by Databricks Geos."

Not verified: that the Claude endpoints used in this build (`databricks-claude-sonnet-4-6`) carry the same terms as the general Foundation Model APIs page. Confirm against the health system's contract and the account's terms before any real data.
