"""
Restore a snapshot from the vault.

Usage:
    python recovery_my_files.py SNAPSHOT_ID [--to DESTINATION]

Files are restored to my_important_files_restored/ by default. Original
files are never overwritten. The vault password is read from the
CIPHERTRAP_VAULT_PASSWORD environment variable, or prompted for.
"""

import argparse
import sys
from pathlib import Path

from core.config import VAULT_DIR, get_vault_password
from core.recovery import restore_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore an encrypted backup snapshot.")
    parser.add_argument("snapshot_id", help="ID printed by backup_my_files.py")
    parser.add_argument("--to", default="my_important_files_restored",
                        help="destination folder (default: my_important_files_restored)")
    args = parser.parse_args()

    try:
        result = restore_snapshot(
            vault_folder=VAULT_DIR,
            snapshot_id=args.snapshot_id,
            destination_folder=Path(args.to),
            password=get_vault_password(),
        )
    except Exception as exc:
        sys.exit(f"Error: restore failed: {exc}")

    print(f"Restored {len(result.restored_files)} file(s) to {Path(args.to).resolve()}")
    for path in result.restored_files:
        print(f"  {Path(path).name}")

    if result.failed_files:
        print(f"Failed to restore {len(result.failed_files)} file(s):")
        for path in result.failed_files:
            print(f"  {path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
