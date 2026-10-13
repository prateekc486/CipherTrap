"""
Recovery module for CipherTrap.

Restores files from an encrypted snapshot created by snapshot.py. Verifies
the manifest hasn't been tampered with before trusting it, and verifies
each restored file's hash matches what's recorded in the manifest.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.crypto_utils import decrypt_file_with_password, sha256_hash, DecryptionError
from core.snapshot import load_manifest, verify_snapshot_manifest


class RecoveryError(Exception):
    """Raised when a snapshot cannot be safely restored."""


@dataclass
class RestoreResult:
    restored_files: list[str]
    failed_files: list[str]
    manifest_verified: bool


def restore_snapshot(
    vault_folder: str | Path,
    snapshot_id: str,
    destination_folder: str | Path,
    password: str,
    *,
    only_files: list[str] | None = None,
) -> RestoreResult:
    """
    Restore files from `snapshot_id` in the vault into `destination_folder`.

    If `only_files` is given, only those relative paths are restored;
    otherwise every file in the snapshot is restored.

    Raises RecoveryError if the manifest itself appears tampered with --
    restoring from a manifest that can't be trusted defeats the purpose
    of integrity verification.
    """
    vault = Path(vault_folder).expanduser().resolve()
    snapshot_dir = vault / snapshot_id
    destination = Path(destination_folder).expanduser().resolve()

    if not snapshot_dir.is_dir():
        raise RecoveryError(f"Snapshot not found: {snapshot_id}")

    manifest_ok = verify_snapshot_manifest(snapshot_dir)
    if not manifest_ok:
        raise RecoveryError(
            f"Manifest for snapshot {snapshot_id} failed integrity verification -- "
            "refusing to restore from a potentially tampered backup."
        )

    manifest = load_manifest(snapshot_dir)
    destination.mkdir(parents=True, exist_ok=True)

    restored: list[str] = []
    failed: list[str] = []

    targets = only_files if only_files is not None else list(manifest.files.keys())

    for relative_path in targets:
        expected_hash = manifest.files.get(relative_path)
        if expected_hash is None:
            failed.append(relative_path)
            continue

        encrypted_path = snapshot_dir / (relative_path + ".enc")
        if not encrypted_path.exists():
            failed.append(relative_path)
            continue

        try:
            blob = encrypted_path.read_bytes()
            plaintext = decrypt_file_with_password(blob, password)
        except DecryptionError:
            failed.append(relative_path)
            continue

        actual_hash = sha256_hash(plaintext)
        if actual_hash != expected_hash:
            # File decrypted but doesn't match the recorded hash -- something
            # is wrong (corrupted vault file, or manifest/backup mismatch).
            failed.append(relative_path)
            continue

        out_path = destination / relative_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(plaintext)
        restored.append(relative_path)

    return RestoreResult(restored_files=restored, failed_files=failed, manifest_verified=manifest_ok)
