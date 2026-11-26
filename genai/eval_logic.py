"""Pure-Python logic for the MLflow GenAI evaluation (pipeline/65_genai_evaluate.py).

No MLflow / Spark imports here on purpose: these functions are unit-tested in genai/test_eval_logic.py.

- generation_blocks: the grounding the generator saw, rendered with the SAME field order and wording as the
  prompt in pipeline/30_generate_appeals.sql (CLAIM, criteria, MPFS, dated notes, digest, denial line, and the
  placeholder rule). test_eval_logic.py checks every literal against the SQL file so the two cannot drift.
- build_grounding_docs: those blocks as retrieval chunks for the groundedness judge.
- quote_check: same definition as pipeline/60_evaluate.py (strict = verbatim after whitespace normalisation,
  normalised = punctuation/case-insensitive, ellipsis-split). Metric only; never changes a determination.
- determination_matches: exact label comparison after normalising case/whitespace.
- estimate_judge_cost: token-count based cost estimate printed before any judge call is made.
"""
import re

CLASSES = ("WARRANTED", "NOT WARRANTED", "NEEDS REVIEW")

# Same single-line double-quote rule as 60_evaluate.py.
QUOTE_RE = re.compile(r'"([^"\n]{20,})"')

# Grounding columns used by the quote metric: the exact field set 60_evaluate.py uses, minus patient_name.
# (The quote metric is a copying measure and is kept on 60_evaluate's definition; only the judge context changed.)
GROUNDING_FIELDS = (
    "criteria_block", "notes_full", "mpfs_context", "reason_text", "what_to_prove",
    "hcpcs_codes", "dx_codes", "payer_name",
)

# Verbatim rule text from the generation prompt (pipeline/30_generate_appeals.sql). Shown to the groundedness
# judge so it knows bracketed placeholders are instructed template fields, not claims.
PLACEHOLDER_RULE = (
    "GENERATION RULES (the generator was instructed with these rules): Never invent facts, dates, scores, member IDs "
    "or provider identifiers. If a field is unknown, say unknown or use a bracketed placeholder. Use bracketed "
    "placeholders like [Provider NPI] for any field not supplied. The health system is written as the placeholder "
    "[Health System Name]. Bracketed placeholders are allowed in the output and are not clinical claims."
)


def _s(v):
    """SQL-style string of a value: NULL -> '' (the prompt's coalesce(x, '') behaviour)."""
    if v is None:
        return ""
    return str(v)


def _or(v, default):
    """coalesce(v, default) for the prompt fields that carry a fallback literal."""
    return default if v is None else str(v)


def generation_blocks(row):
    """Render the generator's grounding blocks from an encounter_grounding row (mapping of column -> value).

    Wording and field order mirror pipeline/30_generate_appeals.sql. Keys: claim, criteria, mpfs, notes, digest,
    denial, rules. `patient_name` is included because the generator's CLAIM block included it.
    """
    claim = (
        "CLAIM:\n"
        f"- Patient: {_s(row.get('patient_name'))}, DOB {_s(row.get('dob'))}, Sex {_s(row.get('sex'))}\n"
        f"- Payer: {_s(row.get('payer_name'))}, Member ID {_or(row.get('member_id'), '[Member ID]')}, "
        f"Claim {_s(row.get('claim_number'))}\n"
        f"- Date of Service: {_s(row.get('dos'))}, POS {_s(row.get('pos'))}\n"
        f"- Procedures (CPT/HCPCS): {_s(row.get('hcpcs_codes'))}  Modifiers: {_or(row.get('modifiers'), '(none)')}\n"
        f"- Diagnoses (ICD-10): {_s(row.get('dx_codes'))}\n- Total charges: ${_s(row.get('total_charges'))}\n"
        f"- Provider: {_s(row.get('provider_name'))}\n\n"
    )
    criteria = (
        f"APPLICABLE MEDICAL-NECESSITY CRITERIA ({_s(row.get('criteria_payer'))}):\n"
        f"- {_s(row.get('criteria_block'))}\n\n"
    )
    mpfs = f"MPFS CODING CONTEXT (cite only if relevant to the denial):\n{_or(row.get('mpfs_context'), '(n/a)')}\n\n"
    notes = (
        "CLINICAL DOCUMENTATION - DATED NOTES (chronological; cite by bracket label):\n"
        f"{_or(row.get('notes_full'), '(no notes)')}\n\n"
    )
    digest = (
        "CLINICAL DIGEST (orientation only; cite the dated notes, not this summary):\n"
        f"{_s(row.get('clinical_digest'))}\n\n"
    )
    denial = (
        f"2. Denial {_s(row.get('denial_code'))} - {_s(row.get('reason_text'))}. "
        f"The appeal must prove: {_s(row.get('what_to_prove'))}.\n"
    )
    return {"claim": claim, "criteria": criteria, "mpfs": mpfs, "notes": notes,
            "digest": digest, "denial": denial, "rules": PLACEHOLDER_RULE}


