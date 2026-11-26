# Stakeholder map (decided by Naveen, 2026-11-24)

Executives are referred to **by role only**. Every $ figure in the deck is labelled *illustrative* until the business case
(Phase 2, Checkpoint 2b) replaces it with sourced numbers. Prototype metrics are always labelled "on synthetic data".

| Role | Value lens | KPIs they care about | Where the build evidences it |
|---|---|---|---|
| **VP of Revenue Cycle** (domain owner) | Revenue leakage | Illustrative medical-necessity denial write-off exposure; appeal eligibility; overturn rate; missed deadlines; recoverable revenue | Gold worklist (`expected_reimbursement`, `deadline_status`, `worklist_tag`), `appeals_metrics` (appealable $, $ at deadline risk, $ lost to deadline, warranted rate), Genie Agent |
| **CDAIO** (Chief Data & AI Officer; technical stakeholder) | Enterprise AI value | Cost per appeal; AI accuracy; governance; reusable agentic architecture; enterprise scalability | `system.billing` cost per appeal, `eval_summary` (accuracy, unsafe_rate, quote_verified_rate), UC tags/grants/lineage, job-as-code DAG, chatbot (LangGraph + UC tools) |
| **CFO** (executive sponsor) | Financial value | **$12.8M — reference placeholder only** (illustrative annual incremental revenue recovery); net financial benefit; operating margin improvement; ROI; payback period | Financial model Sheet (Phase 2), scenario ranges; never presented as a health-system result |
| **Director of Denial Management** (operational owner) | Operational efficiency | Appeal preparation time; appeals processed per employee; backlog reduction; administrative cost per appeal | NEW/AT_RISK worklist ordering, deterministic data sheet (validation time), reviewer actions in Lakebase (`review_actions`, `review_state`), Genie questions on backlog |

## Rules for artifacts
- `$12.8M` appears only as "reference placeholder, to be validated" — never as a computed or the health system-reported figure.
- Measured numbers (cost per appeal, accuracy, counts) come from the build's evidence files; label them "prototype, synthetic data".
- Projected numbers (recovery, ROI, payback, FTE hours) come from the Phase 2 model with conservative / base / upside scenarios.
