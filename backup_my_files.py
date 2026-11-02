"""
Back up a folder into the vault, automatically and repeatedly.

Usage:
    python backup_my_files.py [folder]        # runs until Ctrl+C
    python backup_my_files.py --once          # one snapshot, then exit

The folder defaults to my_important_files. A snapshot is taken immediately,
then again every CIPHERTRAP_BACKUP_INTERVAL seconds (default 600). Old
snapshots beyond CIPHERTRAP_MAX_SNAPSHOTS are deleted. The dashboard reads
the same vault, so new snapshots appear there automatically.
"""

import argparse
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

from core.config import BACKUP_INTERVAL_SECONDS, MAX_SNAPSHOTS, VAULT_DIR, get_vault_password
from core.snapshot import create_snapshot, list_snapshots


def prune_old_snapshots(vault: Path, keep: int) -> None:
    """Delete the oldest snapshots so that only `keep` remain."""
    snapshots = list_snapshots(vault)  # newest first
    for snapshot_id in snapshots[keep:]:
        shutil.rmtree(vault / snapshot_id, ignore_errors=True)
        print(f"  removed old snapshot {snapshot_id}")


def take_snapshot(source: Path, password: str) -> None:
    snapshot = create_snapshot(source_folder=source, vault_folder=VAULT_DIR, password=password)
    stamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{stamp}] Snapshot ID: {snapshot.snapshot_id}  ({len(snapshot.files)} files)")
    prune_old_snapshots(VAULT_DIR, MAX_SNAPSHOTS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Back up a folder into the vault.")
    parser.add_argument("folder", nargs="?", default="my_important_files",
                        help="folder to back up (default: my_important_files)")
    parser.add_argument("--once", action="store_true", help="take one snapshot and exit")
    args = parser.parse_args()

    source = Path(args.folder).expanduser().resolve()
    if not source.is_dir():
        sys.exit(f"Error: folder not found: {source}")
    if not any(p.is_file() for p in source.iterdir()):
        sys.exit(f"Error: no files found in {source}")

    password = get_vault_password()

    if args.once:
        take_snapshot(source, password)
        return

    print(f"Backing up {source} every {BACKUP_INTERVAL_SECONDS} seconds. Press Ctrl+C to stop.")
    try:
        while True:
            take_snapshot(source, password)
            time.sleep(BACKUP_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nBackup stopped.")


if __name__ == "__main__":
    main()