def build_grounding_docs(row):
    """Retrieval chunks for the groundedness judge: the generator's blocks, one chunk each."""
    b = generation_blocks(row)
    return [
        {"page_content": b["claim"].rstrip(), "metadata": {"doc_uri": "claim"}},
        {"page_content": b["denial"].rstrip(), "metadata": {"doc_uri": "denial"}},
        {"page_content": b["criteria"].rstrip(), "metadata": {"doc_uri": "criteria"}},
        {"page_content": b["notes"].rstrip(), "metadata": {"doc_uri": "clinical_notes"}},
        {"page_content": b["digest"].rstrip(), "metadata": {"doc_uri": "clinical_digest"}},
        {"page_content": b["mpfs"].rstrip(), "metadata": {"doc_uri": "mpfs"}},
        {"page_content": b["rules"], "metadata": {"doc_uri": "generation_rules"}},
    ]


def norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def alnum(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def quote_check(text, grounding):
    """Quoted spans (>= 20 chars, one line, double quotes) in `text` checked against `grounding`.

    Returns {"total": int, "strict": int, "normalised": int}.
    """
    ground = norm(grounding)
    raw = [m for m in QUOTE_RE.findall(text or "") if len(norm(m)) >= 20]
    strict = sum(1 for m in raw if norm(m) in ground)
    ground_al = alnum(ground)
    normalised = 0
    for m in raw:
        frags = [f for f in re.split(r"\.\.\.|…", m) if len(alnum(f)) >= 12]
        if frags and all(alnum(f) in ground_al for f in frags):
            normalised += 1
    return {"total": len(raw), "strict": strict, "normalised": normalised}


def quote_text(letter, cheat_sheet):
    """Text that quote_check scans: letter then worksheet, exactly as 60_evaluate does."""
    return (letter or "") + "\n" + (cheat_sheet or "")


def grounding_text(row):
    """Flat grounding string for the quote scorer: the exact field set 60_evaluate.py uses, minus patient_name.

    Kept identical to 60_evaluate so the strict / normalised rates are comparable with evidence/11_eval_180.md.
    """
    return norm(" ".join(str(row.get(k) or "") for k in GROUNDING_FIELDS))


def determination_matches(predicted, expected):
    """True when the model's determination equals the designed label (labels are eval-only)."""
    def canon(x):
        return norm(str(x or "")).upper()
    return canon(predicted) != "" and canon(predicted) == canon(expected)


def estimate_judge_cost(char_counts, judge_calls_per_row, in_usd_per_m, out_usd_per_m,
                        out_tokens_per_call=400, prompt_overhead_tokens=700, chars_per_token=4.0):
    """Estimate judge cost from character counts (chars/4 is a conservative token proxy for English text).

    char_counts: one int per row = grounding chars + response chars (the judge sees both).
    Returns a dict with per-row and total numbers so the notebook can print the basis.
    """
    in_tokens_per_call = [c / chars_per_token + prompt_overhead_tokens for c in char_counts]
    total_in = sum(in_tokens_per_call) * judge_calls_per_row
    total_out = len(char_counts) * judge_calls_per_row * out_tokens_per_call
    cost = total_in / 1e6 * in_usd_per_m + total_out / 1e6 * out_usd_per_m
    per_row = cost / len(char_counts) if char_counts else 0.0
    return {
        "rows": len(char_counts),
        "judge_calls": len(char_counts) * judge_calls_per_row,
        "est_input_tokens": int(total_in),
        "est_output_tokens": int(total_out),
        "est_cost_usd": round(cost, 4),
        "est_cost_per_row_usd": round(per_row, 5),
    }


def rate(numer, denom):
    return round(numer / denom, 4) if denom else None
