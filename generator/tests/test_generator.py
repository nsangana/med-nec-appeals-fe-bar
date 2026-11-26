"""Generator tests: determinism, schema, label/deadline mix, hero claim, date and key integrity, note hygiene."""
import json
import random
import re
from collections import Counter
from datetime import date, timedelta

import pytest

from generator import LABELS, generate
from generator.core import CLAIM_FIELDS, DEFAULT_SEED, NOTE_FIELDS, DEFECT_KINDS, HERO_KEYS

AS_OF = date(2026, 11, 24)
N = 500


@pytest.fixture(scope="module")
def batch():
    return generate(seed=DEFAULT_SEED, n_encounters=N, as_of_date=AS_OF)


def _dump(b):
    return json.dumps({"claims": b.claims, "notes": b.notes, "labels": b.labels, "manifest": b.manifest},
                      sort_keys=True)


def _valid_claims(b):
    defect_lines = {d["LINE_ITEM_CONTROL_NUMBER"] for d in b.manifest["defects"]}
    return [c for c in b.claims if c["LINE_ITEM_CONTROL_NUMBER"] not in defect_lines]


def _encounters(b):
    return {(c["FACILITY_ID"], c["PATIENT_CONTROL_NUMBER"], c["ENCOUNTER_NBR"]) for c in _valid_claims(b)}


# ---------------------------------------------------------------- determinism
def test_same_seed_identical_output(batch):
    again = generate(seed=DEFAULT_SEED, n_encounters=N, as_of_date=AS_OF)
    assert _dump(batch) == _dump(again)


def test_different_seed_changes_output(batch):
    other = generate(seed=DEFAULT_SEED + 1, n_encounters=N, as_of_date=AS_OF)
    assert _dump(batch) != _dump(other)


def test_default_seed_is_spec_seed():
    assert DEFAULT_SEED == 20261124


# ---------------------------------------------------------------- schema
def test_claim_schema_complete(batch):
    expected = set(CLAIM_FIELDS)
    for rec in batch.claims:
        assert set(rec) == expected


def test_claim_new_fields_present_and_typed(batch):
    for rec in _valid_claims(batch):
        assert rec["PAYER_TYPE"] in {"COMMERCIAL", "MEDICARE_ADVANTAGE", "MEDICAID"}
        assert rec["APPEAL_LIMIT_DAYS"] == {"COMMERCIAL": 180, "MEDICARE_ADVANTAGE": 65, "MEDICAID": 60}[rec["PAYER_TYPE"]]
        assert isinstance(rec["EXPECTED_REIMBURSEMENT"], float)
        assert rec["SOURCE_BATCH"] == f"batch_2026-11-24_seed{DEFAULT_SEED}_n{N}"
        date.fromisoformat(rec["DENIAL_DATE"])


def test_note_schema_complete(batch):
    for rec in batch.notes:
        assert set(rec) == set(NOTE_FIELDS)
        assert rec["plain_text"].strip()
        date.fromisoformat(rec["note_date"])


def test_label_schema_complete(batch):
    cols = {"FACILITY_ID", "PATIENT_CONTROL_NUMBER", "ENCOUNTER_NBR", "expected_determination", "scenario",
            "is_hero", "generator_seed", "as_of_date"}
    for row in batch.labels:
        assert cols <= set(row)
        assert row["expected_determination"] in LABELS


# ---------------------------------------------------------------- keys
def test_encounter_count_and_keys_unique(batch):
    assert len(batch.labels) == N
    keys = [(l["FACILITY_ID"], l["PATIENT_CONTROL_NUMBER"], l["ENCOUNTER_NBR"]) for l in batch.labels]
    assert len(set(keys)) == N
    assert len(_encounters(batch)) == N  # every encounter has at least one valid line


def test_line_numbers_unique(batch):
    lines = [c["LINE_ITEM_CONTROL_NUMBER"] for c in batch.claims]
    assert len(set(lines)) == len(lines)


