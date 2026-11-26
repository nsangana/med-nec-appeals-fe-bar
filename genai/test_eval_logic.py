"""Unit tests for eval_logic (scorer logic behind pipeline/65_genai_evaluate.py)."""
from pathlib import Path

import pytest

from eval_logic import (
    GROUNDING_FIELDS, PLACEHOLDER_RULE, build_grounding_docs, determination_matches, estimate_judge_cost,
    generation_blocks, grounding_text, quote_check, quote_text, rate,
)

GEN_SQL = Path(__file__).resolve().parent.parent / "pipeline" / "30_generate_appeals.sql"

NOTES = "[2026-03-14 PT_VISIT] Patient completed 12 PT sessions over six weeks with persistent pain at L4-L5."
CRITERIA = "Conservative therapy of at least six weeks with documented failure is required for lumbar fusion."


def _row(**over):
    base = {
        "patient_name": "Test Patient", "dob": "1944-10-14 00:00:00", "sex": "F", "payer_name": "Payer X",
        "member_id": "MEM-1", "claim_number": 600000402, "dos": "2026-05-15 00:00:00", "pos": 22.0,
        "hcpcs_codes": "27447", "modifiers": "RT", "dx_codes": "M17.11", "total_charges": 1234.5,
        "provider_name": "Dr Example", "denial_code": "CO-50", "reason_text": "not medically necessary",
        "what_to_prove": "medical necessity", "criteria_payer": "Commercial criteria", "criteria_block": CRITERIA,
        "mpfs_context": "MPFS line", "notes_full": NOTES, "clinical_digest": "Digest text",
    }
    base.update(over)
    return base


# ---- quote metric (60_evaluate definition) --------------------------------------------------------------

def test_quote_strict_verbatim_is_verified():
    text = f'The chart states "{NOTES[:60]}" and supports the request.'
    assert quote_check(text, NOTES) == {"total": 1, "strict": 1, "normalised": 1}


def test_quote_not_in_grounding_is_unverified():
    text = 'The note says "the patient was seen by a cardiologist last spring for chest pain".'
    q = quote_check(text, NOTES)
    assert q["total"] == 1 and q["strict"] == 0 and q["normalised"] == 0


def test_short_quotes_are_ignored():
    assert quote_check('It was "short" and "also short".', NOTES)["total"] == 0


def test_quotes_across_lines_are_not_paired():
    text = '"first half of a long span that\nspans lines and ends here quietly"'
    assert quote_check(text, NOTES)["total"] == 0


def test_normalised_ignores_punctuation_and_case_and_ellipsis():
    quoted = '"PT SESSIONS over six weeks, with persistent pain at L4-L5..."'
    q = quote_check(f"Letter: {quoted}", NOTES)
    assert q == {"total": 1, "strict": 0, "normalised": 1}


def test_normalised_fails_when_a_fragment_is_not_in_grounding():
    quoted = '"PT sessions over six weeks ... cardiology referral was never documented"'
    q = quote_check(f"x {quoted}", NOTES)
    assert q["total"] == 1 and q["normalised"] == 0


def test_quote_text_is_letter_then_worksheet():
    assert quote_text("A", "B") == "A\nB"
    assert quote_text(None, None) == "\n"


def test_quote_check_handles_empty_inputs():
    assert quote_check("", "") == {"total": 0, "strict": 0, "normalised": 0}
    assert quote_check(None, None) == {"total": 0, "strict": 0, "normalised": 0}


def test_quote_grounding_keeps_60_evaluate_field_set_without_patient_name():
    row = _row(patient_name="SHOULD NOT APPEAR IN QUOTE GROUNDING", mpfs_context=None)
    g = grounding_text(row)
    assert "SHOULD NOT APPEAR" not in g
    assert NOTES in g and CRITERIA in g
    assert "patient_name" not in GROUNDING_FIELDS
    assert "dos" not in GROUNDING_FIELDS and "total_charges" not in GROUNDING_FIELDS


# ---- shared generation-context builder ------------------------------------------------------------------

def test_claim_block_has_the_generator_fields_in_order():
    claim = generation_blocks(_row())["claim"]
    lines = claim.splitlines()
    assert lines[0] == "CLAIM:"
    assert lines[1] == "- Patient: Test Patient, DOB 1944-10-14 00:00:00, Sex F"
    assert lines[2] == "- Payer: Payer X, Member ID MEM-1, Claim 600000402"
    assert lines[3] == "- Date of Service: 2026-05-15 00:00:00, POS 22.0"
    assert lines[4] == "- Procedures (CPT/HCPCS): 27447  Modifiers: RT"
    assert lines[5] == "- Diagnoses (ICD-10): M17.11"
    assert lines[6] == "- Total charges: $1234.5"
    assert lines[7] == "- Provider: Dr Example"


