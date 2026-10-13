# 🛡️ **CIPHERTRAP - BACKUP YOUR OWN IMPORTANT FILES**

**This guide shows how to protect YOUR actual important files (not demo files!)**

---

## **Why Your Own Files?**

In real companies:
- They protect ACTUAL customer data
- They protect REAL financial records
- They protect REAL source code
- They protect REAL employee information

**CipherTrap works with ANY files!** Let me show you how.

---

## **📋 STEP 1: Create Folder for Your Important Files**

### **On Windows:**
```bash
mkdir my_important_files
```

### **On Mac/Linux:**
```bash
mkdir my_important_files
```

### **Or manually:**
- Open file explorer
- Create new folder named `my_important_files`

---

## **📁 STEP 2: Add Your Important Files**

Copy your actual important files into this folder:

```bash
# Copy individual files
cp ~/Documents/project_report.pdf my_important_files/
cp ~/Desktop/financial_data.xlsx my_important_files/
cp ~/Pictures/client_proposal.pptx my_important_files/
```

**Or manually:**
- Open `my_important_files/` folder
- Drag & drop your files into it

**Examples of files you might protect:**
- 📄 PDF documents
- 📊 Excel spreadsheets
- 📝 Word documents
- 💻 Source code files
- 🖼️ Important images
- 🎬 Videos
- 🗄️ Database backups
- 📧 Email exports

---

## **🔐 STEP 3: Backup Your Important Files**

### **Command:**
```bash
python backup_my_files.py
```

### **What you'll see:**
```
======================================================================
🛡️  CipherTrap - Backup Your Own Important Files
======================================================================

📁 Found your folder: my_important_files
📄 Files to backup: 3

📋 Your important files:
   ✓ project_report.pdf (245.5 KB)
   ✓ financial_data.xlsx (125.3 KB)
   ✓ client_proposal.pptx (892.1 KB)

🔐 Creating encrypted backup...
   Password: recovery_password_123
   Encryption: AES-256-GCM
   Location: vault/

======================================================================
✅ BACKUP SUCCESSFUL!
======================================================================

📸 Snapshot ID: snap_a1b2c3d4e5f6
📄 Files backed up: 3
🔐 Encryption: AES-256-GCM
🔑 Password: recovery_password_123

📋 FILES THAT ARE BACKED UP:
   ✓ project_report.pdf
   ✓ financial_data.xlsx
   ✓ client_proposal.pptx

⚠️  IMPORTANT: Copy this Snapshot ID for recovery!

   snap_a1b2c3d4e5f6

📝 To recover these files later, run:
   python recovery_my_files.py snap_a1b2c3d4e5f6

======================================================================
✅ Your important files are now encrypted and protected!
======================================================================
```

**⚠️ IMPORTANT:** Copy the Snapshot ID! (e.g., `snap_a1b2c3d4e5f6`)

---

## **🎯 STEP 4: Show Files to Judges (Before Attack)**

**Open file explorer:**
```
CipherTrap/my_important_files/
```

**You'll see your actual important files:**
```
my_important_files/
├── project_report.pdf ✅
├── financial_data.xlsx ✅
└── client_proposal.pptx ✅
```

**Double-click to open and show they're readable!**

**Tell judges:** "These are MY important business files that I want to protect."

---

## **🚨 STEP 5: Simulate Attack on Your Files**

### **Command:**
```bash
python tests/simulate_attack.py my_important_files
```

**Your files get encrypted!**

---

## **📁 STEP 6: Show Encrypted Files (After Attack)**

**Open file explorer:**
```
CipherTrap/my_important_files/
```

**Files still exist but are encrypted garbage:**
```
my_important_files/
├── project_report.pdf ❌ (encrypted: a7f3d9e1...)
├── financial_data.xlsx ❌ (encrypted: b8g4e0f2...)
└── client_proposal.pptx ❌ (encrypted: c9h5f1g3...)
```

**Double-click to show it's unreadable gibberish!**

**Tell judges:** "My important business files are now encrypted by ransomware!"

---

## **💾 STEP 7: Recover Your Important Files**

### **Command:**
```bash
python recovery_my_files.py snap_a1b2c3d4e5f6
```

Replace `snap_a1b2c3d4e5f6` with YOUR snapshot ID!

