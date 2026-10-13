# 🛡️ CipherTrap - Ransomware Detection & Recovery System

## ⚡ QUICK START (3 Steps)

### Step 1: Setup
```bash
pip install -r requirements.txt
```

### Step 2: Create Folder with YOUR Important Files
```bash
mkdir my_important_files
cp ~/Documents/your_file.pdf my_important_files/
cp ~/Desktop/your_data.xlsx my_important_files/
```

### Step 3: Run in 3 Terminals

**Terminal 1 - Start Dashboard:**
```bash
python dashboard/app.py demo_folder
# Open: http://127.0.0.1:5000
```

**Terminal 2 - Run Attack Simulation:**
```bash
python tests/simulate_attack.py demo_folder
```

**Terminal 3 - Show Tests Pass:**
```bash
python -m pytest tests/test_ciphertrap.py -v
```

---

## 📋 EXECUTABLE PROGRAMS (What You Run)

| Program | Purpose | Usage |
|---------|---------|-------|
| `backup_my_files.py` | Backup your real files | `python backup_my_files.py` |
| `recovery_my_files.py` | Recover from backup | `python recovery_my_files.py SNAPSHOT_ID` |
| `main.py` | Main system entry | `python main.py` |
| `dashboard/app.py` | Web dashboard | `python dashboard/app.py folder_path` |
| `tests/simulate_attack.py` | Attack simulator | `python tests/simulate_attack.py folder_path` |

---

## 📚 DOCUMENTATION (Read These)

All docs are in `docs/` folder:
- `CIPHERTRAP_VIVA_GUIDE.md` - Complete viva defense guide
- `VIVA_COMMANDS.txt` - Copy-paste demo commands
- `USE_YOUR_OWN_FILES.md` - Guide for real files
- `README.md` - Project overview

---

## 🎯 FOR YOUR VIVA

1. **Prepare files:**
   ```bash
   mkdir my_important_files
   cp ~/Documents/report.pdf my_important_files/
   cp ~/Desktop/data.xlsx my_important_files/
   ```

2. **Create backup:**
   ```bash
   python backup_my_files.py
   # Copy the Snapshot ID!
   ```

3. **Run demo (3 terminals):**
   - Terminal 1: `python dashboard/app.py demo_folder`
   - Terminal 2: `python tests/simulate_attack.py demo_folder`
   - Terminal 3: `python -m pytest tests/test_ciphertrap.py -v`

4. **Recover files:**
   ```bash
   python recovery_my_files.py snap_XXXXX
   ```

---

## 📂 PROJECT STRUCTURE

```
CipherTrap/
├── core/                    ← Core modules (don't touch)
├── dashboard/               ← Flask web app
├── tests/                   ← Unit tests
├── vault/                   ← Encrypted backups (auto-created)
├── logs/                    ← Audit logs (auto-created)
├── my_important_files/      ← PUT YOUR FILES HERE
│
├── backup_my_files.py       ← RUN THIS to backup
├── recovery_my_files.py     ← RUN THIS to recover
├── main.py                  ← Main system
│
├── docs/                    ← Documentation folder
├── demos/                   ← Demo scripts
├── requirements.txt         ← Dependencies
└── README.md                ← Project info
```

---

## 🔐 Security Features

✅ AES-256-GCM encryption
✅ Honeyfile decoys (trap ransomware)
✅ Real-time threat detection
✅ Automatic encrypted backups
✅ Password-protected recovery
✅ 12 unit tests (all passing)

---

## 🚀 Expected Demo Output

```
[BACKUP] 3 files
  report.pdf (250.5 KB)
  data.xlsx (125.3 KB)
Snapshot ID: snap_a1b2c3d4e5f6

[RANSOMWARE SIMULATION] Target: demo_folder
[SETUP] Created 15 files
[ATTACK COMPLETE] Files encrypted with AES-256-GCM

[RECOVERY] Snapshot: snap_a1b2c3d4e5f6
[SUCCESS] Files restored: 3
Data Integrity: 100% Verified
```

---

## ❓ Common Commands

```bash
# Create backup with YOUR files
python backup_my_files.py

# Recover from backup
python recovery_my_files.py snap_a1b2c3d4e5f6

# Run unit tests
python -m pytest tests/test_ciphertrap.py -v

# Start web dashboard
python dashboard/app.py my_important_files

# Simulate ransomware attack
python tests/simulate_attack.py demo_folder
```

---

**Good luck with your viva! 🎓**
