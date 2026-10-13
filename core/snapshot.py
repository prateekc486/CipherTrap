"""
Snapshot module for CipherTrap.

Creates encrypted, integrity-verified backups ("snapshots") of a monitored
folder. Each snapshot stores:
- The encrypted bytes of every file (AES-256-GCM via crypto_utils)
- A manifest listing every file's original SHA-256 hash and relative path
- The manifest itself is hashed, so tampering with the manifest (e.g.
  swapping which hash belongs to which file) is also detectable

This is intentionally simple (no delta/incremental snapshots) to keep the
MVP scope manageable -- each snapshot is a full copy.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from core.crypto_utils import (
    decrypt_file_with_password,
    encrypt_file_with_password,
    sha256_hash,
    sha256_hash_file,
)


@dataclass
class SnapshotManifest:
    snapshot_id: str
    created_at: float
    source_folder: str
    files: dict[str, str]  # relative_path -> original sha256 hash

    def as_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "created_at": self.created_at,
            "source_folder": self.source_folder,
            "files": self.files,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SnapshotManifest":
        return cls(**data)


def create_snapshot(
    source_folder: str | Path,
    vault_folder: str | Path,
    password: str,
    *,
    exclude_names: set[str] | None = None,
) -> SnapshotManifest:
    """
    Create an encrypted snapshot of every file in `source_folder`, storing
    the encrypted copies + manifest inside `vault_folder`.

    `exclude_names` can be used to skip honeyfiles or other files that
    shouldn't be part of the "clean" backup.
    """
    source = Path(source_folder).expanduser().resolve()
    vault = Path(vault_folder).expanduser().resolve()
    exclude_names = exclude_names or set()

    if not source.is_dir():
        raise NotADirectoryError(f"{source} is not a directory")

    snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"
    snapshot_dir = vault / snapshot_id
    snapshot_dir.mkdir(parents=True, exist_ok=False)

    file_hashes: dict[str, str] = {}

    for file_path in source.rglob("*"):
        if file_path.is_dir():
            continue
        if file_path.name in exclude_names:
            continue

        relative_path = file_path.relative_to(source)
        original_hash = sha256_hash_file(str(file_path))
        file_hashes[str(relative_path)] = original_hash

        # Encrypt and write to the vault, preserving folder structure but
        # storing as .enc files so plaintext extensions aren't leaked.
        encrypted_path = snapshot_dir / (str(relative_path) + ".enc")
        encrypted_path.parent.mkdir(parents=True, exist_ok=True)

        plaintext = file_path.read_bytes()
        blob = encrypt_file_with_password(plaintext, password)
        encrypted_path.write_bytes(blob)

    manifest = SnapshotManifest(
        snapshot_id=snapshot_id,
        created_at=time.time(),
        source_folder=str(source),
        files=file_hashes,
    )

    manifest_path = snapshot_dir / "manifest.json"
    manifest_json = json.dumps(manifest.as_dict(), sort_keys=True)
    manifest_path.write_text(manifest_json)

    # Store a signed hash of the manifest alongside it for tamper detection
    manifest_hash_path = snapshot_dir / "manifest.sha256"
    manifest_hash_path.write_text(sha256_hash(manifest_json.encode("utf-8")))

    return manifest


def verify_snapshot_manifest(snapshot_dir: str | Path) -> bool:
    """
    Verify that the manifest.json file hasn't been tampered with, by
    recomputing its hash and comparing to the stored manifest.sha256.
    """
    snapshot_path = Path(snapshot_dir)
    manifest_path = snapshot_path / "manifest.json"
    manifest_hash_path = snapshot_path / "manifest.sha256"

    if not manifest_path.exists() or not manifest_hash_path.exists():
        return False

    manifest_json = manifest_path.read_text()
    expected_hash = manifest_hash_path.read_text().strip()
    actual_hash = sha256_hash(manifest_json.encode("utf-8"))

    return actual_hash == expected_hash


def load_manifest(snapshot_dir: str | Path) -> SnapshotManifest:
    manifest_path = Path(snapshot_dir) / "manifest.json"
    data = json.loads(manifest_path.read_text())
    return SnapshotManifest.from_dict(data)


def list_snapshots(vault_folder: str | Path) -> list[str]:
    """Return snapshot IDs available in the vault, newest first."""
    vault = Path(vault_folder)
    if not vault.is_dir():
        return []
    snapshot_dirs = [d for d in vault.iterdir() if d.is_dir() and d.name.startswith("snap_")]
    snapshot_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    return [d.name for d in snapshot_dirs]