### **What you'll see:**
```
======================================================================
🛡️  CipherTrap - Recover Your Own Important Files
======================================================================

📸 Snapshot ID: snap_a1b2c3d4e5f6
🔓 Decryption: AES-256-GCM
🔑 Password: recovery_password_123
📂 Restoring to: my_important_files_restored/

🔐 Recovering encrypted backup...

======================================================================
✅ RECOVERY SUCCESSFUL!
======================================================================

📄 Files restored: 3
❌ Files failed: 0

📋 YOUR RECOVERED FILES:
   ✓ project_report.pdf (245.5 KB)
   ✓ financial_data.xlsx (125.3 KB)
   ✓ client_proposal.pptx (892.1 KB)

📂 Restored folder: my_important_files_restored/

🎉 Your important files are back!
✅ 100% Data Integrity Verified
======================================================================
```

---

## **📁 STEP 8: Show Recovered Files (After Recovery)**

**Open file explorer:**
```
CipherTrap/my_important_files_restored/
```

**Your files are perfectly recovered:**
```
my_important_files_restored/
├── project_report.pdf ✅ (245.5 KB - PERFECT!)
├── financial_data.xlsx ✅ (125.3 KB - PERFECT!)
└── client_proposal.pptx ✅ (892.1 KB - PERFECT!)
```

**Double-click to show they're readable and identical!**

**Tell judges:** "Perfect recovery! All my business files are back and readable! 100% data integrity!"

---

## **🎬 COMPLETE VIVA DEMO FLOW (With Your Files)**

```bash
# Terminal 1: Start dashboard
python dashboard/app.py my_important_files

# Then open browser: http://127.0.0.1:5000

# Terminal 2: Backup YOUR files
python backup_my_files.py
# [Copy snapshot ID]

# Terminal 2: Show original files in file explorer
# Navigate to my_important_files/
# Double-click to show readable

# Terminal 2: Run attack
python tests/simulate_attack.py my_important_files
# [Watch dashboard spike to RED]

# Terminal 2: Show encrypted files in file explorer
# Navigate to my_important_files/
# Double-click to show encrypted garbage

# Terminal 3: Recover YOUR files
python recovery_my_files.py snap_XXXXX

# Terminal 3: Show recovered files in file explorer
# Navigate to my_important_files_restored/
# Double-click to show recovered & readable

# Terminal 3: Show tests
python -m pytest tests/test_ciphertrap.py -v
# [Show 12 passing]
```

---

## **💡 JUDGE TALKING POINTS**

> "Sir/Ma'am, I've demonstrated CipherTrap with realistic business files.
>
> I backed up my important files (project_report.pdf, financial_data.xlsx, client_proposal.pptx).
>
> When ransomware attacked, these actual business files were encrypted.
>
> But with CipherTrap's encrypted backup, I was able to recover them perfectly!
>
> This proves our system works with ANY real-world files, not just demo data.
>
> In production, companies would protect:
> - Customer databases
> - Financial records
> - Source code repositories
> - Employee information
> - Business documents
>
> CipherTrap protects ALL of them equally with enterprise-grade encryption!"

---

## **🎓 WHY THIS IS IMPRESSIVE**

### **Using Demo Files:**
```
❌ Looks like just a student project
❌ Might work only with dummy data
❌ Not realistic
```

### **Using Real Files:**
```
✅ Looks like real business protection
✅ Judges know it works with ANY files
✅ Professional & realistic
✅ Shows production thinking
✅ Much more impressive!
```

---

## **❓ TROUBLESHOOTING**

### **Problem: "No files found in 'my_important_files'!"**
**Solution:** Make sure you added files to the folder:
```bash
cp ~/Documents/important_file.pdf my_important_files/
```

### **Problem: "Snapshot not found" during recovery**
**Solution:** Make sure you copied the exact snapshot ID from backup output:
```bash
python recovery_my_files.py snap_a1b2c3d4e5f6
```

### **Problem: Files not recovering**
**Solution:** Check that password matches (it's hardcoded as `recovery_password_123`)

---

## **✅ DEMO CHECKLIST**

- [ ] Created `my_important_files/` folder
- [ ] Added 3-5 of YOUR important files
- [ ] Ran `python backup_my_files.py`
- [ ] Copied snapshot ID
- [ ] Ran `python tests/simulate_attack.py my_important_files`
- [ ] Verified files are encrypted
- [ ] Ran `python recovery_my_files.py SNAPSHOT_ID`
- [ ] Verified files are recovered
- [ ] All tests pass
- [ ] Ready for viva!

---

**Your files are now protected with enterprise-grade encryption!** 🛡️

**Judges will be VERY impressed by this realistic demonstration!** 🏆