def test_null_fields_follow_the_sql_coalesce_fallbacks():
    b = generation_blocks(_row(member_id=None, modifiers=None, mpfs_context=None, notes_full=None,
                               patient_name=None))
    assert "Member ID [Member ID]" in b["claim"]
    assert "Modifiers: (none)" in b["claim"]
    assert "(n/a)" in b["mpfs"]
    assert "(no notes)" in b["notes"]
    assert "- Patient: , DOB" in b["claim"]  # plain coalesce(x,'') -> empty


def test_criteria_and_denial_blocks_use_generator_wording():
    b = generation_blocks(_row())
    assert b["criteria"].startswith("APPLICABLE MEDICAL-NECESSITY CRITERIA (Commercial criteria):\n- ")
    assert b["denial"] == ("2. Denial CO-50 - not medically necessary. "
                           "The appeal must prove: medical necessity.\n")


def test_grounding_docs_are_retrieval_chunks_and_include_placeholder_rule():
    docs = build_grounding_docs(_row())
    assert [d["metadata"]["doc_uri"] for d in docs] == [
        "claim", "denial", "criteria", "clinical_notes", "clinical_digest", "mpfs", "generation_rules"]
    assert all(isinstance(d["page_content"], str) and d["page_content"] for d in docs)
    claim_chunk = docs[0]["page_content"]
    assert "Test Patient" in claim_chunk and "MEM-1" in claim_chunk  # identifiers the generator saw are grounding
    assert docs[-1]["page_content"] == PLACEHOLDER_RULE


def test_grounding_docs_tolerate_nulls():
    docs = build_grounding_docs({"notes_full": None})
    assert len(docs) == 7 and all(isinstance(d["page_content"], str) for d in docs)


def test_placeholder_rule_names_the_bracketed_placeholders():
    assert "[Provider NPI]" in PLACEHOLDER_RULE
    assert "[Health System Name]" in PLACEHOLDER_RULE
    assert "not clinical claims" in PLACEHOLDER_RULE


def test_builder_literals_match_the_generation_prompt_sql():
    """Drift guard: every fixed literal the builder renders must appear in pipeline/30_generate_appeals.sql."""
    sql = GEN_SQL.read_text()
    literals = [
        r"CLAIM:\n- Patient: ", ", DOB ", ", Sex ", r"- Payer: ", ", Member ID ", "'[Member ID]'",
        ", Claim ", r"- Date of Service: ", ", POS ", r"- Procedures (CPT/HCPCS): ", "  Modifiers: ",
        "'(none)'", r"- Diagnoses (ICD-10): ", r"- Total charges: $", r"- Provider: ",
        "APPLICABLE MEDICAL-NECESSITY CRITERIA (", r"):\n- ",
        "MPFS CODING CONTEXT (cite only if relevant to the denial):", "'(n/a)'",
        "CLINICAL DOCUMENTATION - DATED NOTES (chronological; cite by bracket label):", "'(no notes)'",
        "CLINICAL DIGEST (orientation only; cite the dated notes, not this summary):",
        "'2. Denial ", ". The appeal must prove: ",
        "Never invent facts, dates, scores, member IDs or provider identifiers.",
        "If a field is unknown, say unknown or use a bracketed placeholder.",
        "Use bracketed placeholders like [Provider NPI] for any field not supplied.",
        "[Health System Name]",
    ]
    missing = [lit for lit in literals if lit not in sql]
    assert not missing, f"not found in 30_generate_appeals.sql: {missing}"


# ---- determination + cost + rate ------------------------------------------------------------------------

@pytest.mark.parametrize("pred,exp,ok", [
    ("WARRANTED", "WARRANTED", True),
    (" warranted ", "WARRANTED", True),
    ("NEEDS REVIEW", "WARRANTED", False),
    ("NOT WARRANTED", "NOT WARRANTED", True),
    ("", "NEEDS REVIEW", False),
    (None, "NEEDS REVIEW", False),
    ("NEEDS REVIEW", None, False),
])
def test_determination_matches(pred, exp, ok):
    assert determination_matches(pred, exp) is ok


def test_cost_estimate_arithmetic():
    est = estimate_judge_cost([4000, 4000], judge_calls_per_row=2, in_usd_per_m=3.0, out_usd_per_m=15.0,
                              out_tokens_per_call=400)
    assert est["judge_calls"] == 4
    assert est["est_input_tokens"] == 4 * 1700
    assert est["est_output_tokens"] == 4 * 400
    expected = (4 * 1700 / 1e6) * 3.0 + (4 * 400 / 1e6) * 15.0
    assert est["est_cost_usd"] == pytest.approx(round(expected, 4))


def test_cost_estimate_empty():
    assert estimate_judge_cost([], 2, 3.0, 15.0)["est_cost_usd"] == 0.0


def test_rate_handles_zero_denominator():
    assert rate(0, 0) is None
    assert rate(3, 4) == 0.75
