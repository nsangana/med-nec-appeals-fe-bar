#!/usr/bin/env python3
"""Run SQL on the FE Bar warehouse via the Statement Execution API (Databricks CLI auth).

Usage:
  tools/run_sql.py "SELECT ... WHERE x = :x" --param x=value   # named parameter markers, never interpolation
  tools/run_sql.py -f path/to/file.sql                          # runs ';'-separated statements in order
Prints results as a markdown table (good for pasting into evidence/*.md).
"""
import argparse, json, os, subprocess, sys, time

PROFILE = os.environ.get("FEBAR_PROFILE", "fevm-appeals-hackathon")
WAREHOUSE = os.environ.get("FEBAR_WAREHOUSE", "559faf81d610a2a1")
os.environ.setdefault("DATABRICKS_AUTH_STORAGE", "plaintext")


def api(method, path, body=None):
    cmd = ["databricks", "--profile", PROFILE, "api", method, path]
    if body is not None:
        cmd += ["--json", json.dumps(body)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip())
    return json.loads(r.stdout or "{}")


def split_sql(text):
    """Split on ';' outside quotes/comments."""
    out, buf, q, i = [], [], None, 0
    while i < len(text):
        c = text[i]
        if q is None and text.startswith("--", i):
            j = text.find("\n", i); j = len(text) if j < 0 else j
            buf.append(text[i:j]); i = j; continue
        if q:
            if c == q:
                q = None
        elif c in ("'", '"', "`"):
            q = c
        elif c == ";":
            s = "".join(buf).strip()
            if s and not all(l.strip().startswith("--") or not l.strip() for l in s.splitlines()):
                out.append(s)
            buf = []; i += 1; continue
        buf.append(c); i += 1
    s = "".join(buf).strip()
    if s and not all(l.strip().startswith("--") or not l.strip() for l in s.splitlines()):
        out.append(s)
    return out


def run(stmt, params=None, max_rows=200):
    body = {"warehouse_id": WAREHOUSE, "statement": stmt, "wait_timeout": "50s",
            "on_wait_timeout": "CONTINUE", "format": "JSON_ARRAY", "disposition": "INLINE"}
    if params:
        body["parameters"] = [{"name": k, "value": v} for k, v in params.items()]
    d = api("post", "/api/2.0/sql/statements", body)
    while d.get("status", {}).get("state") in ("PENDING", "RUNNING"):
        time.sleep(3)
        d = api("get", f"/api/2.0/sql/statements/{d['statement_id']}")
    st = d.get("status", {})
    if st.get("state") != "SUCCEEDED":
        raise RuntimeError(f"{st.get('state')}: {st.get('error', {}).get('message', '')}")
    cols = [c["name"] for c in d.get("manifest", {}).get("schema", {}).get("columns", [])]
    rows = d.get("result", {}).get("data_array", []) or []
    return cols, rows[:max_rows]


def md(cols, rows):
    if not cols:
        return "(ok)"
    esc = lambda v: "NULL" if v is None else str(v).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(esc(v) for v in r) + " |" for r in rows]
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sql", nargs="?")
    ap.add_argument("-f", "--file")
    ap.add_argument("--param", action="append", default=[], help="name=value (named parameter marker :name)")
    ap.add_argument("--max-rows", type=int, default=200)
    a = ap.parse_args()
    params = dict(p.split("=", 1) for p in a.param)
    stmts = split_sql(open(a.file).read()) if a.file else [a.sql]
    for s in stmts:
        try:
            cols, rows = run(s, params or None, a.max_rows)
        except Exception as e:
            print(f"-- FAILED: {s[:120]}\n{e}", file=sys.stderr); sys.exit(1)
        if len(stmts) > 1:
            print(f"-- {s.splitlines()[0][:100]}")
        print(md(cols, rows)); print()
