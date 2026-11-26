# Checkpoint 2b — MEASURED platform cost per appeal (prototype on synthetic data)

Source: `system.billing.usage` × `system.billing.list_prices` (**list price, no discounts**) for workspace
fevm-appeals-hackathon (id 7474656043998914), usage_date 2026-11-24, queried 2026-11-25 after billing closed
(latest usage_end_time 2026-11-25T00:00Z). Supersedes COST_2A.md. All figures are a prototype at demo scale, **not the health system results**.

## A. Variable cost — one end-to-end job run (`fe-bar-appeals-job` run 1038287240919742, 60 appeals generated)
| Component | How measured | DBU | $/DBU | $ / run |
|---|---|---|---|---|
| Appeal generation LLM (`ai_query` → databricks-claude-sonnet-4-6) | billing window 10:40 (batch 3 = this run) | 53.90 | 0.07 | 3.773 |
| Grounding digests (`ai_summarize`, re-run over all 460 grounded encounters) | windows 10:30–10:40 | 4.79 | 0.07 | 0.335 |
| SQL warehouse time for grounding + data sheet + generation (~6.1 min of a 24 DBU/h serverless warehouse) | allocated by task duration (warehouse is shared; billing is uptime-based) | ~2.44 | 0.70 | ~1.71 |
| Serverless jobs compute (generator, bootstrap, render PDFs, Lakebase sync, eval notebooks) | `usage_metadata.job_run_id` = this run | 0.8246 | 0.45 | 0.371 |
| SDP pipeline update (`fe-bar-appeals-sdp`) | day total 1.59 DBU over ~4 updates → per-update share | ~0.40 | 0.45 | ~0.18 |
| Lakebase synced-table refresh pipeline | day total 0.417 DBU over ~4 refreshes | ~0.10 | 0.45 | ~0.05 |
| **Total per run** | | | | **≈ $6.42** |
| **Variable cost per appeal** (÷ 60) | | | | **≈ $0.107** |
| — of which LLM generation (measured across all 3 batches: 177.86 DBU ÷ 180 appeals = 0.988 DBU) | | | | **$0.069** |

## B. Always-on platform (fixed), measured run-rates
| Resource | Measured | $/day |
|---|---|---|
| App `fe-bar-appeals-app` | 7.024 DBU over 15 h × $0.95 | ~10.70 |
| Chat endpoint `fe-bar-appeals-chat` (Small CPU, scale-to-zero OFF) | 106.93 DBU over 13.3 h × $0.07 | ~13.50 |
| Lakebase `fe-bar-appeals-lakebase` (0.5 CU, autosuspend) | 0.406 DBU × $0.26 + storage | ~0.15 |
| Vector Search endpoint (shared `appeals-vs-endpoint`, also used by the earlier build) | ~4 DBU/h × $0.07 | ~6.70 (shared) |
| **Fixed, own resources** | | **≈ $24.4/day ≈ $8.9K/yr** |
| Fixed incl. shared VS | | ≈ $31.1/day ≈ $11.3K/yr |

## C. Cost per appeal (deck uses these)
| View | $ / appeal |
|---|---|
| **Variable (per appeal generated)** | **$0.11** |
| Fully loaded at prototype scale (60 appeals/day, own resources) | **$0.51** |
| Fully loaded at 60/day incl. shared VS | $0.62 |
| Fully loaded at 60/day with chat scale-to-zero ON | ~$0.29 |

## Caveats
- List prices; the health system's contracted rates would differ. Warehouse and SDP shares are allocations, labelled "~".
- Grounding re-summarizes all grounded encounters every run (fixed ~$0.34/run today); making it incremental lowers variable cost further.
- Production sizing (more appeals/day, more reviewers) changes the fixed-cost denominator; that's an assumption to validate.
