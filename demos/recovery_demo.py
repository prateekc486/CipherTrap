#!/usr/bin/env python
"""
Simple one-command recovery for viva demo.
Just run: python recovery_demo.py YOUR_SNAPSHOT_ID

Example: python recovery_demo.py snap_a1b2c3d4e5f6
"""

import sys
from pathlib import Path
from core.recovery import restore_snapshot

if len(sys.argv) < 2:
    print("❌ Error: Please provide snapshot ID")
    print("\nUsage: python recovery_demo.py YOUR_SNAPSHOT_ID")
    print("\nExample: python recovery_demo.py snap_a1b2c3d4e5f6")
    sys.exit(1)

snapshot_id = sys.argv[1]

result = restore_snapshot(
    vault_folder='vault',
    snapshot_id=snapshot_id,
    destination_folder='demo_folder_restored',
    password='recovery_password_123'
)

print(f'✅ RECOVERY SUCCESSFUL!')
print(f'✅ Files restored: {len(result.restored_files)}')
print(f'❌ Failed: {len(result.failed_files)}')
for f in result.restored_files:
    print(f'  ✓ {Path(f).name}')
