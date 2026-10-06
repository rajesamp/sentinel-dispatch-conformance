"""Hash-chained audit log (WORM-style, honestly labeled).

Each entry embeds the SHA-256 of the previous entry, so editing or deleting
any record breaks every downstream hash. This gives TAMPER-EVIDENCE, not
tamper-PROOFNESS: an attacker with write access to the log file can rewrite
the whole chain. For real WORM guarantees, ship entries to append-only
storage with retention lock (e.g. GCS bucket retention policy / object
holds). This module is the client-side chain; the retention lock is the
deployment's job.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

GENESIS = "0" * 64


def _entry_hash(entry: dict[str, Any]) -> str:
    """SHA-256 over the canonical entry WITHOUT its own hash field."""
    material = {k: v for k, v in entry.items() if k != "entry_hash"}
    blob = json.dumps(material, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class AuditChain:
    """Append-only in-memory chain, optionally mirrored to a JSONL file."""

    def __init__(self, path: str | Path | None = None) -> None:
        self._entries: list[dict[str, Any]] = []
        self._path = Path(path) if path else None
        if self._path and self._path.exists():
            self._load()

    def _load(self) -> None:
        assert self._path is not None
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    self._entries.append(json.loads(line))

    # -- write path ----------------------------------------------------------

    def append(self, event: str, payload: dict[str, Any]) -> dict[str, Any]:
        prev = self._entries[-1]["entry_hash"] if self._entries else GENESIS
        entry: dict[str, Any] = {
            "seq": len(self._entries),
            "ts": time.time(),
            "event": event,
            "payload": payload,
            "prev_hash": prev,
        }
        entry["entry_hash"] = _entry_hash(entry)
        self._entries.append(entry)
        if self._path:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    # -- verify path ---------------------------------------------------------

    def verify(self) -> tuple[bool, str]:
        """Recompute every hash and link. Returns (ok, detail)."""
        prev = GENESIS
        for i, entry in enumerate(self._entries):
            if entry.get("prev_hash") != prev:
                return False, f"chain broken at seq {i}: prev_hash mismatch"
            if _entry_hash(entry) != entry.get("entry_hash"):
                return False, f"chain broken at seq {i}: entry_hash mismatch"
            prev = entry["entry_hash"]
        return True, f"chain intact: {len(self._entries)} entries"

    # -- introspection -------------------------------------------------------

    @property
    def entries(self) -> list[dict[str, Any]]:
        return list(self._entries)

    @property
    def head(self) -> str:
        return self._entries[-1]["entry_hash"] if self._entries else GENESIS

    def __len__(self) -> int:
        return len(self._entries)
