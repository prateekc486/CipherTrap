"""
Integrity module for CipherTrap.

Maintains a hash-chained (tamper-evident) audit log of security events.
Each log entry includes the SHA-256 hash of the previous entry, so any
retroactive edit or deletion of a past entry breaks the chain and is
immediately detectable by verify_chain().
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from core.crypto_utils import sha256_hash

GENESIS_HASH = "0" * 64


@dataclass
class AuditEntry:
    index: int
    timestamp: float
    event_type: str
    details: dict
    previous_hash: str
    entry_hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.entry_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "event_type": self.event_type,
                "details": self.details,
                "previous_hash": self.previous_hash,
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256_hash(payload)

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "details": self.details,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        entry = cls(
            index=data["index"],
            timestamp=data["timestamp"],
            event_type=data["event_type"],
            details=data["details"],
            previous_hash=data["previous_hash"],
        )
        # Preserve the originally stored hash rather than recomputing,
        # so verify_chain() can detect if the recomputed hash differs.
        entry.entry_hash = data["entry_hash"]
        return entry


class AuditLog:
    """A simple append-only, hash-chained audit log stored as JSON lines."""

    def __init__(self, log_path: str | Path):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.write_text("")

    def _read_entries(self) -> list[AuditEntry]:
        entries: list[AuditEntry] = []
        content = self.log_path.read_text().strip()
        if not content:
            return entries
        for line in content.splitlines():
            entries.append(AuditEntry.from_dict(json.loads(line)))
        return entries

    def append(self, event_type: str, details: dict) -> AuditEntry:
        entries = self._read_entries()
        previous_hash = entries[-1].entry_hash if entries else GENESIS_HASH
        new_entry = AuditEntry(
            index=len(entries),
            timestamp=time.time(),
            event_type=event_type,
            details=details,
            previous_hash=previous_hash,
        )
        with self.log_path.open("a") as f:
            f.write(json.dumps(new_entry.as_dict()) + "\n")
        return new_entry

    def all_entries(self) -> list[AuditEntry]:
        return self._read_entries()

    def verify_chain(self) -> tuple[bool, int | None]:
        """
        Verify the entire hash chain.

        Returns (True, None) if the chain is intact, or (False, index) with
        the index of the first entry found to be tampered with or broken.
        """
        entries = self._read_entries()
        expected_previous = GENESIS_HASH

        for entry in entries:
            if entry.previous_hash != expected_previous:
                return False, entry.index

            recomputed = entry._compute_hash()
            if recomputed != entry.entry_hash:
                return False, entry.index

            expected_previous = entry.entry_hash

        return True, None