def test_note_event_ids_unique_per_encounter(batch):
    seen = Counter((n["FACILITY_ID"], n["PATIENT_CONTROL_NUMBER"], n["ENCOUNTER_NBR"], n["event_id"])
                   for n in batch.notes)
    assert max(seen.values()) == 1


def test_every_encounter_has_notes(batch):
    enc_with_notes = {(n["FACILITY_ID"], n["PATIENT_CONTROL_NUMBER"], n["ENCOUNTER_NBR"]) for n in batch.notes}
    assert enc_with_notes == _encounters(batch)


# ---------------------------------------------------------------- label + deadline mix
def test_label_mix_within_tolerance(batch):
    total = len(batch.labels)
    counts = Counter(l["expected_determination"] for l in batch.labels)
    assert abs(counts["WARRANTED"] / total - 0.45) <= 0.05
    assert abs(counts["NOT WARRANTED"] / total - 0.35) <= 0.05
    assert abs(counts["NEEDS REVIEW"] / total - 0.20) <= 0.05


def test_deadline_mix_within_tolerance(batch):
    total = len(batch.labels)
    by_enc = {(e["FACILITY_ID"], e["PATIENT_CONTROL_NUMBER"], e["ENCOUNTER_NBR"]): e
              for e in batch.manifest["encounters"]}
    past = sum(1 for e in by_enc.values() if e["days_remaining"] < 0)
    at_risk = sum(1 for e in by_enc.values() if 0 <= e["days_remaining"] <= 14)
    assert abs(past / total - 0.08) <= 0.02
    assert abs(at_risk / total - 0.15) <= 0.03


def test_deadline_days_consistent_with_denial(batch):
    for e in batch.manifest["encounters"]:
        if e["deadline_bucket"] == "AT_RISK" and e["days_remaining"] == 9:
            continue
        denial = date.fromisoformat(e["denial_date"])
        limit = {"COMMERCIAL": 180, "MEDICARE_ADVANTAGE": 65, "MEDICAID": 60}[e["payer_type"]]
        assert (denial + timedelta(days=limit) - AS_OF).days == e["days_remaining"]


def test_carc_mix_covers_all_five(batch):
    carcs = Counter(c["DENIAL_CODE"] for c in _valid_claims(batch))
    assert set(carcs) == {"CO50", "CO55", "CO57", "CO150", "CO186"}


def test_payer_mix_has_all_payer_types(batch):
    names = {c["PAYER_NAME"] for c in _valid_claims(batch)}
    for required in ("BCBS of Arizona", "BCBS of Arizona Medicare Advantage", "UnitedHealthcare", "Aetna",
                     "Cigna", "Humana Medicare Advantage", "UnitedHealthcare Medicare Advantage", "AHCCCS Medicaid"):
        assert required in names


def test_procedures_fit_carc(batch):
    allowed = {
        "CO50": {"27447", "01402", "22612", "22840", "72148", "95810", "43775"},
        "CO55": {"63650"},
        "CO57": {"99291"},
        "CO150": {"99285", "99215"},
        "CO186": {"99223"},
    }
    for c in _valid_claims(batch):
        assert c["HCPCS_CODE"] in allowed[c["DENIAL_CODE"]], (c["DENIAL_CODE"], c["HCPCS_CODE"])


def test_expected_reimbursement_well_below_charges(batch):
    per_enc = {}
    for c in _valid_claims(batch):
        k = (c["FACILITY_ID"], c["PATIENT_CONTROL_NUMBER"], c["ENCOUNTER_NBR"])
        per_enc.setdefault(k, [c["TOTAL_CHARGES"], 0.0])[1] += c["EXPECTED_REIMBURSEMENT"]
    for charges, expected in per_enc.values():
        assert 0 < expected < charges * 0.6


def test_non_hero_expected_below_hero_cap(batch):
    # keeps the hero at or near the top of the worklist (SPEC: priority near top)
    hero = HERO_KEYS
    per_enc = {}
    for c in _valid_claims(batch):
        k = (c["FACILITY_ID"], c["PATIENT_CONTROL_NUMBER"], c["ENCOUNTER_NBR"])
        per_enc[k] = per_enc.get(k, 0.0) + c["EXPECTED_REIMBURSEMENT"]
    for k, v in per_enc.items():
        if k != (hero["FACILITY_ID"], hero["PATIENT_CONTROL_NUMBER"], hero["ENCOUNTER_NBR"]):
            assert v < 24850.0


