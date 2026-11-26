"""Parser for the appeal-generation response. Mirrors pipeline/30_generate_appeals.sql exactly.

The SQL is the production path; this module exists so the parse/normalise rules can be unit-tested without a
warehouse, and so any drift between the two is caught by the tests (genai/test_appeal_parser.py).

Rules (same as the SQL):
- Four sections with literal delimiters; text before the first delimiter is ignored.
- Each section ends at the next delimiter, or at end of text if the next one is missing.
- DETERMINATION: first non-empty line, upper-cased, reduced to A-Z and single spaces, must equal exactly
  WARRANTED, NOT WARRANTED or NEEDS REVIEW. Anything else is a parse failure.
- Parse failure (determination invalid, cheat sheet missing/empty, or WARRANTED without a letter) routes the
  encounter to NEEDS REVIEW with a reason starting "PARSE_FAILURE:". Nothing is defaulted to WARRANTED.
- NEEDS REVIEW and NOT WARRANTED never carry an appeal letter.
"""
import re

VALID = ("WARRANTED", "NOT WARRANTED", "NEEDS REVIEW")

_DET = re.compile(r"===DETERMINATION===\s*(.*?)\s*(?:===CHEAT_SHEET===|$)", re.DOTALL)
_CHEAT = re.compile(r"===CHEAT_SHEET===\s*(.*?)\s*(?:===APPEAL_LETTER===|===NEEDS_REVIEW_REASON===|$)", re.DOTALL)
_LETTER = re.compile(r"===APPEAL_LETTER===\s*(.*?)\s*(?:===NEEDS_REVIEW_REASON===|$)", re.DOTALL)
_REASON = re.compile(r"===NEEDS_REVIEW_REASON===\s*(.*)$", re.DOTALL)
_FIRST_LINE = re.compile(r"^\s*([^\r\n]+)", re.DOTALL)


def _section(pattern, text):
    m = pattern.search(text or "")
    return m.group(1) if m else ""


def _normalise_determination(det_block):
    line = _section(_FIRST_LINE, det_block)
    s = re.sub(r"[^A-Z ]", "", line.strip().upper())
    return re.sub(r" +", " ", s).strip()


def parse_response(text):
    """Parse one model response. Returns a dict with the columns written to appeals_output."""
    det_block = _section(_DET, text)
    cheat_block = _section(_CHEAT, text)
    letter_block = _section(_LETTER, text)
    reason_block = _section(_REASON, text)

    det_norm = _normalise_determination(det_block)
    det_valid = det_norm if det_norm in VALID else None
    letter_ok = len(letter_block.strip()) > 0 and not letter_block.startswith("(No appeal letter")
    cheat_ok = len(cheat_block.strip()) > 0

    problem = None
    if det_valid is None:
        problem = ('determination not one of WARRANTED / NOT WARRANTED / NEEDS REVIEW '
                   f'(model wrote: "{det_block.strip()[:80]}")')
    elif not cheat_ok:
        problem = "AI reasoning worksheet section missing"
    elif det_valid == "WARRANTED" and not letter_ok:
        problem = "WARRANTED without an appeal letter"

    if problem is not None:
        recommendation = "NEEDS REVIEW"
        reason = ("PARSE_FAILURE: " + problem
                  + ". Routed to NEEDS REVIEW by the pipeline; reviewer to check raw_response.")
    else:
        recommendation = det_valid
        if det_valid == "NEEDS REVIEW":
            reason = reason_block.strip() or "NEEDS REVIEW (model gave no reason)"
        else:
            reason = None

    return {
        "recommendation": recommendation,
        "needs_review_reason": reason,
        "cheat_sheet": cheat_block.strip() or None,
        "appeal_letter": (letter_block.strip() or None) if recommendation == "WARRANTED" else None,
        "parse_failure": problem is not None,
        "parse_problem": problem,
        "determination_raw": det_norm,
    }
