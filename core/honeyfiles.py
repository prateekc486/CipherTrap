"""
Honeyfile module for CipherTrap.

Creates decoy files inside the monitored folder that a normal user has no
reason to touch. If a honeyfile is modified, renamed, or deleted, it is a
very strong signal of unauthorized or malicious activity (a legitimate
user's software updates, backups, etc. don't know these files are special
and won't single them out -- but ransomware and other bulk-scanning
malware often touch every file in a directory, tripping the decoy).
"""

from __future__ import annotations

import hashlib
import random
import string
from dataclasses import dataclass
from pathlib import Path

# Realistic-looking filenames that an attacker/ransomware scanning a
# directory would have no reason to skip.
HONEYFILE_NAMES = [
    "passwords_backup.txt",
    "financial_records_2024.xlsx",
    "id_documents_scan.pdf",
    "company_confidential.docx",
    "database_credentials.txt",
]

HONEYFILE_MARKER = "CIPHERTRAP_HONEYFILE_DO_NOT_DELETE"


@dataclass(frozen=True, slots=True)
class Honeyfile:
    path: Path
    original_hash: str


def _generate_decoy_content(filename: str) -> bytes:
    """Generate plausible-looking filler content for a decoy file."""
    noise = "".join(random.choices(string.ascii_letters + string.digits, k=256))
    content = (
        f"{HONEYFILE_MARKER}\n"
        f"filename: {filename}\n"
        f"-- do not delete, this file is used by CipherTrap for tamper detection --\n"
        f"{noise}\n"
    )
    return content.encode("utf-8")


def deploy_honeyfiles(folder: str | Path, count: int = 3) -> list[Honeyfile]:
    """
    Create `count` honeyfiles inside `folder` and return their metadata
    (path + original SHA-256 hash) so they can later be checked for
    tampering by the integrity module.
    """
    folder_path = Path(folder).expanduser().resolve(strict=False)
    if not folder_path.is_dir():
        raise NotADirectoryError(f"{folder_path} is not a directory")

    chosen_names = random.sample(HONEYFILE_NAMES, k=min(count, len(HONEYFILE_NAMES)))
    honeyfiles: list[Honeyfile] = []

    for name in chosen_names:
        file_path = folder_path / name
        content = _generate_decoy_content(name)
        file_path.write_bytes(content)
        file_hash = hashlib.sha256(content).hexdigest()
        honeyfiles.append(Honeyfile(path=file_path, original_hash=file_hash))

    return honeyfiles


def is_honeyfile(path: str | Path, honeyfiles: list[Honeyfile]) -> bool:
    """Check whether a given path matches one of the deployed honeyfiles."""
    resolved = Path(path).expanduser().resolve(strict=False)
    return any(h.path == resolved for h in honeyfiles)


def check_honeyfile_integrity(honeyfile: Honeyfile) -> bool:
    """
    Return True if the honeyfile is unchanged (still exists with the
    original hash), False if it was modified or deleted.
    """
    if not honeyfile.path.exists():
        return False
    current_content = honeyfile.path.read_bytes()
    current_hash = hashlib.sha256(current_content).hexdigest()
    return current_hash == honeyfile.original_hash


def cleanup_honeyfiles(honeyfiles: list[Honeyfile]) -> None:
    """Remove all deployed honeyfiles (e.g. on app shutdown)."""
    for h in honeyfiles:
        if h.path.exists():
            h.path.unlink()
