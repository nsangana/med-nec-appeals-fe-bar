"""Static guard: every pipeline/sdp/genie SQL file must have balanced single quotes outside comments.

Regression for 2026-11-25: an apostrophe ("health system's") inside an ai_query prompt literal in
pipeline/30_generate_appeals.sql ended the string early and failed the generate_appeals job task.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SQL_FILES = sorted(p for d in ("pipeline", "sdp", "genie", "governance") for p in (ROOT / d).glob("*.sql"))


def _strip_comments(sql: str) -> str:
    out, i, in_str = [], 0, False
    while i < len(sql):
        c = sql[i]
        if not in_str and sql.startswith("--", i):
            j = sql.find("\n", i)
            i = len(sql) if j < 0 else j
            continue
        if c == "'":
            if in_str and sql.startswith("''", i):  # escaped quote inside a literal
                out.append("''"); i += 2; continue
            in_str = not in_str
        out.append(c); i += 1
    return "".join(out)


def test_sql_files_found():
    assert SQL_FILES, "no SQL files discovered"


def test_single_quotes_balanced():
    bad = []
    for p in SQL_FILES:
        body = _strip_comments(p.read_text())
        body = body.replace("''", "")  # escaped quotes
        body = re.sub(r"\\'", "", body)  # backslash-escaped quotes
        if body.count("'") % 2:
            bad.append(str(p.relative_to(ROOT)))
    assert not bad, f"unbalanced single quotes in: {bad}"
