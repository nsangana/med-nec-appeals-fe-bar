# Evidence 09 — Chatbot endpoint `fe-bar-appeals-chat` (LangGraph ResponsesAgent + UC function tools + VS retriever)

REFRESHED 2026-11-26 (UTC). The hero invocation below was re-run on 2026-11-26 against the current endpoint.

History: earlier runs are in git history.

- Endpoint state (re-read 2026-11-26): `ready` READY, `config_update` NOT_UPDATING, config version 5.
- Served entity: UC model `appeals_hackathon_catalog.fe_bar_appeals.appeals_chat_agent` version **2** (anonymized system prompt), traffic **100%**. The `feedback` entity is at 0%.
- App binding: resource `serving-endpoint` (app SP CAN_QUERY). The app calls it on behalf of the signed-in user.
- Traces: chat tracing is on and 0 traces are recorded for this endpoint (see evidence/14).

## Hero invocation (real, 2026-11-26, `/serving-endpoints/fe-bar-appeals-chat/invocations`, synthetic hero claim)

**Q:** For FACILITY_ID=101, PATIENT_CONTROL_NUMBER=770000001, ENCOUNTER_NBR=50000001: what is the recommendation and the top 3 pieces of clinical evidence supporting it? Be brief.

**A (verbatim model output):**

## Recommendation: ✅ WARRANTED

The appeal for CPT **27447-RT** (Right Total Knee Arthroplasty), denied under **CO50** by BCBS of Arizona, is fully supported. Here are the **top 3 pieces of clinical evidence**:

---

### 1. 🦴 Objective Imaging — End-Stage Disease
Weight-bearing X-rays on **2026-02-04** showed **Kellgren-Lawrence grade 4 osteoarthritis with bone-on-bone medial compartment**, osteophytes, and subchondral sclerosis — the most severe radiographic classification of knee OA. *(Source: 2026-02-04 IMAGING_XRAY)*

---

### 2. 💊 Documented Failure of Conservative Treatment (7+ months)
A stepwise course of conservative care all failed:
- **NSAIDs** (Naproxen 500mg BID, Oct–Dec 2025): only partial, temporary relief
- **12 supervised PT visits** (Nov 2025–Jan 2026): goals not met, pain 6/10 at discharge, explicitly documented as failure
- **Corticosteroid injection** (Feb 9, 2026): only ~3 weeks of relief before returning to baseline
*(Sources: 2025-09-17 RX_HISTORY; 2026-01-25 PT_DISCHARGE; 2026-02-09 INJECTION_NOTE)*

---

### 3. 🚶 Severe Functional Limitation + Documented Surgical Rationale
At the **2026-04-15 orthopedic consult**, the patient scored **KOOS 31/100** (pain subscale 28) and could **not walk more than one block without stopping**, with antalgic gait. The surgeon documented complete rationale for surgery citing all failed modalities. *(Source: 2026-04-15 ORTHO_CONSULT)*

---

> ⚠️ **Deadline Alert:** The appeal deadline is **2026-12-04** — only **8 days remaining** (status: AT RISK). Submit promptly.

The three dated facts and the deadline are in the answer. The hero's 9 days remaining was the 2026-11-25 run; the answer reads 8 on 2026-11-26.

## Identity probe (v2, 2026-11-25)

Recorded on 2026-11-25, after the v2 deploy (anonymized system prompt). The reply carries no customer name.

> **Recommendation: WARRANTED** | **Appeal Deadline: December 4, 2026** (8 days remaining — status: ⚠️ AT RISK)
>
> **Act quickly** — with only 8 days left, this appeal should be submitted as soon as possible. Let me know if you'd like to review the full appeal letter, AI reasoning worksheet, or any specific aspect of this claim!
