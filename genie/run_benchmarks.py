#!/usr/bin/env python3
"""Run the FE Bar Genie benchmarks through the Genie Conversation API and grade them.

Usage: python3 genie/run_benchmarks.py [--space SPACE_ID]  -> writes evidence/07_genie.md

Grading (value containment, rounded so 12345.6 matches 12345.60):
  * the Genie run must reach COMPLETED with a query attachment and a result;
  * if the expected SQL returns rows, every non-NULL expected cell value must appear in the Genie result;
  * if the expected SQL returns no rows, the Genie result must also be empty (or have no rows).
Expected SQL runs on the same warehouse via tools/run_sql.py, so both sides see the same data snapshot.
"""
import argparse, json, os, pathlib, subprocess, sys, time, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_sql  # noqa: E402  (same warehouse + profile as the rest of the build)

PROFILE = "fevm-appeals-hackathon"
SPACE_DEFAULT = "01f1e7ec913217158b231c3e2f18fa20"
os.environ.setdefault("DATABRICKS_AUTH_STORAGE", "plaintext")


def cli(*args):
    r = subprocess.run(["databricks", "--profile", PROFILE, *args], capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip())
    return json.loads(r.stdout or "{}")


def norm(v):
    if v is None:
        return "NULL"
    s = str(v).strip()
    try:
        return f"{round(float(s), 2):.2f}"
    except ValueError:
        return s


def cells(cols_rows):
    _, rows = cols_rows
    return {norm(v) for r in rows for v in r}


def genie_ask(space, question, poll_s=4, max_wait_s=300):
    start = cli("genie", "start-conversation", "--no-wait", space, question)
    conv, msg = start["conversation_id"], start["message_id"]
    t0 = time.time()
    while True:
        m = cli("genie", "get-message", space, conv, msg)
        if m.get("status") in ("COMPLETED", "FAILED", "CANCELLED"):
            break
        if time.time() - t0 > max_wait_s:
            m["status"] = "TIMEOUT"
            break
        time.sleep(poll_s)
    out = {"status": m.get("status"), "error": (m.get("error") or {}).get("error"), "sql": None,
           "text": None, "columns": [], "rows": [], "conversation_id": conv, "message_id": msg}
    for a in m.get("attachments") or []:
        if a.get("query") and out["sql"] is None:
            out["sql"] = a["query"].get("query")
            att = a.get("attachment_id")
            try:
                res = cli("genie", "get-message-attachment-query-result", space, conv, msg, att)
                st = res.get("statement_response", {})
                out["columns"] = [c["name"] for c in st.get("manifest", {}).get("schema", {}).get("columns", [])]
                out["rows"] = st.get("result", {}).get("data_array", []) or []
            except RuntimeError as e:
                out["error"] = (out["error"] or "") + f" | result fetch: {e}"
        if a.get("text") and out["text"] is None:
            out["text"] = a["text"].get("content")
    return out


