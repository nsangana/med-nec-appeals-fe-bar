#!/usr/bin/env python3
"""Build genie/genie_space.json (parsed serialized_space object) for "FE Bar – Medical Necessity Appeals".

Run:  python3 genie/build_space.py        (writes genie/genie_space.json, deterministic ids)
Ids are derived from a fixed seed so re-runs produce the same JSON (32-char lowercase hex, unique across lists).
"""
import hashlib, json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
CAT = "appeals_hackathon_catalog.fe_bar_appeals"


def hid(seed: str) -> str:
    return hashlib.md5(seed.encode()).hexdigest()


# Role-mapped sample questions (docs/STAKEHOLDERS.md). Each one is also a benchmark in genie/benchmarks.json.
SAMPLE_QUESTIONS = [
    # VP of Revenue Cycle
    "How much appealable revenue is at deadline risk this week by payer?",
    "How much expected reimbursement was lost to missed appeal deadlines by payer?",
    "What is the warranted rate by payer type?",
    # CDAIO
    "What is the cost per appeal?",
    "What is the AI accuracy and unsafe rate of the latest evaluation run?",
    "What share of appeals were routed to NEEDS REVIEW, and why?",
    # CFO (illustrative only)
    "What is the illustrative recoverable revenue by payer?",
    "How does expected reimbursement compare with total charges by denial code?",
    # Director of Denial Management
    "How many denials were logged as NEW (denied yesterday)?",
    "How many denials are in the backlog by worklist tag?",
    "What share of reviewed appeals were approved, meaning submitted?",
]

TEXT_INSTRUCTION = [
    "You are the analyst for Revenue Cycle leadership reviewing medical-necessity denial appeals. Answer in plain business language. Lead with the number, then the payer or driver, then a one-line caveat when the answer depends on an estimate or on AI output.\n",
    "DATA MODEL. Use the metric view appeals_metrics for every KPI and dollar question. It is at one row per denied encounter (gold_denial_worklist) and carries the generated appeal (appeals_output) through a LEFT join. Use the base tables gold_denial_worklist and appeals_output only for row-level or claim-level lookups, such as a named patient or a list of encounters.\n",
    "METRIC VIEW RULE. A metric view cannot be JOINed to another table directly. To combine appeals_metrics with another table, first wrap it in a WITH clause: WITH m AS (SELECT payer, `Revenue At Deadline Risk` FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL) SELECT m.*, ... FROM m JOIN other ON ... . Measures must be called with MEASURE(`name`) and are never SELECT *.\n",
    "DEFINITIONS. denial_code is a CARC code; CO50 means the service was not deemed medically necessary, which is the denial this workflow appeals. expected_reimbursement is the contracted or allowed dollar amount at stake: use it for every dollar-at-risk question. total_charges is billed charges, not revenue: use it only when the user asks for charges. Never add them together. Plain \"expected reimbursement\" or \"expected vs charges\" means the sum of expected_reimbursement over ALL worklist encounters, including PAST_DUE, which is the measure Expected Reimbursement (All Encounters). Use the measure Appealable Revenue only when the user says appealable or still open, and say which one you used.\n",
    "DEADLINE STATUS. deadline_status = PAST_DUE when the appeal window has closed; AT_RISK when 14 days or fewer remain (days_remaining <= 14); OK otherwise. days_remaining is counted from the current date. Phrases like 'at deadline risk' mean AT_RISK. 'This week' is NOT a date filter on the worklist: the worklist is a current snapshot, so say so instead of inventing a date range.\n",
    "APPEAL WINDOWS (modelled assumptions, not payer contract terms): COMMERCIAL 180 days, MEDICARE_ADVANTAGE 65 days, MEDICAID (AHCCCS) 60 days, all counted from the denial date. If asked about contract terms, say they were not reviewed in this build.\n",
    "RECOMMENDATION. recommendation is WARRANTED, NOT WARRANTED or NEEDS REVIEW and is AI output, not a final determination. NEEDS REVIEW means the AI could not decide and a human must decide; needs_review_reason explains why (a PARSE_FAILURE reason means the model output could not be read). NOT GENERATED in the metric view means no appeal exists yet. Warranted Rate and NEEDS REVIEW Rate use Appeals Generated as the denominator.\n",
    "REVIEW. review_status is the latest reviewer action (SUBMIT, EDIT, ROUTE_TO_REVIEW, or NOT REVIEWED). Approval Rate = share of reviewed encounters submitted (SUBMIT); its denominator is Reviewed Encounters. In this build review_state_uc holds SIMULATED reviewer actions (a demo seed, not real reviewers), and the sample is small. Always say that when you report an approval rate, and say how many encounters were reviewed. Use review_state_uc directly only for per-reviewer or timing questions, and never expose reviewer identities.\n",
    "CFO FIGURES. Illustrative Recoverable Revenue (Prototype) is a prototype figure computed on synthetic data: expected reimbursement of WARRANTED appeals whose window is still open. It is NOT a forecast, NOT a customer result and NOT a business case. Always label it illustrative and name the data as synthetic. Never state a recovery total, ROI or payback from this space.\n",
    "AI ACCURACY. eval_summary holds one row per evaluation run, with accuracy, unsafe_rate (WARRANTED predicted where the expected label is not WARRANTED), quote_verified_rate and per-class precision and recall. Use the latest run (highest run_ts). Say the labels are synthetic.\n",
    "COST. Cost Per Appeal (ESTIMATE) is a placeholder estimate, not a measured cost. Always label it as an estimate when you report it.\n",
    "PRIORITY. priority_rank 1 is the most urgent encounter (priority_score weights AT_RISK and near-deadline encounters, and is 0 for PAST_DUE). Use priority_rank for 'highest priority' questions.\n",
    "PATIENTS. Name a patient only when the user names one or asks for a claim status. Do not list patient names in aggregate answers.\n",
    "If a question needs a role or group you cannot see, say the data is not available to you rather than guessing.\n",
]

