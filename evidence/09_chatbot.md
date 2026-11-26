# Evidence 09 — Chatbot endpoint `fe-bar-appeals-chat` (LangGraph ResponsesAgent + UC function tools + VS retriever)

> **SUPERSEDED for dates (2026-11-25).** This invocation was made on the 2026-11-24 data layer. The hero's appeal deadline is now **Dec 4, 2026** (9 days remaining at the 2026-11-25 run), not Dec 3. The endpoint itself was not re-invoked in the clean rerun; the quoted text below is the 2026-11-24 output. Re-invoke before quoting the chat answer.

- Endpoint state: READY (config version 3, 2026-11-24). UC model `appeals_hackathon_catalog.fe_bar_appeals.appeals_chat_agent` v1.
- App binding: resource `serving-endpoint` (app SP CAN_QUERY); app calls it on behalf of the signed-in user.
- Deploy history: v1 failed (credential generation), v2 failed (model load: System Service Principal lacked EXECUTE on get_appeal because the job re-created the UC functions mid-deploy), v3 READY after making function creation idempotent (CREATE FUNCTION IF NOT EXISTS).

## Sample invocation (real, via /serving-endpoints/fe-bar-appeals-chat/invocations, synthetic hero claim)

**Q:** For FACILITY_ID=101, PATIENT_CONTROL_NUMBER=770000001, ENCOUNTER_NBR=50000001: what is the recommendation and the top 3 pieces of clinical evidence supporting it? Be brief.

## Recommendation: ✅ WARRANTED

**Patient:** Elena Marquez | **Claim:** CO50 denial (Not Medically Necessary) | **Procedure:** CPT 27447-RT (Right Total Knee Arthroplasty) | **Payer:** BCBS of Arizona | **⚠️ Deadline: Dec 3, 2026 — only 9 days remaining (AT RISK)**

---

### Top 3 Pieces of Clinical Evidence

1. **Kellgren-Lawrence Grade 4 Imaging (Feb 3, 2026)**
Weight-bearing X-ray confirmed bone-on-bone medial compartment, osteophytes, and subchondral sclerosis — objective end-stage structural disease directly supporting surgical necessity.

2. **Documented Failure of Three Conservative Modalities (Sep 2025 – Mar 2026)**
- NSAIDs (Naproxen + adjuncts, ~7 months) → only partial, temporary relief
- Supervised PT (12 visits, Nov 2025–Jan 2026) → goals not met, pain 6/10 persisting at discharge
- Corticosteroid injection (Feb 8, 2026) → only 3 weeks of relief before return to baseline

3. **Severe Functional Limitation with Explicit Surgical Rationale (Apr 14, 2026 Ortho Consult)**
KOOS score 31/100 (pain subscale 28), unable to walk more than one block, antalgic gait — with the orthopedic surgeon explicitly documenting surgical rationale for 27447-RT after exhausting conservative care.

---

> **⚠️ Action needed:** The appeal deadline is **December 3, 2026 — 9 days away**. Prioritize submission immediately.


## Re-run after the clean rerun (2026-11-25, same question, endpoint READY, regenerated appeals_output)

## Recommendation: ✅ WARRANTED

**Patient:** Elena Marquez | **Denial:** CO50 (Not Medically Necessary) | **Procedure:** CPT 27447-RT (Right Total Knee Arthroplasty) | **Payer:** BCBS of Arizona

**⚠️ Deadline Alert:** Appeal due **2026-12-04 — only 9 days remaining (AT RISK).**

---

### Top 3 Pieces of Clinical Evidence

1. **End-stage imaging findings** *(Source: [2026-02-04 IMAGING_XRAY])*
Weight-bearing X-rays confirmed **Kellgren-Lawrence grade 4 osteoarthritis** with bone-on-bone medial compartment narrowing, osteophytes, and subchondral sclerosis — the most severe radiographic grade possible.

2. **Documented failure of all conservative therapies** *(Sources: [2025-09-17 RX_HISTORY], [2026-01-25 PT_DISCHARGE], [2026-02-09 INJECTION_NOTE])*
Three modalities all failed with specific dates and outcomes:
   - NSAIDs (Naproxen + adjuncts): only partial, temporary relief (Oct–Dec 2025)
   - 12 supervised PT visits: goals not met, pain 6/10 at discharge (Nov 2025–Jan 2026)
   - Corticosteroid injection: only ~3 weeks of relief before return to baseline (Feb 2026)

3. **Severe, quantified functional impairment + complete surgical rationale** *(Source: [2026-04-15 ORTHO_CONSULT])*
KOOS score of **31/100** (pain subscale 28), unable to walk more than one block. The treating orthopedic surgeon explicitly documented surgical rationale citing all failed conservative treatments and grade 4 imaging — satisfying BCBS AZ's requirement for "complete medical rationale."

---

> **Bottom line:** All BCBS Arizona medical necessity documentation requirements are met with no gaps identified. The appeal is strongly supported.


## v2 (anonymized system prompt) — 2026-11-25
UC model version 2 deployed to `fe-bar-appeals-chat` via one-time run 915704767665281 (TERMINATED SUCCESS); traffic 100% v2. Identity probe + hero question:

Here's your one-liner:

> **Recommendation: WARRANTED** | **Appeal Deadline: December 4, 2026** (8 days remaining — status: ⚠️ AT RISK)

**Act quickly** — with only 8 days left, this appeal should be submitted as soon as possible. Let me know if you'd like to review the full appeal letter, AI reasoning worksheet, or any specific aspect of this claim!
