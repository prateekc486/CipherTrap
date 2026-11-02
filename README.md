# CipherTrap

Ransomware detection, encrypted backup, and recovery for a folder of files.

## Features

- Encrypted snapshots of a folder (AES-256-GCM, key derived with Argon2id)
- Scheduled automatic backups with snapshot rotation
- Honeyfile decoys that alert when touched
- File monitoring with a risk score and a web dashboard
- Restore to a separate folder; originals are never overwritten

## Setup

```bash
pip install -r requirements.txt
```

Set the vault password. It is never stored in the code.

PowerShell (Windows):
```powershell
$env:CIPHERTRAP_VAULT_PASSWORD = "your-strong-password"
```

Bash (Linux/macOS):
```bash
export CIPHERTRAP_VAULT_PASSWORD="your-strong-password"
```

If the variable is not set, the scripts prompt for the password in the terminal.

## Usage

Back up a folder (defaults to `my_important_files/`):

```bash
python backup_my_files.py
python backup_my_files.py path/to/folder
```

Restore a snapshot (defaults to `my_important_files_restored/`):

```bash
python recovery_my_files.py SNAPSHOT_ID
python recovery_my_files.py SNAPSHOT_ID --to some_other_folder
```

Run the dashboard on a folder:

```bash
python dashboard/app.py path/to/folder
```

Open http://127.0.0.1:5000.

Run the attack simulator. It only works on a demo folder, which must contain a
`.ciphertrap_demo` marker file or not exist yet:

```bash
python tests/simulate_attack.py demo_folder
```

Run the tests:

```bash
python -m pytest tests/ -v
```

## Configuration

All optional, set as environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `CIPHERTRAP_VAULT_PASSWORD` | prompt | Password for encrypting and decrypting snapshots |
| `CIPHERTRAP_VAULT_DIR` | `vault/` | Where encrypted snapshots are stored |
| `CIPHERTRAP_LOG_DIR` | `logs/` | Where the audit log is written |
| `CIPHERTRAP_BACKUP_INTERVAL` | `600` | Seconds between automatic backups |
| `CIPHERTRAP_MAX_SNAPSHOTS` | `10` | Snapshots kept before the oldest are deleted |

## Layout

```
core/              detection, encryption, snapshots, recovery, scheduling
dashboard/         Flask dashboard
tests/             unit tests and attack simulator
docs/              viva guide
backup_my_files.py       create a snapshot
recovery_my_files.py     restore a snapshot
```

## Security notes

- Keep the vault on a separate disk or copy it off the machine. A backup on the same disk fails with the disk.
- Losing the vault password means losing access to every snapshot.
- Detection is heuristic. Keep normal backups as well.