# Example SQL (question -> SQL). These are also the benchmark reference set; kept in benchmarks.json too.
EXAMPLE_SQL = [
    ("How much appealable revenue is at deadline risk by payer?",
     "SELECT payer, MEASURE(`Revenue At Deadline Risk`) AS at_risk_revenue FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY at_risk_revenue DESC"),
    ("Which payer has the most CO50 denials?",
     "SELECT payer, MEASURE(`Denials In Worklist`) AS co50_denials FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics WHERE denial_code = 'CO50' GROUP BY ALL ORDER BY co50_denials DESC LIMIT 1"),
    ("What is the warranted rate and NEEDS REVIEW rate by payer type?",
     "SELECT payer_type, MEASURE(`Warranted Rate`) AS warranted_rate, MEASURE(`NEEDS REVIEW Rate`) AS needs_review_rate FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics GROUP BY ALL ORDER BY ALL"),
    ("Why were appeals routed to NEEDS REVIEW?",
     "SELECT COALESCE(needs_review_reason, 'NO REASON RECORDED') AS needs_review_reason, COUNT(*) AS appeals FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_output WHERE recommendation = 'NEEDS REVIEW' GROUP BY ALL ORDER BY appeals DESC"),
    ("What is the status of the claim for Elena Marquez?",
     "WITH w AS (SELECT FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR, patient_name, payer_name, denial_code, deadline_status, days_remaining, expected_reimbursement FROM appeals_hackathon_catalog.fe_bar_appeals.gold_denial_worklist WHERE patient_name = 'Elena Marquez') SELECT w.patient_name, w.payer_name, w.denial_code, w.deadline_status, w.days_remaining, w.expected_reimbursement, COALESCE(a.recommendation, 'NOT GENERATED') AS recommendation FROM w LEFT JOIN appeals_hackathon_catalog.fe_bar_appeals.appeals_output a ON w.FACILITY_ID = a.FACILITY_ID AND w.PATIENT_CONTROL_NUMBER = a.PATIENT_CONTROL_NUMBER AND w.ENCOUNTER_NBR = a.ENCOUNTER_NBR"),
    ("What is the cost per appeal?",
     "SELECT MEASURE(`Cost Per Appeal (ESTIMATE)`) AS cost_per_appeal_estimate_usd FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_metrics"),
]


def build() -> dict:
    sq = [{"id": hid(f"sq{i}"), "question": [q]} for i, q in enumerate(SAMPLE_QUESTIONS)]
    ex = [{"id": hid(f"ex{i}"), "question": [q], "sql": [s]} for i, (q, s) in enumerate(EXAMPLE_SQL)]
    ti = [{"id": hid("ti0"), "content": TEXT_INSTRUCTION}]
    tables = sorted(
        [
            f"{CAT}.appeals_metrics",
            f"{CAT}.appeals_output",
            f"{CAT}.gold_denial_worklist",
            f"{CAT}.eval_summary",
            f"{CAT}.review_state_uc",
        ]
    )
    return {
        "version": 2,
        "config": {"sample_questions": sorted(sq, key=lambda x: x["id"])},
        "data_sources": {"tables": [{"identifier": t} for t in tables]},
        "instructions": {
            "example_question_sqls": sorted(ex, key=lambda x: x["id"]),
            "text_instructions": ti,
        },
    }


if __name__ == "__main__":
    out = HERE / "genie_space.json"
    out.write_text(json.dumps(build(), indent=2) + "\n")
    print(f"wrote {out}")
