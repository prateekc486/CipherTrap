# CipherTrap
**A Cryptographic Ransomware Detection, Integrity Monitoring, and File Recovery System**

CipherTrap watches a folder for ransomware-like destructive activity, keeps
encrypted verified backups, and lets you restore clean files after an
incident. Built for a BCA cybersecurity/cryptography project.

## What it detects
- Rapid repeated modification of a single file (in-place encryption pattern)
- Mass file extension changes (e.g. `.locked`, `.enc`)
- High-entropy file content (a strong signal of encryption/compression)
- Tampering with decoy "honeyfiles" planted in the monitored folder

## What it protects
- Every backed-up file is encrypted locally with **AES-256-GCM**
  (authenticated encryption — tampering with backup data is automatically
  detected on decrypt).
- Keys are derived from your password using **Argon2id** (memory-hard,
  resistant to brute force).
- Backup manifests are hashed, so a swapped or edited manifest is detected
  before restore ever happens.
- The security event log is **hash-chained** (like a mini blockchain) —
  editing any past log entry breaks the chain and is immediately visible.

## Project structure
```
CipherTrap/
├── main.py                 # CLI live monitor + risk scorer
├── requirements.txt
├── core/
│   ├── monitor.py          # watchdog-based folder monitoring (raw + debounced events)
│   ├── honeyfiles.py       # decoy files + tamper checking
│   ├── risk_engine.py      # rule-based 0-100 risk scoring
│   ├── crypto_utils.py     # AES-256-GCM + Argon2id
│   ├── integrity.py        # hash-chained audit log
│   ├── snapshot.py         # encrypted backup creation
│   └── recovery.py         # restore from snapshot
├── dashboard/
│   ├── app.py               # Flask dashboard
│   └── templates/index.html
├── tests/
│   └── simulate_attack.py   # SAFE ransomware-behavior simulator
├── vault/snapshots/         # encrypted backups live here
└── logs/audit_log.jsonl     # tamper-evident event log
```

## Setup
```bash
cd CipherTrap
pip install -r requirements.txt
```

## Running the live CLI demo
```bash
python main.py /path/to/folder_to_protect
```
In a second terminal, run the safe attack simulator against the same folder:
```bash
python tests/simulate_attack.py /path/to/folder_to_protect
```
You'll see the risk score rise in real time as the simulator runs.

## Running the dashboard
```bash
python dashboard/app.py /path/to/folder_to_protect /path/to/vault
```
Then open **http://127.0.0.1:5000**

## Creating and restoring a backup (Python API)
```python
from core.snapshot import create_snapshot
from core.recovery import restore_snapshot

# Create an encrypted snapshot
manifest = create_snapshot("my_folder", "vault/snapshots", password="my-secret-password")

# Later, restore it
result = restore_snapshot("vault/snapshots", manifest.snapshot_id, "restored_folder", "my-secret-password")
print(result.restored_files, result.failed_files)
```

## Cryptography design
```
User password
     |
     v
Argon2id  (memory-hard KDF, unique salt per file)
     |
     v
256-bit AES key
     |
     v
AES-256-GCM encrypts file  (fresh random nonce every time)
     |
     v
[salt][nonce][ciphertext + auth tag]  -> written to vault
```

Tampering with any encrypted backup file causes AES-GCM's authentication
tag check to fail on decrypt, raising `DecryptionError` — this is how
CipherTrap knows a backup has been corrupted or tampered with, without
needing a separate integrity-check step.

## Known limitations (be upfront about these in your report)
- This is a rule-based heuristic detector, not a guarantee — legitimate
  software (backup tools, compressors, updaters) can also trigger elevated
  scores. Frame it as detecting "ransomware-like destructive behavior,"
  not "detects all ransomware."
- Snapshots are full copies, not incremental/delta backups — fine for a
  student project scope, but would need optimization for large real-world
  folders.
- The Flask dev server is single-user and not production-hardened; that's
  expected and fine for a project demo.

## Testing
All core modules were tested during development:
- `crypto_utils.py`: round-trip encryption/decryption, wrong-password
  rejection, tamper detection (bit-flip → `DecryptionError`), nonce
  uniqueness, Argon2id timing.
- `monitor.py`: create/modify/move/delete detection, rapid same-file writes
  correctly tracked via raw (non-debounced) counters, ignored-path
  exclusion, callback-exception resilience.
- `risk_engine.py`: normal activity stays low-risk, combined attack
  scenario (rapid writes + high entropy + honeyfile tamper) correctly
  scores High-risk (75/100).
- Full integration: clean snapshot → simulated ransomware corruption →
  restore recovers exact original content; tampered manifests are
  correctly refused at restore time; audit log tampering is detected via
  broken hash chain.
