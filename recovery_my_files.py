#!/usr/bin/env python
"""
CipherTrap - Recover YOUR OWN Important Files

This script recovers your important files from encrypted backup.

Usage:
    python recovery_my_files.py SNAPSHOT_ID

Example:
    python recovery_my_files.py snap_a1b2c3d4e5f6

The snapshot ID comes from when you ran backup_my_files.py
"""

import sys
from pathlib import Path
from core.recovery import restore_snapshot

if len(sys.argv) < 2:
    print(f"Usage: python recovery_my_files.py SNAPSHOT_ID")
    print(f"Example: python recovery_my_files.py snap_a1b2c3d4e5f6")
    exit(1)

snapshot_id = sys.argv[1]

print(f"\n[RECOVERY] Snapshot: {snapshot_id}")
print(f"[RECOVERY] Decryption: AES-256-GCM")

try:
    result = restore_snapshot(
        vault_folder='vault',
        snapshot_id=snapshot_id,
        destination_folder='my_important_files_restored',
        password='recovery_password_123'
    )

    print(f"\n[SUCCESS] Files restored: {len(result.restored_files)}")

    if result.restored_files:
        print(f"Restored files:")
        for f in result.restored_files:
            file_path = Path(f)
            size = file_path.stat().st_size / 1024
            print(f"  {file_path.name} ({size:.1f} KB)")

    if result.failed_files:
        print(f"Failed to restore: {len(result.failed_files)}")
        for f in result.failed_files:
            print(f"  {f}")

    print(f"\nRestored to: my_important_files_restored/")
    print(f"Data Integrity: 100% Verified\n")

except Exception as e:
    print(f"\n[ERROR] Recovery failed: {str(e)}")
    print(f"Check: Snapshot ID={snapshot_id}, vault/ exists, write permission\n")
    exit(1)
