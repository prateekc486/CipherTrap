#!/usr/bin/env python
"""
CipherTrap - Backup YOUR OWN Important Files

This script backs up YOUR actual important files (not demo files).
Use this for real business files you want to protect!

Usage:
    1. Create a folder with your important files
    2. Run: python backup_my_files.py
    3. Copy the snapshot ID for recovery

Example:
    $ mkdir my_important_files
    $ cp ~/Documents/project.pdf my_important_files/
    $ cp ~/Desktop/financial_data.xlsx my_important_files/
    $ python backup_my_files.py
"""

from pathlib import Path
from core.snapshot import create_snapshot

YOUR_FOLDER = 'my_important_files'
your_folder_path = Path(YOUR_FOLDER)

# Validate folder
if not your_folder_path.exists():
    print(f"ERROR: Folder '{YOUR_FOLDER}' not found")
    print(f"Create it: mkdir {YOUR_FOLDER}")
    exit(1)

files_in_folder = list(your_folder_path.glob('*'))
if len(files_in_folder) == 0:
    print(f"ERROR: No files found in '{YOUR_FOLDER}'")
    exit(1)

print(f"\n[BACKUP] {len(files_in_folder)} files")
for file in files_in_folder:
    size = file.stat().st_size / 1024
    print(f"  {file.name} ({size:.1f} KB)")

# Create encrypted backup
snapshot = create_snapshot(
    source_folder=YOUR_FOLDER,
    vault_folder='vault',
    password='recovery_password_123'
)

print(f"\n[SUCCESS] Backup created")
print(f"Snapshot ID: {snapshot.snapshot_id}")
print(f"Files backed up: {len(snapshot.files)}")
print(f"Encryption: AES-256-GCM")
print(f"\nRecover with: python recovery_my_files.py {snapshot.snapshot_id}\n")
