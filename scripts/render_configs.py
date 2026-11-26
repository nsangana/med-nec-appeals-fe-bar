#!/usr/bin/env python3
"""Render the exported dashboard and Genie JSON for one catalog.schema.

Bundle variables are not substituted inside the exported JSON, so this script rewrites the source catalog and
schema (appeals_hackathon_catalog.fe_bar_appeals) in:
  - dashboards/appeals_automation_agent_insights.lvdash.json: the per-dataset "catalog" and "schema" keys,
    and any dotted catalog.schema reference;
  - genie/appeals_metrics.geniespace.json: dotted catalog.schema references (serialized_space).
Bytes are copied as-is apart from those replacements, so with the source names the output is byte-identical.

Usage:
  scripts/render_configs.py --catalog C --schema S --out build/<target>/
"""
import argparse
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
SOURCE_CATALOG = "appeals_hackathon_catalog"
SOURCE_SCHEMA = "fe_bar_appeals"
SOURCES = [
    REPO / "dashboards" / "appeals_automation_agent_insights.lvdash.json",
    REPO / "genie" / "appeals_metrics.geniespace.json",
]
IDENT = re.compile(r"^[A-Za-z0-9_]+$")


def render(text: str, catalog: str, schema: str) -> str:
    dotted = re.compile(rf"(?<![A-Za-z0-9_]){SOURCE_CATALOG}\.{SOURCE_SCHEMA}(?![A-Za-z0-9_])")
    text = dotted.sub(f"{catalog}.{schema}", text)
    text = re.sub(rf'("catalog"\s*:\s*)"{SOURCE_CATALOG}"', lambda m: f'{m.group(1)}"{catalog}"', text)
    text = re.sub(rf'("schema"\s*:\s*)"{SOURCE_SCHEMA}"', lambda m: f'{m.group(1)}"{schema}"', text)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--schema", required=True)
    ap.add_argument("--out", required=True, help="output directory (created if missing)")
    args = ap.parse_args()
    if not IDENT.match(args.catalog) or not IDENT.match(args.schema):
        print("catalog and schema must match [A-Za-z0-9_]+", file=sys.stderr)
        return 2
    out_dir = pathlib.Path(args.out)
    if not out_dir.is_absolute():
        out_dir = REPO / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    for src in SOURCES:
        text = src.read_bytes().decode("utf-8")
        rendered = render(text, args.catalog, args.schema)
        leftover = []
        if args.catalog != SOURCE_CATALOG and f'"{SOURCE_CATALOG}"' in rendered:
            leftover.append("catalog")
        if args.schema != SOURCE_SCHEMA and f'"{SOURCE_SCHEMA}"' in rendered:
            leftover.append("schema")
        if leftover:
            print(f"{src.name}: source {' and '.join(leftover)} still referenced after render", file=sys.stderr)
            return 1
        dst = out_dir / src.name
        dst.write_bytes(rendered.encode("utf-8"))
        print(f"rendered {dst.relative_to(REPO) if dst.is_relative_to(REPO) else dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
