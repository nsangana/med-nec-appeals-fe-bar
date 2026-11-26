# Checkpoint 2a — platform cost per appeal (ESTIMATE, prototype on synthetic data)

Source: `system.billing.usage` × `system.billing.list_prices` (list price, no discounts) for workspace fevm-appeals-hackathon,
queried 2026-11-24 ~12:40 UTC. Billing was complete only through ~10:00 UTC for warehouse-linked usage, so this is a
partial measurement + estimate. **Checkpoint 2b** replaces it once all three generation batches (09:49, 10:00, 10:41 UTC)
and the end-to-end job run are billed.

## Measured so far
| Component | Evidence | DBU | $/DBU (list) | $ |
|---|---|---|---|---|
| Appeal generation, batch 1 (60 encounters, `ai_query` → `databricks-claude-sonnet-4-6`) | billing window 09:50–10:00, warehouse 559faf81 | 61.12 | 0.07 | 4.28 |
| → **LLM generation per appeal** | 61.12 / 60 | 1.02 | 0.07 | **0.071** |
| Grounding clinical digests (`ai_summarize`, 460 encounters; several rebuilds during development) | windows 09:30–09:50 | 28.86 | 0.07 | 2.02 (≤ $0.0044 per encounter per pass if a single pass) |
| Lakebase (0.5 CU, autosuspend 300 s) | LAKEBASE product, today | 0.06 | 0.26 | 0.02 |

## Always-on components (allocated, not metered per appeal) — observed run-rates of equivalent resources today
| Component | Observed rate | ≈ $/day (list) |
|---|---|---|
| Databricks App compute (same size as `fe-bar-appeals-app`) | 0.5 DBU/h × $0.95 | ~11.40 |
| Chat agent endpoint (Small CPU, **scale-to-zero OFF**, same config as `fe-bar-appeals-chat`) | ~12 DBU/h × $0.07 | ~20.10 |
| Vector Search endpoint (shared `appeals-vs-endpoint`) | ~4 DBU/h × $0.07 | ~6.70 (shared) |

## Estimate (2a)
| View | $/appeal | Notes |
|---|---|---|
| **Variable (per appeal generated)** | **≈ $0.08 – $0.11** | LLM $0.071 + grounding/SQL warehouse/serverless job share (est. $0.01–0.04 at 60 appeals/run) |
| Fully loaded at prototype scale (60 appeals/day) | ≈ $0.70 – $0.75 | adds ~$38/day always-on (app + chat endpoint + shared VS) ÷ 60 |
| Fully loaded at 60/day with chat scale-to-zero ON | ≈ $0.36 – $0.40 | removes most of the ~$20/day idle endpoint cost |

## Findings to act on (cost hygiene)
1. `fe-bar-appeals-chat` has scale-to-zero OFF → ~$20/day idle. Recommend ON for the demo (cold start ~minutes).
2. Grounding rebuilds `ai_summarize` for all non-past-due encounters on every run; make it incremental on `input_hash`
   like generation (P1), so per-run cost scales with new denials only.
3. Per-appeal LLM cost is driven by output tokens (letter + worksheet); the cap of 60/run bounds daily LLM spend at ≈ $4.30.
