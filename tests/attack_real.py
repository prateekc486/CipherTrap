"""
Real-world style attack on YOUR original files in my_important_files/.

What it does:
1. Takes a fresh encrypted backup of my_important_files/
2. Restores that backup to a temporary folder and checks every file matches
3. Encrypts your ORIGINAL files in place, the way ransomware would

The encryption key is discarded. After this runs, the only way back is the
snapshot in the vault, so the backup check in step 2 must pass first.

Usage:
    python tests/attack_real.py
"""

import argparse
import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simulate_attack import encrypt_file
from core.config import VAULT_DIR, get_vault_password
from core.recovery import restore_snapshot
from core.snapshot import create_snapshot


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Attack your original files (with a verified backup first).")
    parser.add_argument("folder", nargs="?", default="my_important_files", help="folder to attack")
    args = parser.parse_args()
    SOURCE = Path(args.folder).expanduser().resolve()

    if not SOURCE.is_dir():
        sys.exit(f"Error: {SOURCE} not found.")
    files = [p for p in SOURCE.rglob("*") if p.is_file()]
    if not files:
        sys.exit(f"Error: no files in {SOURCE}.")

    password = get_vault_password()

    print(f"WARNING: this encrypts the {len(files)} ORIGINAL file(s) in {SOURCE}.")
    if input("Type YES to continue: ").strip() != "YES":
        sys.exit("Cancelled. Nothing was changed.")

    snapshot = create_snapshot(source_folder=SOURCE, vault_folder=VAULT_DIR, password=password)
    print(f"Backup taken: {snapshot.snapshot_id}")

    check_dir = Path(tempfile.mkdtemp(prefix="ciphertrap_check_"))
    try:
        result = restore_snapshot(
            vault_folder=VAULT_DIR,
            snapshot_id=snapshot.snapshot_id,
            destination_folder=check_dir,
            password=password,
        )
        if result.failed_files:
            sys.exit("Backup verification failed. Originals NOT encrypted.")

        restored = {p.name: p for p in check_dir.rglob("*") if p.is_file()}
        for original in files:
            copy = restored.get(original.name)
            if copy is None or sha256(copy) != sha256(original):
                sys.exit(f"Backup check mismatch on {original.name}. Originals NOT encrypted.")
    finally:
        shutil.rmtree(check_dir, ignore_errors=True)

    print("Backup verified: every file restores exactly.")

    key = os.urandom(32)  # discarded after this run
    for path in files:
        encrypt_file(path, key)
        print(f"[ATTACK] Encrypted: {path}")

    print(f"\nDone. {len(files)} original file(s) are now encrypted.")
    print(f"Recover with: python recovery_my_files.py {snapshot.snapshot_id}")


if __name__ == "__main__":
    main()