# ---------------------------------------------------------------- hero claim (exact per SPEC)
def test_hero_claim_exact(batch):
    hero = [c for c in batch.claims if c["PATIENT_CONTROL_NUMBER"] == 770000001]
    assert len(hero) == 1
    h = hero[0]
    assert (h["FACILITY_ID"], h["PATIENT_CONTROL_NUMBER"], h["ENCOUNTER_NBR"]) == (101, 770000001, 50000001)
    assert h["PATIENT_NAME"] == "Elena Marquez"
    assert h["PATIENT_SEX"] == "F"
    assert h["PATIENT_BIRTHDATE"] == "1962-03-14"
    assert h["PAYER_NAME"] == "BCBS of Arizona"
    assert h["PAYER_TYPE"] == "COMMERCIAL"
    assert h["HCPCS_CODE"] == "27447"
    assert h["MOD1"] == "RT"
    assert h["DENIAL_CODE"] == "CO50"
    assert h["DISCH_DIAG1"] == "M17.11"
    assert h["DISCH_DIAG2"] == "M25.561"
    assert h["DISCH_DIAG3"] == "Z68.31"
    assert h["TOTAL_CHARGES"] == 58400.00
    assert h["EXPECTED_REIMBURSEMENT"] == 24850.00
    assert h["APPEAL_LIMIT_DAYS"] == 180
    assert h["DENIAL_DATE"] == (AS_OF - timedelta(days=171)).isoformat() == "2026-06-06"
    deadline = date.fromisoformat(h["DENIAL_DATE"]) + timedelta(days=h["APPEAL_LIMIT_DAYS"])
    assert (deadline - AS_OF).days == 9


def test_hero_label_and_scenario(batch):
    hero = [l for l in batch.labels if l["PATIENT_CONTROL_NUMBER"] == 770000001]
    assert len(hero) == 1
    assert hero[0]["expected_determination"] == "WARRANTED"
    assert hero[0]["is_hero"] is True
    assert sum(1 for l in batch.labels if l["is_hero"]) == 1


def test_hero_notes_document_the_chain(batch):
    text = " ".join(n["plain_text"] for n in batch.notes if n["PATIENT_CONTROL_NUMBER"] == 770000001)
    for needle in ("NSAID", "Naproxen", "12 supervised visits", "Kellgren-Lawrence grade 4", "one block",
                   "KOOS", "injection", "3 weeks", "rationale"):
        assert needle.lower() in text.lower(), needle


# ---------------------------------------------------------------- dates
def test_dos_before_denial_for_valid_lines(batch):
    for c in _valid_claims(batch):
        assert date.fromisoformat(c["DOS"]) < date.fromisoformat(c["DENIAL_DATE"])


def test_defects_are_the_only_dos_violations(batch):
    violators = [c for c in batch.claims if date.fromisoformat(c["DOS"]) >= date.fromisoformat(c["DENIAL_DATE"])]
    dos_defects = {d["LINE_ITEM_CONTROL_NUMBER"] for d in batch.manifest["defects"] if d["kind"] == "dos_after_denial"}
    assert {c["LINE_ITEM_CONTROL_NUMBER"] for c in violators} == dos_defects


def test_note_dates_not_after_dos(batch):
    dos_by_enc = {}
    for c in _valid_claims(batch):
        dos_by_enc[(c["FACILITY_ID"], c["PATIENT_CONTROL_NUMBER"], c["ENCOUNTER_NBR"])] = c["DOS"]
    for n in batch.notes:
        k = (n["FACILITY_ID"], n["PATIENT_CONTROL_NUMBER"], n["ENCOUNTER_NBR"])
        assert n["note_date"] <= dos_by_enc[k]


