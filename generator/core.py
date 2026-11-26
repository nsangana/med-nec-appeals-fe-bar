"""Seeded, reproducible synthetic generator for the FE Bar medical-necessity appeals caseload.

Pure Python standard library. Same (seed, n_encounters, as_of_date) -> byte-identical output.

Output (`Batch`):
  claims  - claim-line records (mednecessity_ai_agent columns + DENIAL_DATE, PAYER_TYPE,
            APPEAL_LIMIT_DAYS, EXPECTED_REIMBURSEMENT, SOURCE_BATCH)
  notes   - clinical-note records (composite key + PATIENT_NAME + event_id, event_tag, note_date,
            author_role, plain_text)
  labels  - eval ground truth (eval_case_labels). Never written to landing or the pipeline.
  manifest- internal: per-encounter plan and the deliberately injected defect rows.

Label design (what the notes embody; notes never name the label):
  WARRANTED        criteria met: dated conservative treatment, imaging / functional limits, provider rationale
  NOT WARRANTED    criteria clearly not met: no conservative care, mild imaging, lower level justified
  NEEDS REVIEW     evidence genuinely insufficient or contradictory: referenced but missing records,
                   conflicting dates, outside report "reviewed" but not in chart
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional

from . import catalog as C

GENERATOR_VERSION = "1.0.0"
DEFAULT_SEED = 20261124
DEFAULT_N_ENCOUNTERS = 500
LABELS = ("WARRANTED", "NOT WARRANTED", "NEEDS REVIEW")
LABEL_MIX = {"WARRANTED": 0.45, "NOT WARRANTED": 0.35, "NEEDS REVIEW": 0.20}
BUCKET_MIX = {"PAST_DUE": 0.08, "AT_RISK": 0.15, "OK": 0.77}  # NEW (denied yesterday) is carved out of OK
DEFECT_KINDS = ("bad_carc", "dos_after_denial", "null_key", "negative_expected")
HERO_KEYS = {"FACILITY_ID": 101, "PATIENT_CONTROL_NUMBER": 770000001, "ENCOUNTER_NBR": 50000001}
HERO_DOS_BEFORE_DENIAL = 23
HERO_DAYS_REMAINING = 9

CLAIM_FIELDS = (
    "PATIENT_NAME", "PATIENT_BIRTHDATE", "PATIENT_SEX", "PATIENT_CONTROL_NUMBER", "FACILITY_ID",
    "MEDICAL_RECORD_NUMBER", "STATEMENT_COVERS_PERIOD", "TOTAL_CHARGES", "SITEID", "CLAIM_NUMBER",
    "PAYER_NAME", "PAYER_ADDRESS_STREET", "PAYER_CSZ", "TYPE_OF_BILL", "HEALTH_PLAN_ID",
    "FEDERAL_TAX_ID", "PROVIDER_NAME", "BILL_DATE", "DENIAL_ID", "DENIAL_CODE", "PATIENTIDENTITYCODE",
    "CLAIMPOLICYNUMBER", "DATE_PAID", "HCPCS_CODE", "MOD1", "POS", "REV_CODE", "DOS",
    "LINE_ITEM_CONTROL_NUMBER", "ADMIT_DIAG", "DISCH_DIAG1", "DISCH_DIAG2", "DISCH_DIAG3",
    "DISCH_DIAG4", "DISCH_DIAG5", "DISCH_DIAG6", "ENCOUNTER_NBR",
    # new fields (FE Bar SPEC)
    "DENIAL_DATE", "PAYER_TYPE", "APPEAL_LIMIT_DAYS", "EXPECTED_REIMBURSEMENT", "SOURCE_BATCH",
)
NOTE_FIELDS = (
    "FACILITY_ID", "PATIENT_CONTROL_NUMBER", "ENCOUNTER_NBR", "PATIENT_NAME",
    "event_id", "event_tag", "note_date", "author_role", "plain_text",
)


@dataclass
class Batch:
    seed: int
    n_encounters: int
    as_of_date: date
    claims: List[dict]
    notes: List[dict]
    labels: List[dict]
    manifest: dict

    @property
    def source_batch(self) -> str:
        return f"batch_{self.as_of_date.isoformat()}_seed{self.seed}_n{self.n_encounters}"


# --------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------
def _largest_remainder(n: int, mix: Dict[str, float]) -> Dict[str, int]:
    raw = {k: n * v for k, v in mix.items()}
    counts = {k: int(v) for k, v in raw.items()}
    short = n - sum(counts.values())
    keys = list(mix)
    for k in sorted(keys, key=lambda k: (-(raw[k] - counts[k]), keys.index(k)))[:short]:
        counts[k] += 1
    return counts


def _plan_labels_and_buckets(seed: int, n: int):
    """Exact quotas (not random draws) so the label mix and deadline mix hold for every seed.
    Encounter 0 is the hero: WARRANTED and AT_RISK, so it is removed from the quotas."""
    master = random.Random(f"fe-bar:{seed}:master")
    lab = _largest_remainder(n, LABEL_MIX)
    buc = _largest_remainder(n, BUCKET_MIX)
    lab["WARRANTED"] -= 1
    buc["AT_RISK"] -= 1
    label_list = [k for k in LABELS for _ in range(lab[k])]
    bucket_list = [k for k in BUCKET_MIX for _ in range(buc[k])]
    master.shuffle(label_list)
    master.shuffle(bucket_list)
    # ADDENDUM 1: ~4% of encounters (20 of 500) are "denied yesterday" (denial_date = as_of - 1 day).
    # They are carved out of the OK bucket so the PAST_DUE / AT_RISK quotas are unchanged.
    ok_positions = [i for i, b in enumerate(bucket_list) if b == "OK"]
    n_new = min(len(ok_positions), max(1, round(0.04 * n)))
    for i in master.sample(ok_positions, n_new):
        bucket_list[i] = "NEW"
    return label_list, bucket_list, master


def _pick(rng: random.Random, items, weights):
    return rng.choices(list(items), weights=list(weights), k=1)[0]


def _money(rng: random.Random, lo: float, hi: float):
    expected = round(rng.uniform(lo, hi), 2)
    charges = round(expected / rng.uniform(0.34, 0.50), 2)  # expected is well below charges
    return charges, expected


# --------------------------------------------------------------------------------------------
# clinical-note templates. Each returns (variant_name, [(tag, role, days_before_dos, text), ...])
# All dates are expressed as days before the date of service so the chart is internally dated.
# --------------------------------------------------------------------------------------------
class _NoteCtx:
    """Chart-writing context. `side` / `mod` carry the laterality of a lateralized procedure (TKA): the note text
    and the claim modifier (MOD1) must name the same knee. Non-lateralized templates ignore them."""

    def __init__(self, dos: date, rng: random.Random, side: str = "right", mod: str = "RT"):
        self.dos = dos
        self.rng = rng
        self.side = side          # "right" | "left"
        self.mod = mod            # "RT" | "LT"

    @property
    def Side(self) -> str:
        return self.side.capitalize()

    def d(self, k: int) -> str:
        return (self.dos - timedelta(days=k)).isoformat()


def _tka_w(c: _NoteCtx):
    # Hero-compatible: with side="right" / mod="RT" the text is identical to the original fixed hero chart.
    return "full_conservative_chain", [
        ("RX_HISTORY", "PRIMARY_CARE", 240,
         f"{c.Side} knee osteoarthritis with pain for more than 7 months. Naproxen 500 mg BID started {c.d(200)}; "
         f"continued through {c.d(150)} with partial, temporary relief. Acetaminophen and topical diclofenac added."),
        ("PT_EVAL", "PHYSICAL_THERAPIST", 170,
         f"Physical therapy initial evaluation, {c.side} knee. Pain 7/10 with stair climbing and prolonged standing. "
         "Antalgic gait. Plan: 2 visits per week for 12 weeks."),
        ("PT_DISCHARGE", "PHYSICAL_THERAPIST", 110,
         f"Discharged after 12 supervised visits ({c.d(170)} to {c.d(112)}). Goals not met. Pain 6/10 with ADLs. "
         "Range of motion plateaued after visit 12. Documented failure of supervised conservative therapy."),
        ("INJECTION_NOTE", "PAIN_MANAGEMENT", 95,
         f"{c.Side} knee intra-articular corticosteroid injection performed {c.d(95)}. Relief reported for about "
         f"3 weeks; pain returned to baseline by {c.d(74)}."),
        ("IMAGING_XRAY", "RADIOLOGIST", 100,
         f"Weight-bearing AP and lateral {c.side} knee ({c.d(100)}): Kellgren-Lawrence grade 4 osteoarthritis. "
         "Bone-on-bone medial compartment. Osteophytes and subchondral sclerosis."),
        ("ORTHO_CONSULT", "ORTHOPEDIC_SURGEON", 30,
         f"Consult for {c.side} knee osteoarthritis. Pain over 7 months. Cannot walk more than one block without stopping. "
         "KOOS 31/100 (pain subscale 28). Failed NSAIDs, 12 PT visits, and corticosteroid injection with 3-week relief. "
         f"Kellgren-Lawrence grade 4 on imaging. Recommend {c.side} total knee arthroplasty (27447-{c.mod}). "
         "Surgical rationale documented."),
    ]


def _tka_n(c: _NoteCtx):
    return "no_conservative_care_mild_imaging", [
        ("PRIMARY_CARE", "PRIMARY_CARE", 60,
         f"Intermittent {c.side} knee discomfort after yard work. Pain 2/10 at rest. Walks 3 miles most days and plays "
         "golf weekly. No knee treatment documented."),
        ("IMAGING_XRAY", "RADIOLOGIST", 45,
         f"Weight-bearing {c.side} knee: mild joint space narrowing. No significant osteophytes. Alignment normal. "
         "Kellgren-Lawrence grade 1."),
        ("ORTHO_CONSULT", "ORTHOPEDIC_SURGEON", 30,
         "Patient requests a consult about surgery to return to high-impact dance classes. Exam: mild crepitus, full "
         "range of motion, no effusion. Imaging shows mild change. Recommended activity modification and home exercise. "
         "Surgery not indicated at this time. No medication, physical therapy, or injection trial documented."),
    ]


def _tka_nr(c: _NoteCtx):
    return "outside_imaging_and_pt_referenced_not_in_chart", [
        ("RX_HISTORY", "PRIMARY_CARE", 150,
         "Patient states she has taken anti-inflammatories 'for a long time.' No dates, prescriptions, or fill history in chart."),
        ("PT_EVAL", "PHYSICAL_THERAPIST", 200,
         "Patient reports completing physical therapy last year at an outside clinic. Records requested; none received as of this note."),
        ("INJECTION_NOTE", "PAIN_MANAGEMENT", 10,
         f"Corticosteroid injection {c.side} knee performed today."),
        ("OUTSIDE_IMAGING_REF", "ORTHOPEDIC_SURGEON", 30,
         f"Outside {c.side} knee radiograph from 2025 reviewed; described as severe degenerative change. Formal report not in chart."),
        ("ORTHO_CONSULT", "ORTHOPEDIC_SURGEON", 30,
         f"{c.Side} knee osteoarthritis, pain 8/10, unable to walk more than one block. Recommend total knee arthroplasty. "
         "Per patient, injection given about two months ago and PT completed last year. Conservative care summary as reported."),
    ]


def _lumbar_fusion_w(c: _NoteCtx):
    gaba = c.rng.choice([280, 275, 290])
    return "fusion_full_chain_with_instability", [
        ("PRIMARY_CARE", "PRIMARY_CARE", 300,
         f"Low back pain radiating to left leg for 8 months. Gabapentin started {c.d(gaba)}; no durable relief."),
        ("PT_DISCHARGE", "PHYSICAL_THERAPIST", 190,
         f"Discharged after 8 supervised visits ({c.d(230)} to {c.d(195)}). Pain 7/10 standing; no functional improvement. "
         "Failed supervised therapy."),
        ("INJECTION_NOTE", "PAIN_MANAGEMENT", 170,
         f"Left L4-5 transforaminal epidural steroid injection {c.d(170)}. Relief 10 days, then recurrence."),
        ("INJECTION_NOTE", "PAIN_MANAGEMENT", 120,
         f"Second left-sided epidural steroid injection {c.d(120)}. Relief under 2 weeks."),
        ("IMAGING_MRI", "RADIOLOGIST", 160,
         "MRI lumbar spine: grade 1 L4-5 spondylolisthesis with severe central and lateral recess stenosis and left L5 "
         "nerve root compression."),
        ("IMAGING_XRAY", "RADIOLOGIST", 150,
         "Flexion-extension lumbar radiographs: 4 mm translational motion at L4-5, consistent with instability."),
        ("ORTHO_CONSULT", "ORTHOPEDIC_SURGEON", 40,
         f"Left EHL weakness 4/5 and decreased L5 sensation. Smoking cessation program enrolled {c.d(60)}; cotinine negative. "
         "Recommend L4-L5 posterolateral fusion (22612) with posterior instrumentation (22840). Surgical rationale documented."),
    ]


def _lumbar_fusion_n(c: _NoteCtx):
    return "mild_bulge_no_compression_no_conservative_care", [
        ("PRIMARY_CARE", "PRIMARY_CARE", 60,
         "Low back pain, mild, for 2 weeks. Pain 3/10, controlled with OTC acetaminophen. Neurologic exam normal, "
         "strength 5/5, reflexes symmetric. No radicular symptoms."),
        ("IMAGING_MRI", "RADIOLOGIST", 50,
         "MRI lumbar spine: mild disc bulge at L4-5 without neural compression. No spondylolisthesis. Degenerative change age-appropriate."),
        ("ORTHO_CONSULT", "ORTHOPEDIC_SURGEON", 30,
         "Patient requests a second opinion about fusion. No instability on exam. Recommended home exercise and return in 3 months. "
         "Fusion not indicated at this time. No physical therapy or injection documented."),
    ]


def _lumbar_fusion_nr(c: _NoteCtx):
    return "outside_mri_not_in_chart_motor_exam_conflict", [
        ("PRIMARY_CARE", "PRIMARY_CARE", 120,
         "Low back pain radiating to left leg. Patient reports prior PT and two epidurals 'last year'; no records in chart."),
        ("ORTHO_CONSULT", "ORTHOPEDIC_SURGEON", 30,
         "Lumbar fusion recommended. Outside MRI from 2025 reviewed per surgeon; report not in chart. Motor exam: left EHL "
         "4/5 in the surgeon exam section; nursing intake the same date records 5/5 with no difference noted."),
    ]


def _lumbar_mri_w(c: _NoteCtx):
    return "eight_weeks_conservative_with_progressive_deficit", [
        ("PRIMARY_CARE", "PRIMARY_CARE", 120,
         f"Low back pain with left leg radiation. Meloxicam started {c.d(118)}; cyclobenzaprine added {c.d(118)}; partial relief only."),
        ("PT_PROGRESS", "PHYSICAL_THERAPIST", 70,
         f"Physical therapy 6 visits over 8 weeks ({c.d(110)} to {c.d(60)}) plus daily NSAID. No improvement. "
         f"New left L5 dorsiflexion weakness 4/5 and positive straight-leg raise on {c.d(12)}; progressive numbness of the dorsum of the foot."),
        ("PRIMARY_CARE", "PRIMARY_CARE", 10,
         "Progressive L5 radiculopathy despite 8 weeks of conservative care. MRI lumbar spine ordered to evaluate nerve root compression."),
    ]


def _lumbar_mri_n(c: _NoteCtx):
    return "two_weeks_no_red_flags_no_therapy", [
        ("PRIMARY_CARE", "PRIMARY_CARE", 14,
         "Low back pain for 2 weeks after lifting boxes. No leg symptoms. No red flags: no bowel or bladder change, no fever, "
         "no saddle anesthesia. Neurologic exam normal. Advised ice and activity as tolerated. Patient requests MRI for reassurance."),
    ]


def _lumbar_mri_nr(c: _NoteCtx):
    return "red_flag_unexamined_pt_undated", [
        ("PRIMARY_CARE", "PRIMARY_CARE", 20,
         "Low back pain radiating to leg. Patient notes new bowel urgency; rectal tone and saddle sensation not documented. "
         "Prior PT referenced by patient; no dates or records. MRI ordered."),
    ]


def _sleep_w(c: _NoteCtx):
    return "inadequate_home_test_comorbid_hf", [
        ("PRIMARY_CARE", "PRIMARY_CARE", 90,
         "Snoring, witnessed apneas per bed partner, daytime somnolence. Epworth 17. STOP-BANG 6. BMI 38. "
         "Chronic systolic heart failure, EF 35%."),
        ("SLEEP_STUDY", "SLEEP_MEDICINE", 55,
         f"Home sleep apnea test {c.d(55)}: technically inadequate (insufficient channels, under 4 hours recorded). Repeat study indicated."),
        ("SLEEP_CONSULT", "SLEEP_MEDICINE", 30,
         "Attended in-lab polysomnography recommended: home test non-diagnostic; comorbid heart failure with possible central component. "
         "CPAP titration to follow if obstructive sleep apnea is confirmed."),
    ]


def _sleep_n(c: _NoteCtx):
    return "normal_home_test_not_indicated", [
        ("PRIMARY_CARE", "PRIMARY_CARE", 60,
         "Occasional snoring. Epworth 5. No witnessed apneas reported. Sleeps 7 hours. Normal exam."),
        ("SLEEP_STUDY", "SLEEP_MEDICINE", 45,
         "Home sleep apnea test: AHI 3.1/hr, normal oxygen nadir. Results reviewed with patient; no further sleep testing indicated."),
        ("SLEEP_CONSULT", "SLEEP_MEDICINE", 30,
         "Patient requested an in-lab study for reassurance. Home test normal; study not clinically indicated at this time."),
    ]


def _sleep_nr(c: _NoteCtx):
    return "referred_home_test_missing_conflicting_epworth", [
        ("PRIMARY_CARE", "PRIMARY_CARE", 70,
         "Epworth 7 at intake. Epworth 16 at follow-up two weeks later; no explanation documented."),
        ("SLEEP_CONSULT", "SLEEP_MEDICINE", 40,
         "Attended polysomnography ordered. Home sleep apnea test referenced in the referral; result not in chart."),
    ]


def _bariatric_w(c: _NoteCtx):
    return "supervised_program_comorbidities_psych_cleared", [
        ("PRIMARY_CARE", "PRIMARY_CARE", 400,
         "Class III obesity, BMI 47 (weight 298 lb). Type 2 diabetes, A1c 8.1%. Obstructive sleep apnea on CPAP. Hypertension on two agents."),
        ("NUTRITION", "NUTRITIONIST", 330,
         f"Supervised medically directed weight program: 6 visits {c.d(330)} to {c.d(90)}. Weight regain of 9 lb after initial loss."),
        ("PSYCH_EVAL", "PSYCHOLOGIST", 60,
         f"Psychological evaluation completed {c.d(60)}: cleared for bariatric surgery; no active substance use."),
        ("BARIATRIC_CONSULT", "BARIATRIC_SURGEON", 30,
         "Candidate for sleeve gastrectomy (43775). Comorbidities and failed nonsurgical weight management documented. Surgery indicated."),
    ]


def _bariatric_n(c: _NoteCtx):
    return "bmi_36_no_comorbidity_no_program", [
        ("PRIMARY_CARE", "PRIMARY_CARE", 60,
         "BMI 36. Patient asks about surgery. No diabetes (A1c 5.4%); blood pressure controlled without medication. No sleep apnea."),
        ("BARIATRIC_CONSULT", "BARIATRIC_SURGEON", 30,
         "Discussed options. Patient has not completed a supervised weight management program. Recommended diet and exercise plan; "
         "surgery not indicated at BMI 36 without comorbidity."),
    ]


def _bariatric_nr(c: _NoteCtx):
    return "bmi_conflict_psych_clearance_missing", [
        ("INTAKE", "UR_NURSE", 45, "Intake weight 268 lb, BMI 41."),
        ("ANESTHESIA_PRE", "ANESTHESIA", 20, "Pre-anesthesia visit: BMI 36, weight 245 lb."),
        ("BARIATRIC_CONSULT", "BARIATRIC_SURGEON", 30,
         "Recommend sleeve gastrectomy. Psychological evaluation completed per patient; clearance letter not in chart. "
         "Supervised program documented for 6 months."),
    ]


def _scs_w(c: _NoteCtx):
    # WARRANTED label design: (1) failed conservative care with dates, (2) dated lumbar MRI establishing the
    # radicular source, (3) a named device that is FDA premarket-approved (PMA) for an indication that covers this
    # patient, (4) the labeled-use statement. The device/indication wording is synthetic chart text; verify the
    # PMA number and labeling against the FDA PMA database before quoting it outside this prototype.
    return "fda_labeled_use_guideline_supported", [
        ("PAIN_MGMT", "PAIN_MANAGEMENT", 120,
         "Chronic radicular pain refractory to 9 months of physical therapy, medication, and two epidural steroid injections. Pain 8/10."),
        ("IMAGING_MRI", "RADIOLOGIST", 150,
         f"MRI lumbar spine ({c.d(150)}): L5-S1 and L4-5 degenerative disc disease with left L5 nerve root compression "
         "and no progressive spondylolisthesis. Findings correlate with the documented radicular leg pain."),
        ("PAIN_MGMT", "PAIN_MANAGEMENT", 40,
         "Spinal cord stimulator trial: percutaneous electrode array placement (63650) for chronic radicular pain of the "
         "lower extremity. Device: Medtronic Intellis spinal cord stimulator system, FDA premarket approval (PMA) for chronic "
         "intractable pain of the trunk and/or limbs. This patient's chronic radicular pain falls within that labeled indication "
         "and the patient meets the labeled criteria. Randomized trial evidence and a specialty society guideline recommendation "
         "are cited in the plan. Use within labeled indication and guideline-supported standard of care."),
    ]


def _scs_n(c: _NoteCtx):
    return "research_protocol_no_labeling_no_guideline", [
        ("PAIN_MGMT", "PAIN_MANAGEMENT", 40,
         "Percutaneous electrode array placed under research protocol RX-2026-041 (IRB approved). Consent form describes the "
         "device as investigational for this indication. No FDA labeling for this use; no guideline recommendation cited."),
    ]


def _scs_nr(c: _NoteCtx):
    return "consent_conflict_fda_status_and_evidence_missing", [
        ("PAIN_MGMT", "PAIN_MANAGEMENT", 40,
         "Electrode array placed. Consent form states 'standard care' in section 1 and lists a protocol number in section 4. "
         "Device FDA status (PMA vs 510(k)) not documented. Evidence citations listed as 'to be attached'."),
    ]


def _crit_w(c: _NoteCtx):
    return "time_documented_shock_physiology", [
        ("CRIT_CARE_NOTE", "CRITICAL_CARE", 0,
         "Critical care time: 58 minutes, exclusive of separately billed procedures, documented start 02:10, end 03:08. "
         "Septic shock physiology: MAP 58 requiring norepinephrine; lactate 4.2; WBC 22 with left shift; right lower lobe "
         "infiltrate on chest radiograph. Reassessed every 15 minutes; vasopressor titrated. Total critical care time documented."),
        ("ADMIT_NOTE", "HOSPITALIST", 0,
         "Admitted to ICU from emergency department. Broad-spectrum antibiotics started; fluid resuscitation ongoing."),
    ]


def _crit_n(c: _NoteCtx):
    return "stable_no_time_statement", [
        ("CRIT_CARE_NOTE", "CRITICAL_CARE", 0,
         "Patient stable; afebrile; vitals normal; lactate 1.1; viral upper respiratory symptoms. Critical care billed; "
         "no critical care time statement in chart. Care consistent with an office or ED level visit."),
    ]


def _crit_nr(c: _NoteCtx):
    return "time_statements_conflict", [
        ("CRIT_CARE_NOTE", "CRITICAL_CARE", 0,
         "Critical care attestation: 25 minutes. Procedure note (central line): critical care time stated as 45 minutes. "
         "No time breakdown for separately billed procedures. Hypotension documented; lactate 3.4."),
    ]


def _ed_w(c: _NoteCtx):
    return "high_acuity_workup", [
        ("ED_NOTE", "EMERGENCY_PHYSICIAN", 0,
         "ESI level 2. Abdominal pain with hypotension (BP 84/52) and tachycardia 128. Two large-bore IVs, IV fluid resuscitation, "
         "CT abdomen and pelvis with contrast, lactate, surgery consulted for possible ruptured aortic aneurysm versus perforation. "
         "High complexity medical decision making with acute threat to bodily function."),
    ]


def _ed_n(c: _NoteCtx):
    return "minor_complaint_low_complexity", [
        ("ED_NOTE", "EMERGENCY_PHYSICIAN", 0,
         "ESI level 4. Sore throat with cough, afebrile, normal vital signs. Rapid strep negative. Discharged with symptomatic care. "
         "Visit documentation supports a low-complexity emergency level."),
    ]


def _ed_nr(c: _NoteCtx):
    return "workup_described_not_ordered", [
        ("ED_NOTE", "EMERGENCY_PHYSICIAN", 0,
         "Note describes a high-risk workup, but no laboratory or imaging orders are documented. Medical decision making not stated. "
         "Triage ESI 3; physician summary says critical. Abdominal findings limited."),
    ]


def _office_w(c: _NoteCtx):
    return "severe_exacerbation_intensive_monitoring", [
        ("PRIMARY_CARE", "PRIMARY_CARE", 30,
         "Type 2 diabetes with hyperglycemia, A1c 11.2% (8.4% three months ago). Basal insulin started today; requires intensive "
         "monitoring. eGFR declined from 68 to 49 over 6 months; metformin held. Multiple chronic illnesses with severe exacerbation. "
         "Hospitalization considered; outpatient plan with 48-hour nurse call documented."),
    ]


def _office_n(c: _NoteCtx):
    return "stable_refill_visit", [
        ("PRIMARY_CARE", "PRIMARY_CARE", 30,
         "Hypertension, stable on current medication. BP 122/78. Medication refill, no changes. Follow up in 6 months."),
    ]


def _office_nr(c: _NoteCtx):
    return "stable_and_uncontrolled_no_visit_data", [
        ("PRIMARY_CARE", "PRIMARY_CARE", 30,
         "Hypertension described as stable and uncontrolled; three medications adjusted today, but no blood pressure readings or "
         "labs recorded at this visit. Diabetes section lists an A1c without a date."),
    ]


def _cardiac_w(c: _NoteCtx):
    return "troponin_rise_two_midnight_expectation", [
        ("ED_NOTE", "EMERGENCY_PHYSICIAN", 0,
         "Chest pressure for 3 hours. Troponin I 0.08, then 0.92, then 2.6 ng/mL serially (0h, 3h, 6h). ECG: ST depression V4-V6. "
         "Diagnosis non-ST-elevation myocardial infarction. Heparin infusion and aspirin started. Cardiology consulted."),
        ("ADMIT_NOTE", "HOSPITALIST", 0,
         "Admitted inpatient. Expect medically necessary hospital care spanning at least 2 midnights: heparin infusion, serial troponins, "
         "cardiology evaluation for catheterization. Telemetry bed. Inpatient order placed at 16:10."),
    ]


def _cardiac_n(c: _NoteCtx):
    return "negative_troponin_observed_discharged", [
        ("ED_NOTE", "EMERGENCY_PHYSICIAN", 0,
         "Atypical chest discomfort, resolved. Troponin I 0.01 at 0 hours and 0.01 at 3 hours. ECG nonischemic. Observed 12 hours; "
         "ambulated without symptoms; discharged home with outpatient cardiology follow-up."),
    ]


def _cardiac_nr(c: _NoteCtx):
    return "status_conflict_repeat_lab_missing", [
        ("ED_NOTE", "EMERGENCY_PHYSICIAN", 0,
         "Chest pain. Troponin I 0.04 at 0 hours; repeat ordered, result not in chart. Note says 'placed in observation.'"),
        ("ADMIT_NOTE", "HOSPITALIST", 0,
         "Inpatient admission order time 16:10. Utilization review not documented. Status change to inpatient not documented. "
         "Continued on telemetry."),
    ]


def _syncope_w(c: _NoteCtx):
    return "recurrent_pauses_on_monitor_device_eval", [
        ("ED_NOTE", "EMERGENCY_PHYSICIAN", 0,
         "Recurrent syncope three times in 2 weeks without prodrome while seated. 48-hour Holter: pauses to 3.2 seconds during sleep. "
         "Admitted with telemetry for pacemaker evaluation. Expect 2 or more midnights for evaluation and device placement."),
    ]


def _syncope_n(c: _NoteCtx):
    return "single_orthostatic_resolved_observed", [
        ("ED_NOTE", "EMERGENCY_PHYSICIAN", 0,
         "Single brief syncope after standing up quickly, with prodrome. Orthostatic vitals positive; improved with oral fluids. "
         "Observation 12 hours; ECG normal; discharged."),
    ]


def _syncope_nr(c: _NoteCtx):
    return "telemetry_missing_duplicate_status_orders", [
        ("ED_NOTE", "EMERGENCY_PHYSICIAN", 0,
         "Syncope, single episode. Telemetry strip referenced; not in chart. Observation order and inpatient order both dated for the same encounter."),
    ]


NOTE_TEMPLATES = {
    "tka": {"WARRANTED": _tka_w, "NOT WARRANTED": _tka_n, "NEEDS REVIEW": _tka_nr},
    "lumbar_fusion": {"WARRANTED": _lumbar_fusion_w, "NOT WARRANTED": _lumbar_fusion_n, "NEEDS REVIEW": _lumbar_fusion_nr},
    "lumbar_mri": {"WARRANTED": _lumbar_mri_w, "NOT WARRANTED": _lumbar_mri_n, "NEEDS REVIEW": _lumbar_mri_nr},
    "sleep_study": {"WARRANTED": _sleep_w, "NOT WARRANTED": _sleep_n, "NEEDS REVIEW": _sleep_nr},
    "bariatric": {"WARRANTED": _bariatric_w, "NOT WARRANTED": _bariatric_n, "NEEDS REVIEW": _bariatric_nr},
    "scs_trial": {"WARRANTED": _scs_w, "NOT WARRANTED": _scs_n, "NEEDS REVIEW": _scs_nr},
    "critical_care": {"WARRANTED": _crit_w, "NOT WARRANTED": _crit_n, "NEEDS REVIEW": _crit_nr},
    "ed_visit": {"WARRANTED": _ed_w, "NOT WARRANTED": _ed_n, "NEEDS REVIEW": _ed_nr},
    "office_visit": {"WARRANTED": _office_w, "NOT WARRANTED": _office_n, "NEEDS REVIEW": _office_nr},
    "inpatient_cardiac": {"WARRANTED": _cardiac_w, "NOT WARRANTED": _cardiac_n, "NEEDS REVIEW": _cardiac_nr},
    "inpatient_syncope": {"WARRANTED": _syncope_w, "NOT WARRANTED": _syncope_n, "NEEDS REVIEW": _syncope_nr},
}

# --------------------------------------------------------------------------------------------
# encounter construction
# --------------------------------------------------------------------------------------------
def _build_encounter(idx: int, seed: int, as_of: date, label: str, bucket: str, is_hero: bool):
    rng = random.Random(f"fe-bar:{seed}:enc:{idx}")

    # --- keys ----------------------------------------------------------------------------
    if is_hero:
        facility_id = 101
        pcn = 770000001
        enc_nbr = 50000001
    else:
        facility_id = _pick(rng, [f["FACILITY_ID"] for f in C.FACILITIES], [f["weight"] for f in C.FACILITIES])
        pcn = 770000001 + idx
        enc_nbr = 50000001 + idx
    facility = next(f for f in C.FACILITIES if f["FACILITY_ID"] == facility_id)

    # --- payer --------------------------------------------------------------------------
    payer = C.PAYERS[0] if is_hero else _pick(rng, C.PAYERS, [p["weight"] for p in C.PAYERS])
    payer_type = payer["type"]
    limit = C.PAYER_LIMITS[payer_type]

    # --- procedure family -----------------------------------------------------------------
    if is_hero:
        fam_key = "tka"
        carc = "CO50"
    else:
        carc = _pick(rng, list(C.CARC_MIX), list(C.CARC_MIX.values()))
        fam_keys = [k for k, f in C.FAMILIES.items() if f["carc"] == carc]
        fam_key = _pick(rng, fam_keys, [C.FAMILIES[k]["weight"] for k in fam_keys])
    fam = C.FAMILIES[fam_key]

    # --- denial / deadline ---------------------------------------------------------------
    if is_hero:
        days_remaining = HERO_DAYS_REMAINING
    elif bucket == "NEW":  # denied yesterday: denial_date == as_of - 1 day
        days_remaining = limit - 1
    elif bucket == "PAST_DUE":
        days_remaining = -rng.randint(1, 60)
    elif bucket == "AT_RISK":
        days_remaining = rng.randint(0, 14)
    else:
        days_remaining = rng.randint(15, min(150, limit - 2))  # denial <= as_of - 2: never 'NEW'
    denial_date = as_of + timedelta(days=days_remaining - limit)
    dos = (denial_date - timedelta(days=HERO_DOS_BEFORE_DENIAL)) if is_hero else \
        (denial_date - timedelta(days=rng.randint(10, 30)))

    # --- demographics -----------------------------------------------------------------------
    if is_hero:
        name, sex, dob = "Elena Marquez", "F", "1962-03-14"
        member_id = "W482915037"
        mrn = "MR4829150"
    else:
        sex = rng.choice(["F", "M"])
        first = rng.choice(C.FIRST_NAMES_F if sex == "F" else C.FIRST_NAMES_M)
        name = f"{first} {rng.choice(C.LAST_NAMES)}"
        dob_date = date(1935, 1, 1) + timedelta(days=rng.randint(0, 24000))
        dob = dob_date.isoformat()
        member_id = f"W{rng.randint(100000000, 999999999)}"
        mrn = f"MR{rng.randint(1000000, 9999999)}"

    claim_number = 600000000 + idx
    denial_id = f"DN-{enc_nbr}"
    bill_date = dos + timedelta(days=4 if is_hero else rng.randint(3, 7))

    # --- lines -------------------------------------------------------------------------------
    lines_spec = []  # (cpt, mod, dx_primary, dx_extra, charges, expected, los_days)
    if is_hero:
        mod = "RT"
        dx_primary = "M17.11"
        dx_extra = ["M25.561", "Z68.31"]
        lines_spec.append((fam["cpt"], mod, dx_primary, dx_extra, 58400.00, 24850.00, 0))
    else:
        mod = None
        if fam["mods"]:
            mod = _pick(rng, fam["mods"], [0.7, 0.3])
        dx_primary = rng.choice(list(fam["dx"]))
        if fam["lat"]:
            dx_primary = "M17.11" if mod == "RT" else "M17.12"
        dx_extra = list(fam["extra"])
        if fam["lat"]:
            dx_extra = ["M25.561" if mod == "RT" else "M25.562", "Z68.31"]
        charges, expected = _money(rng, *fam["exp"])
        los = fam["los"]
        lines_spec.append((fam["cpt"], mod, dx_primary, dx_extra, charges, expected, los))
        if fam["anc"] and rng.random() < 0.35:
            anc_cpt, lo, hi = fam["anc"]
            a_charges, a_expected = _money(rng, lo, hi)
            lines_spec.append((anc_cpt, None, dx_primary, dx_extra, a_charges, a_expected, 0))

    total_charges = round(sum(ls[4] for ls in lines_spec), 2)
    los_max = max(ls[6] for ls in lines_spec)
    period = f"{dos.isoformat()} - {(dos + timedelta(days=los_max)).isoformat()}"

    # --- claim lines -------------------------------------------------------------------------
    line_base = 5000000000 + idx * 10
    claims = []
    for k, (cpt, mod_k, dxp, dxe, charges, expected, _) in enumerate(lines_spec):
        rec = {
            "PATIENT_NAME": name,
            "PATIENT_BIRTHDATE": dob,
            "PATIENT_SEX": sex,
            "PATIENT_CONTROL_NUMBER": pcn,
            "FACILITY_ID": facility_id,
            "MEDICAL_RECORD_NUMBER": mrn,
            "STATEMENT_COVERS_PERIOD": period,
            "TOTAL_CHARGES": total_charges,
            "SITEID": facility["SITEID"],
            "CLAIM_NUMBER": claim_number,
            "PAYER_NAME": payer["name"],
            "PAYER_ADDRESS_STREET": payer["street"],
            "PAYER_CSZ": payer["csz"],
            "TYPE_OF_BILL": fam["tob"],
            "HEALTH_PLAN_ID": payer["plan"],
            "FEDERAL_TAX_ID": facility["FEDERAL_TAX_ID"],
            "PROVIDER_NAME": facility["PROVIDER_NAME"],
            "BILL_DATE": bill_date.isoformat(),
            "DENIAL_ID": denial_id,
            "DENIAL_CODE": carc,
            "PATIENTIDENTITYCODE": "18",
            "CLAIMPOLICYNUMBER": member_id,
            "DATE_PAID": denial_date.isoformat(),
            "HCPCS_CODE": cpt,
            "MOD1": mod_k,
            "POS": float(fam["pos"]),
            "REV_CODE": fam["rev"],
            "DOS": dos.isoformat(),
            "LINE_ITEM_CONTROL_NUMBER": line_base + k,
            "ADMIT_DIAG": dxp,
            "DISCH_DIAG1": dxp,
            "DISCH_DIAG2": dxe[0] if len(dxe) > 0 else None,
            "DISCH_DIAG3": dxe[1] if len(dxe) > 1 else None,
            "DISCH_DIAG4": dxe[2] if len(dxe) > 2 else None,
            "DISCH_DIAG5": None,
            "DISCH_DIAG6": None,
            "ENCOUNTER_NBR": enc_nbr,
            "DENIAL_DATE": denial_date.isoformat(),
            "PAYER_TYPE": payer_type,
            "APPEAL_LIMIT_DAYS": limit,
            "EXPECTED_REIMBURSEMENT": expected,
            "SOURCE_BATCH": f"batch_{as_of.isoformat()}_seed{seed}_n{0}",  # patched by caller
        }
        claims.append(rec)

    # --- clinical notes + label ------------------------------------------------------------------
    rng_notes = random.Random(f"fe-bar:{seed}:notes:{idx}")
    # Laterality: the chart names the same side as the claim modifier (LT = left knee, RT = right knee).
    line_mod = lines_spec[0][1] if fam["lat"] else None
    ctx = _NoteCtx(dos, rng_notes, side="left" if line_mod == "LT" else "right", mod=line_mod or "RT")
    variant, note_specs = NOTE_TEMPLATES[fam_key][label](ctx)
    notes = []
    for k, (tag, role, days_before, text) in enumerate(note_specs, start=1):
        notes.append({
            "FACILITY_ID": facility_id,
            "PATIENT_CONTROL_NUMBER": pcn,
            "ENCOUNTER_NBR": enc_nbr,
            "PATIENT_NAME": name,
            "event_id": idx * 100 + k,
            "event_tag": tag,
            "note_date": (dos - timedelta(days=days_before)).isoformat(),
            "author_role": role,
            "plain_text": text,
        })

    label_row = {
        "FACILITY_ID": facility_id,
        "PATIENT_CONTROL_NUMBER": pcn,
        "ENCOUNTER_NBR": enc_nbr,
        "expected_determination": label,
        "scenario": f"{fam_key}:{variant}",
        "is_hero": is_hero,
    }
    enc_manifest = {
        "FACILITY_ID": facility_id,
        "PATIENT_CONTROL_NUMBER": pcn,
        "ENCOUNTER_NBR": enc_nbr,
        "expected_determination": label,
        "scenario": f"{fam_key}:{variant}",
        "carc": carc,
        "family": fam_key,
        "payer_type": payer_type,
        "deadline_bucket": "AT_RISK" if is_hero else bucket,
        "days_remaining": days_remaining,
        "denial_date": denial_date.isoformat(),
        "dos": dos.isoformat(),
        "total_charges": total_charges,
        "expected_reimbursement": round(sum(ls[5] for ls in lines_spec), 2),
        "n_lines": len(claims),
        "n_notes": len(notes),
    }
    return claims, notes, label_row, enc_manifest


def _inject_defects(claims: List[dict], rng: random.Random, eligible_enc: List[int]) -> List[dict]:
    """Inject ~1.5% deliberately bad lines (one batch of rows per defect kind) so the SDP expectations
    visibly drop or warn. Defect lines copy a real line of a non-hero encounter; they never create
    encounters or labels. Each defect line gets a unique LINE_ITEM_CONTROL_NUMBER (9900000001+)."""
    if not eligible_enc:
        return []
    per_kind = max(1, round(0.015 * len(claims) / len(DEFECT_KINDS)))
    first_line_by_enc: Dict[int, dict] = {}
    for rec in claims:
        first_line_by_enc.setdefault(rec["ENCOUNTER_NBR"], rec)
    manifest = []
    serial = 0
    for kind in DEFECT_KINDS:
        for _ in range(per_kind):
            serial += 1
            tpl = dict(first_line_by_enc[rng.choice(eligible_enc)])
            tpl["LINE_ITEM_CONTROL_NUMBER"] = 9900000000 + serial
            if kind == "bad_carc":
                tpl["DENIAL_CODE"] = "CO97"
            elif kind == "dos_after_denial":
                tpl["DOS"] = (date.fromisoformat(tpl["DENIAL_DATE"]) + timedelta(days=2)).isoformat()
            elif kind == "null_key":
                tpl["PATIENT_CONTROL_NUMBER"] = None
            elif kind == "negative_expected":
                tpl["EXPECTED_REIMBURSEMENT"] = -round(abs(tpl["EXPECTED_REIMBURSEMENT"]) * 0.5, 2)
            claims.append(tpl)
            manifest.append({
                "kind": kind,
                "FACILITY_ID": tpl["FACILITY_ID"],
                "PATIENT_CONTROL_NUMBER": tpl["PATIENT_CONTROL_NUMBER"],
                "ENCOUNTER_NBR": tpl["ENCOUNTER_NBR"],
                "LINE_ITEM_CONTROL_NUMBER": tpl["LINE_ITEM_CONTROL_NUMBER"],
                "expected_outcome": "warn_kept" if kind == "negative_expected" else "dropped",
            })
    return manifest


def generate(seed: int = DEFAULT_SEED, n_encounters: int = DEFAULT_N_ENCOUNTERS,
             as_of_date: Optional[date] = None) -> Batch:
    """Generate one deterministic batch. Encounter 0 is always the hero claim (Elena Marquez)."""
    if n_encounters < 1:
        raise ValueError("n_encounters must be >= 1")
    as_of = as_of_date or date.today()
    label_list, bucket_list, _ = _plan_labels_and_buckets(seed, n_encounters)

    claims: List[dict] = []
    notes: List[dict] = []
    labels: List[dict] = []
    enc_manifest: List[dict] = []
    for idx in range(n_encounters):
        is_hero = idx == 0
        label = "WARRANTED" if is_hero else label_list[idx - 1]
        bucket = "AT_RISK" if is_hero else bucket_list[idx - 1]
        c, n, l, m = _build_encounter(idx, seed, as_of, label, bucket, is_hero)
        claims.extend(c)
        notes.extend(n)
        labels.append(l)
        enc_manifest.append(m)

    source_batch = f"batch_{as_of.isoformat()}_seed{seed}_n{n_encounters}"
    for rec in claims:
        rec["SOURCE_BATCH"] = source_batch

    # defects: attach to non-hero encounters (hero is encounter 0)
    eligible = [e["ENCOUNTER_NBR"] for e in enc_manifest if e["ENCOUNTER_NBR"] != HERO_KEYS["ENCOUNTER_NBR"]]
    defect_rng = random.Random(f"fe-bar:{seed}:defects")
    defects = _inject_defects(claims, defect_rng, eligible)
    n_valid = len(claims) - len(defects)
    for rec in claims:  # defect rows were copied before the batch tag was known; tag every row
        rec["SOURCE_BATCH"] = source_batch

    manifest = {
        "generator_version": GENERATOR_VERSION,
        "seed": seed,
        "n_encounters": n_encounters,
        "as_of_date": as_of.isoformat(),
        "source_batch": source_batch,
        "n_claim_lines_valid": n_valid,
        "n_claim_lines_total": len(claims),
        "n_notes": len(notes),
        "label_counts": {k: sum(1 for l in labels if l["expected_determination"] == k) for k in LABELS},
        "defects": defects,
        "encounters": enc_manifest,
    }
    for l in labels:
        l["generator_seed"] = seed
        l["as_of_date"] = as_of.isoformat()
    return Batch(seed=seed, n_encounters=n_encounters, as_of_date=as_of, claims=claims,
                 notes=notes, labels=labels, manifest=manifest)

