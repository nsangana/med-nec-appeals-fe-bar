"""Local CLI: python -m generator --seed 20261124 --n 500 --as-of 2026-11-24 --out /tmp/febar_out

Writes claims/, clinical_notes/, _manifests/ and prints a summary. Labels are printed to stdout as JSON
(they are never written to the landing area). The notebook pipeline/10_generate_raw_data.py is the
production path; this CLI exists for local checks.
"""
import argparse
import json
from datetime import date

from . import DEFAULT_N_ENCOUNTERS, DEFAULT_SEED, generate, write_landing


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--n", type=int, default=DEFAULT_N_ENCOUNTERS)
    ap.add_argument("--as-of", default=None, help="YYYY-MM-DD (default: today)")
    ap.add_argument("--out", required=True, help="landing root directory")
    ns = ap.parse_args(argv)
    as_of = date.fromisoformat(ns.as_of) if ns.as_of else None
    batch = generate(seed=ns.seed, n_encounters=ns.n, as_of_date=as_of)
    res = write_landing(batch, ns.out)
    print(json.dumps({"landing": res, "label_counts": batch.manifest["label_counts"],
                      "defects": len(batch.manifest["defects"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