# ---------------------------------------------------------------- defects
def test_defect_injection_about_two_percent_and_all_kinds(batch):
    defects = batch.manifest["defects"]
    assert 0.005 <= len(defects) / len(batch.claims) <= 0.02
    assert {d["kind"] for d in defects} == set(DEFECT_KINDS)


def test_defects_never_hit_hero(batch):
    assert all(d["PATIENT_CONTROL_NUMBER"] != 770000001 for d in batch.manifest["defects"])


# ---------------------------------------------------------------- note hygiene
LABEL_WORDS = re.compile(r"warrant|needs review|not warranted|expected_determination|scenario", re.I)


def test_notes_never_mention_label(batch):
    for n in batch.notes:
        assert not LABEL_WORDS.search(n["plain_text"]), n["plain_text"]
        assert not LABEL_WORDS.search(n["event_tag"])


def test_every_label_has_note_variety(batch):
    scenarios = Counter(l["scenario"] for l in batch.labels)
    assert len(scenarios) >= 25
    assert all(l["scenario"].split(":")[0] in {"tka", "lumbar_fusion", "lumbar_mri", "sleep_study", "bariatric",
                                              "scs_trial", "critical_care", "ed_visit", "office_visit",
                                              "inpatient_cardiac", "inpatient_syncope"} for l in batch.labels)


def test_small_batch_works():
    b = generate(seed=7, n_encounters=10, as_of_date=AS_OF)
    assert len(b.labels) == 10
    assert b.labels[0]["is_hero"] is True


def test_denied_yesterday_encounters(batch):
    # ADDENDUM 1: ~20 encounters denied yesterday (denial_date = as_of - 1 day); hero unchanged
    new = [e for e in batch.manifest["encounters"] if e["deadline_bucket"] == "NEW"]
    assert len(new) == 20  # round(0.04 * 500)
    # and no other encounter is 'denied yesterday or today' (keeps worklist_tag NEW == the designed 20)
    others = [e for e in batch.manifest["encounters"] if e["deadline_bucket"] != "NEW"]
    assert all(date.fromisoformat(e["denial_date"]) <= AS_OF - timedelta(days=2) for e in others)
    for e in new:
        assert e["denial_date"] == (AS_OF - timedelta(days=1)).isoformat()
        assert e["days_remaining"] > 14
    hero = [e for e in batch.manifest["encounters"] if e["ENCOUNTER_NBR"] == 50000001]
    assert hero[0]["deadline_bucket"] == "AT_RISK" and hero[0]["days_remaining"] == 9


def test_denied_yesterday_labels_still_mixed(batch):
    new_keys = {(e["FACILITY_ID"], e["PATIENT_CONTROL_NUMBER"], e["ENCOUNTER_NBR"])
                for e in batch.manifest["encounters"] if e["deadline_bucket"] == "NEW"}
    labels = Counter(l["expected_determination"] for l in batch.labels
                     if (l["FACILITY_ID"], l["PATIENT_CONTROL_NUMBER"], l["ENCOUNTER_NBR"]) in new_keys)
    assert len(labels) == 3


# ---------------------------------------------------------------- laterality (TKA)
SIDE_RE = re.compile(r"\b(right|left) knee\b", re.I)


def _tka_encounters(b):
    """(key -> claim line) for valid primary TKA lines (CPT 27447)."""
    out = {}
    for c in _valid_claims(b):
        if c["HCPCS_CODE"] == "27447":
            out[(c["FACILITY_ID"], c["PATIENT_CONTROL_NUMBER"], c["ENCOUNTER_NBR"])] = c
    return out


