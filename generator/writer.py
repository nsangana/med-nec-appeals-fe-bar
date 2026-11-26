"""Write one generator batch to the landing area as JSON lines (idempotent per seed + as_of).

Layout under `landing_root` (the UC volume `landing`):
  claims/<batch>.json            claim-line records (Auto Loader source)
  clinical_notes/<batch>.json    clinical-note records (Auto Loader source)
  _manifests/<batch>.json        internal manifest (defects, per-encounter plan). Not an Auto Loader source.
  _staging/                      temp files; renamed into place so readers never see partial files

<batch> = batch_<as_of>_seed<seed>_n<n>. Commit order: notes -> manifest -> claims. The claims file is the
commit marker: if it exists the batch is considered landed and the whole call is a no-op.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict

from .core import Batch


def _write_jsonl(path: str, records) -> None:
    tmp = os.path.join(os.path.dirname(path).replace(os.sep + "claims", os.sep + "_staging")
                       .replace(os.sep + "clinical_notes", os.sep + "_staging"), "_part_" + os.path.basename(path))
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, separators=(",", ":"), sort_keys=False))
            fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def write_landing(batch: Batch, landing_root: str) -> Dict[str, Any]:
    """Land a batch. Returns a status dict; status is 'landed' or 'skipped_exists'."""
    name = batch.source_batch + ".json"
    claims_path = os.path.join(landing_root, "claims", name)
    notes_path = os.path.join(landing_root, "clinical_notes", name)
    manifest_path = os.path.join(landing_root, "_manifests", name)
    result = {"source_batch": batch.source_batch, "claims_file": claims_path, "notes_file": notes_path,
              "manifest_file": manifest_path, "n_claims": len(batch.claims), "n_notes": len(batch.notes)}
    if os.path.exists(claims_path):
        result["status"] = "skipped_exists"
        return result
    for d in ("claims", "clinical_notes", "_manifests", "_staging"):
        os.makedirs(os.path.join(landing_root, d), exist_ok=True)
    _write_jsonl(notes_path, batch.notes)
    _write_jsonl(manifest_path, [batch.manifest])
    _write_jsonl(claims_path, batch.claims)  # commit marker last
    result["status"] = "landed"
    return result
