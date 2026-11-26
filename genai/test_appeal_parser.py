"""Unit tests for appeal_parser.parse_response (mirrors pipeline/30_generate_appeals.sql parse logic)."""
from appeal_parser import parse_response

CHEAT = "AI REASONING WORKSHEET\n- Evidence mapping: [2026-03-14 PT_VISIT] 12 PT sessions documented failure."
LETTER = "RE: Patient [Member ID], DOS 2026-01-08.\n\nDear Medical Director, the documented course supports coverage."


def resp(det, cheat=CHEAT, letter="", reason=""):
    return (f"===DETERMINATION===\n{det}\n===CHEAT_SHEET===\n{cheat}\n"
            f"===APPEAL_LETTER===\n{letter}\n===NEEDS_REVIEW_REASON===\n{reason}")


def test_good_warranted_has_letter_and_worksheet():
    out = parse_response(resp("WARRANTED", letter=LETTER, reason="N/A"))
    assert out["recommendation"] == "WARRANTED"
    assert out["parse_failure"] is False
    assert out["needs_review_reason"] is None
    assert out["appeal_letter"].startswith("RE: Patient")
    assert "[2026-03-14 PT_VISIT]" in out["cheat_sheet"]


def test_good_not_warranted_has_no_letter_even_if_model_wrote_one():
    out = parse_response(resp("NOT WARRANTED", letter="(No appeal letter - not warranted.)"))
    assert out["recommendation"] == "NOT WARRANTED"
    assert out["appeal_letter"] is None
    assert out["needs_review_reason"] is None
    assert out["parse_failure"] is False


def test_good_needs_review_lists_missing_documentation_and_no_letter():
    reason = "- No dated conservative-treatment record before 2026-02-01\n- No imaging report"
    out = parse_response(resp("NEEDS REVIEW", letter="(No appeal letter - needs review.)", reason=reason))
    assert out["recommendation"] == "NEEDS REVIEW"
    assert out["needs_review_reason"] == reason
    assert out["appeal_letter"] is None
    assert out["parse_failure"] is False


def test_malformed_no_delimiters_is_parse_failure_routed_to_needs_review():
    out = parse_response("I think this is warranted because the notes are good.")
    assert out["recommendation"] == "NEEDS REVIEW"
    assert out["parse_failure"] is True
    assert out["needs_review_reason"].startswith("PARSE_FAILURE:")
    assert out["appeal_letter"] is None


def test_malformed_template_echo_is_not_accepted_as_a_determination():
    out = parse_response(resp("WARRANTED or NOT WARRANTED", letter=LETTER))
    assert out["recommendation"] == "NEEDS REVIEW"
    assert out["parse_failure"] is True
    assert "not one of" in out["needs_review_reason"]


def test_missing_worksheet_section_is_parse_failure():
    out = parse_response(resp("NOT WARRANTED", cheat="", letter="(No appeal letter - not warranted.)"))
    assert out["recommendation"] == "NEEDS REVIEW"
    assert "worksheet section missing" in out["needs_review_reason"]


def test_missing_letter_for_warranted_is_parse_failure_not_silent_warranted():
    out = parse_response(resp("WARRANTED", letter="(No appeal letter - not warranted.)"))
    assert out["recommendation"] == "NEEDS REVIEW"
    assert out["parse_failure"] is True
    assert "WARRANTED without an appeal letter" in out["needs_review_reason"]
    assert out["appeal_letter"] is None


def test_missing_trailing_sections_still_parse_when_warranted_letter_is_last():
    text = ("===DETERMINATION===\nWARRANTED\n===CHEAT_SHEET===\n" + CHEAT +
            "\n===APPEAL_LETTER===\n" + LETTER)  # no NEEDS_REVIEW_REASON section at all
    out = parse_response(text)
    assert out["recommendation"] == "WARRANTED"
    assert out["appeal_letter"].endswith("supports coverage.")


def test_lowercase_determination_is_normalised():
    out = parse_response(resp("warranted", letter=LETTER))
    assert out["recommendation"] == "WARRANTED"
    assert out["determination_raw"] == "WARRANTED"


def test_lowercase_not_warranted_is_not_read_as_warranted():
    out = parse_response(resp("not warranted", letter="(No appeal letter - not warranted.)"))
    assert out["recommendation"] == "NOT WARRANTED"


def test_extra_text_before_first_delimiter_is_ignored():
    text = "Sure! Here is the analysis.\n\n" + resp("WARRANTED", letter=LETTER)
    out = parse_response(text)
    assert out["recommendation"] == "WARRANTED"
    assert out["parse_failure"] is False


def test_punctuation_and_markdown_bold_on_determination_line_are_tolerated():
    out = parse_response(resp("**NOT WARRANTED.**", letter="(No appeal letter - not warranted.)"))
    assert out["recommendation"] == "NOT WARRANTED"


def test_extra_explanation_on_determination_line_is_flagged_not_guessed():
    # The prompt asks for one line only. Anything else on that line is a parse failure, by design.
    out = parse_response(resp("WARRANTED - strong evidence", letter=LETTER))
    assert out["recommendation"] == "NEEDS REVIEW"
    assert out["parse_failure"] is True


def test_needs_review_with_blank_reason_gets_fallback_text():
    out = parse_response(resp("NEEDS REVIEW", letter="(No appeal letter - needs review.)", reason="   "))
    assert out["recommendation"] == "NEEDS REVIEW"
    assert out["needs_review_reason"] == "NEEDS REVIEW (model gave no reason)"
