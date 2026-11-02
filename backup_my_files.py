"""
Create an encrypted snapshot of a folder in the vault.

Usage:
    python backup_my_files.py [folder]

The folder defaults to my_important_files. The vault password is read from
the CIPHERTRAP_VAULT_PASSWORD environment variable, or prompted for.
"""

import argparse
import sys
from pathlib import Path

from core.config import VAULT_DIR, get_vault_password
from core.snapshot import create_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an encrypted backup snapshot.")
    parser.add_argument("folder", nargs="?", default="my_important_files",
                        help="folder to back up (default: my_important_files)")
    args = parser.parse_args()

    source = Path(args.folder).expanduser().resolve()
    if not source.is_dir():
        sys.exit(f"Error: folder not found: {source}")
    if not any(p.is_file() for p in source.iterdir()):
        sys.exit(f"Error: no files found in {source}")

    snapshot = create_snapshot(
        source_folder=source,
        vault_folder=VAULT_DIR,
        password=get_vault_password(),
    )

    print(f"Snapshot ID: {snapshot.snapshot_id}")
    print(f"Files backed up: {len(snapshot.files)}")
    print(f"Restore with: python recovery_my_files.py {snapshot.snapshot_id}")


if __name__ == "__main__":
    main()