def test_tka_modifier_matches_side_documented_in_notes(batch):
    """Claim laterality (MOD1, ICD-10 M17.11 vs M17.12) must match the knee the notes document."""
    notes_by_enc = {}
    for n in batch.notes:
        notes_by_enc.setdefault((n["FACILITY_ID"], n["PATIENT_CONTROL_NUMBER"], n["ENCOUNTER_NBR"]), []).append(n)
    tka = _tka_encounters(batch)
    assert tka, "default batch must contain TKA encounters"
    seen_mods = set()
    for key, line in tka.items():
        mod = line["MOD1"]
        seen_mods.add(mod)
        assert mod in ("RT", "LT"), (key, mod)
        sides = {m.group(1).lower() for n in notes_by_enc[key] for m in SIDE_RE.finditer(n["plain_text"])}
        expected_side = "right" if mod == "RT" else "left"
        other_side = "left" if expected_side == "right" else "right"
        assert sides == {expected_side}, (key, mod, sides)
        assert other_side not in sides
        assert line["DISCH_DIAG1"] == ("M17.11" if mod == "RT" else "M17.12"), key
        assert line["DISCH_DIAG2"] == ("M25.561" if mod == "RT" else "M25.562"), key
    assert seen_mods == {"RT", "LT"}, "both laterality cases must occur in the default batch"


def test_tka_warranted_ortho_note_cites_modifier(batch):
    """The WARRANTED ortho consult names the procedure with the same modifier as the claim line."""
    tka = _tka_encounters(batch)
    checked = 0
    for n in batch.notes:
        if n["event_tag"] != "ORTHO_CONSULT" or "27447-" not in n["plain_text"]:
            continue
        key = (n["FACILITY_ID"], n["PATIENT_CONTROL_NUMBER"], n["ENCOUNTER_NBR"])
        assert f"27447-{tka[key]['MOD1']}" in n["plain_text"], key
        checked += 1
    assert checked >= 1


def test_hero_tka_note_is_right_knee_rt(batch):
    hero = [n for n in batch.notes if n["PATIENT_CONTROL_NUMBER"] == 770000001]
    assert "27447-RT" in " ".join(n["plain_text"] for n in hero)


# ---------------------------------------------------------------- SCS WARRANTED template (CO55 label defensibility)
SCS_W = "scs_trial:fda_labeled_use_guideline_supported"


def test_scs_warranted_template_elements_direct():
    """The WARRANTED spinal cord stimulator chart carries a dated lumbar MRI and a named PMA-approved device."""
    from generator.core import NOTE_TEMPLATES, _NoteCtx
    dos = date(2026, 3, 1)
    variant, specs = NOTE_TEMPLATES["scs_trial"]["WARRANTED"](_NoteCtx(dos, random.Random(0)))
    assert variant == "fda_labeled_use_guideline_supported"
    mri = [s for s in specs if s[0] == "IMAGING_MRI"]
    assert len(mri) == 1
    tag, role, days_before, text = mri[0]
    assert "MRI lumbar spine" in text
    assert f"({(dos - timedelta(days=days_before)).isoformat()})" in text  # the MRI date is written in the note
    assert days_before > 40  # imaging precedes the trial placement (40 days before DOS)
    device_text = " ".join(s[3] for s in specs)
    assert "Intellis" in device_text
    assert "FDA premarket approval (PMA)" in device_text
    assert "labeled indication" in device_text


def test_scs_warranted_batch_chart_has_dated_mri_and_pma_device(batch):
    keys = {(l["FACILITY_ID"], l["PATIENT_CONTROL_NUMBER"], l["ENCOUNTER_NBR"])
            for l in batch.labels if l["scenario"] == SCS_W}
    assert keys, "default batch must contain WARRANTED SCS encounters"
    dos_by_enc = {(c["FACILITY_ID"], c["PATIENT_CONTROL_NUMBER"], c["ENCOUNTER_NBR"]): c["DOS"]
                  for c in _valid_claims(batch)}
    for key in keys:
        chart = [n for n in batch.notes if (n["FACILITY_ID"], n["PATIENT_CONTROL_NUMBER"], n["ENCOUNTER_NBR"]) == key]
        mri = [n for n in chart if n["event_tag"] == "IMAGING_MRI" and "MRI lumbar spine" in n["plain_text"]]
        assert mri, key
        assert all(n["note_date"] < dos_by_enc[key] for n in mri), key
        assert any("PMA" in n["plain_text"] and "FDA" in n["plain_text"] and "Intellis" in n["plain_text"]
                   for n in chart), key
