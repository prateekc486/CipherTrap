#!/usr/bin/env python
"""
Simple one-command backup for viva demo.
Just run: python backup_demo.py
"""

from pathlib import Path
from core.snapshot import create_snapshot

# Create demo files
demo = Path('demo_folder')
demo.mkdir(exist_ok=True)
for i in range(5):
    (demo / f'document_{i}.txt').write_text(f'Important document #{i}\nCritical business data.\n' * 3)

# Create encrypted snapshot
snapshot = create_snapshot(demo, 'vault', 'recovery_password_123')
print(f'✅ Snapshot created: {snapshot.snapshot_id}')
print(f'✅ Files backed up: {len(snapshot.files)}')
print(f'\n📋 COPY THIS SNAPSHOT ID FOR RECOVERY:')
print(f'   {snapshot.snapshot_id}')