def md_table(cols, rows, limit=6):
    if not cols:
        return "(no rows)"
    esc = lambda v: "NULL" if v is None else str(v).replace("|", "\\|").replace("\n", " ")[:120]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(esc(v) for v in r) + " |" for r in rows[:limit]]
    if len(rows) > limit:
        lines.append(f"| ... {len(rows) - limit} more rows |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--space", default=SPACE_DEFAULT)
    ap.add_argument("--only", default=None, help="comma-separated benchmark ids")
    ap.add_argument("--out", default=str(ROOT / "evidence" / "07_genie.md"))
    a = ap.parse_args()
    bench = json.loads((ROOT / "genie" / "benchmarks.json").read_text())
    if a.only:
        keep = set(a.only.split(","))
        bench = [b for b in bench if b["id"] in keep]

    appeals_rows = run_sql.run("SELECT count(*) FROM appeals_hackathon_catalog.fe_bar_appeals.appeals_output", None, 1)[1][0][0]
    appeals_rows = int(appeals_rows)
    results = []
    for b in bench:
        g = genie_ask(a.space, b["question"])
        exp_cols, exp_rows = run_sql.run(b["expected_sql"], None, 500)
        exp = (exp_cols, exp_rows)
        g_cells = cells((g["columns"], g["rows"]))
        exp_cells = cells(exp)
        if g["status"] != "COMPLETED" or g["sql"] is None:
            ok, why = False, f"Genie status={g['status']} error={g['error']}"
        elif not exp_rows:
            ok = len(g["rows"]) == 0
            why = "expected empty; Genie " + ("empty" if ok else f"returned {len(g['rows'])} rows")
        else:
            # NULL / blank expected cells (e.g. a payer with no open warranted appeals) need not be echoed by Genie
            missing = sorted((exp_cells - {"NULL", ""}) - g_cells)
            ok = not missing
            why = "all expected values present" if ok else f"missing expected values: {missing[:8]}"
        pending = (not ok) and b.get("needs_appeals") and appeals_rows == 0
        if pending:
            why = "PENDING_DATA: appeals_output has 0 rows, so the answer is empty/NULL (" + why + ")"
        results.append({"b": b, "g": g, "exp": exp, "ok": ok, "why": why, "pending": pending})
        tag = "PENDING_DATA" if pending else ("PASS" if ok else "FAIL")
        print(f"{b['id']} {tag} :: {why}", flush=True)

    graded = [r for r in results if not r["pending"]]
    passed = sum(r["ok"] for r in graded)
    lines = [
        "# 07 Genie benchmarks (FE Bar – Medical Necessity Appeals)",
        "",
        f"- Space: `{a.space}` (default workspace permissions; not shared)",
        f"- Run at: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC (Genie Conversation API via CLI profile `{PROFILE}`)",
        f"- appeals_output rows at run: {appeals_rows}",
        f"- Pass rate: **{passed}/{len(graded)}** graded; PENDING_DATA: {len(results) - len(graded)} (need generated appeals)",
        "- Grading: Genie query COMPLETED with SQL; expected SQL (run on the same warehouse) values all present in Genie's result rows; empty expected => empty Genie result.",
        "- Expected SQL is in `genie/benchmarks.json`. Results are real (not simulated).",
        "",
        "| ID | Question | Result | Genie SQL (first 200 chars) | Note |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        sql = (r["g"]["sql"] or "").replace("\n", " ").replace("|", "\\|")[:200]
        tag = 'PENDING_DATA' if r['pending'] else ('PASS' if r['ok'] else 'FAIL')
        lines.append(f"| {r['b']['id']} | {r['b']['question']} | {tag} | `{sql}` | {r['why']} |")
    lines.append("")
    role_order = ["VP Revenue Cycle", "CDAIO", "CFO", "Director of Denial Management", "General analyst"]
    results.sort(key=lambda r: (role_order.index(r["b"].get("role", "General analyst")), r["b"]["id"]))
    # role summary
    lines += ["", "## Pass rate by stakeholder role", "", "| Role | Pass | Benchmarks |", "|---|---|---|"]
    for role in role_order:
        rr = [r for r in results if r["b"].get("role", "General analyst") == role and not r["pending"]]
        if rr:
            lines.append(f"| {role} | {sum(r['ok'] for r in rr)}/{len(rr)} | {', '.join(r['b']['id'] for r in rr)} |")
    lines.append("")
    last_role = None
    for r in results:
        role = r["b"].get("role", "General analyst")
        if role != last_role:
            lines += [f"# Role: {role}", ""]
            last_role = role
        lines += [
            f"## {r['b']['id']}: {r['b']['question']}",
            f"- Result: **{'PENDING_DATA' if r['pending'] else ('PASS' if r['ok'] else 'FAIL')}** ({r['why']})",
            f"- Genie status: {r['g']['status']}, conversation `{r['g']['conversation_id']}`",
            "",
            "Genie SQL:",
            "```sql",
            r["g"]["sql"] or "(none)",
            "```",
            "Genie result (snippet):",
            "",
            md_table(r["g"]["columns"], r["g"]["rows"]),
            "",
            "Expected SQL:",
            "```sql",
            r["b"]["expected_sql"],
            "```",
            "Expected result (snippet):",
            "",
            md_table(r["exp"][0], r["exp"][1]),
            "",
        ]
        if r["g"]["text"]:
            lines += [f"Genie text: {r['g']['text'][:300]}", ""]
    pathlib.Path(a.out).write_text("\n".join(lines) + "\n")
    print(f"pass rate {passed}/{len(graded)} graded, pending {len(results)-len(graded)} -> {a.out}")


if __name__ == "__main__":
    main()
