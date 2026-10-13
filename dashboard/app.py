"""
CipherTrap Dashboard - Enhanced ransomware detection & protection system.

Features:
- Real-time risk scoring and threat detection
- Ransomware signature identification (LockBit, Ryuk, WannaCry, etc.)
- Honeyfile deployment and monitoring
- Automatic snapshot creation and recovery
- Audit logging with tampering detection

Run: python dashboard/app.py /path/to/protected_folder
Then open http://127.0.0.1:5000
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, jsonify, render_template

from core.monitor import FolderMonitor
from core.risk_engine import score_activity, filter_file_only_stats
from core.honeyfiles import deploy_honeyfiles, check_honeyfile_integrity
from core.integrity import AuditLog
from core.snapshot import list_snapshots
from core.threat_intelligence import detect_malware_signature, is_likely_encrypted
from core.auto_backup import SnapshotScheduler, HOURLY_BACKUP

app = Flask(__name__)

state = {
    "folder": None,
    "monitor": None,
    "honeyfiles": [],
    "directory_paths": set(),
    "changed_extensions": set(),
    "vault_folder": None,
    "audit_log": None,
    "latest_assessment": None,
    "suspicious_patterns": [],
    "honeyfile_status": {},
    "modified_files": [],
    "encrypted_files": [],
    "scheduler": None,
    "vault_available": False,
}


def _background_scorer():
    while True:
        time.sleep(2)
        monitor: FolderMonitor | None = state["monitor"]
        if monitor is None:
            continue

        raw_stats = filter_file_only_stats(monitor.all_raw_stats(), state["directory_paths"])
        samples = []
        modified_files = []
        encrypted_files = []
        
        for stat in sorted(raw_stats, key=lambda s: s.last_seen, reverse=True)[:5]:
            try:
                if stat.path.exists() and stat.path.is_file():
                    samples.append(stat.path.read_bytes()[:4096])
                    modified_files.append(stat.path)
                    
                    # Check if file appears encrypted
                    if is_likely_encrypted(stat.path):
                        encrypted_files.append(stat.path)
            except OSError:
                continue

        assessment = score_activity(
            raw_stats=raw_stats,
            honeyfiles=state["honeyfiles"],
            changed_extensions=state["changed_extensions"],
            sampled_file_bytes=samples,
        )
        state["latest_assessment"] = assessment
        state["modified_files"] = modified_files
        state["encrypted_files"] = encrypted_files
        
        # Threat Intelligence Detection
        threat_detection = detect_malware_signature(
            modified_files=modified_files,
            deleted_files=[],
            encrypted_files=encrypted_files,
        )
        
        state["suspicious_patterns"] = [
            {
                "malware": malware,
                "confidence": f"{threat_detection.confidence_scores[malware]:.0%}",
                "description": f"Detected {malware} signature"
            }
            for malware in threat_detection.detected_malware
        ] + [
            {"malware": "Behavior", "confidence": "high", "description": pattern}
            for pattern in threat_detection.attack_patterns
        ]
        
        # Check honeyfile integrity
        for honey in state["honeyfiles"]:
            is_intact = check_honeyfile_integrity(honey)
            state["honeyfile_status"][str(honey.path)] = is_intact
            if not is_intact and state["audit_log"]:
                state["audit_log"].append("honeyfile_compromised", {
                    "file": honey.path.name,
                    "risk_escalation": "HONEYFILE_TRIPPED"
                })

        if assessment.reasons and state["audit_log"] is not None:
            state["audit_log"].append("risk_assessment", assessment.as_dict())


def init_monitoring(folder: str, vault_folder: str, enable_auto_backup: bool = False) -> None:
    folder_path = Path(folder).expanduser().resolve()
    folder_path.mkdir(parents=True, exist_ok=True)
    vault_path = Path(vault_folder).expanduser().resolve()
    vault_path.mkdir(parents=True, exist_ok=True)

    state["folder"] = folder_path
    state["vault_folder"] = vault_path
    state["vault_available"] = True
    state["honeyfiles"] = deploy_honeyfiles(folder_path, count=3)
    state["audit_log"] = AuditLog(Path(__file__).parent.parent / "logs" / "audit_log.jsonl")

    def on_event(event):
        if event.is_directory:
            state["directory_paths"].add(event.path)
        elif event.path.suffix:
            state["changed_extensions"].add(event.path.suffix)

    monitor = FolderMonitor(folder_path, callback=on_event, debounce_seconds=0.25)
    monitor.start()
    state["monitor"] = monitor
    
    # Initialize auto-backup scheduler (optional)
    if enable_auto_backup:
        scheduler = SnapshotScheduler(HOURLY_BACKUP)
        scheduler.start(folder_path, vault_path)
        state["scheduler"] = scheduler
        state["audit_log"].append("auto_backup_enabled", {
            "interval": "hourly",
            "max_snapshots": HOURLY_BACKUP.max_snapshots
        })

    threading.Thread(target=_background_scorer, daemon=True).start()


@app.route("/")
def index():
    return render_template("index.html", folder=str(state["folder"]))


@app.route("/api/status")
def api_status():
    assessment = state["latest_assessment"]
    
    honeyfile_status = []
    for h in state["honeyfiles"]:
        is_intact = state["honeyfile_status"].get(str(h.path), True)
        honeyfile_status.append({
            "name": h.path.name,
            "path": str(h.path),
            "compromised": not is_intact
        })
    
    snapshots = list_snapshots(state["vault_folder"]) if state["vault_folder"] else []

    return jsonify({
        "folder": str(state["folder"]),
        "risk_score": assessment.score if assessment else 0,
        "risk_level": assessment.level if assessment else "Normal",
        "reasons": assessment.reasons if assessment else [],
        "honeyfiles": honeyfile_status,
        "snapshots": snapshots,
        "suspicious_patterns": state["suspicious_patterns"],
        "vault_available": state["vault_available"],
        "encryption_detected": len(state["encrypted_files"]) > 0,
    })


@app.route("/api/audit-log")
def api_audit_log():
    if state["audit_log"] is None:
        return jsonify({"entries": [], "chain_verified": True})
    entries = [e.as_dict() for e in state["audit_log"].all_entries()][-50:]
    verified, bad_index = state["audit_log"].verify_chain()
    return jsonify({"entries": entries, "chain_verified": verified, "first_bad_index": bad_index})


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dashboard/app.py /path/to/protected_folder [/path/to/vault]")
        sys.exit(1)

    folder_arg = sys.argv[1]
    vault_arg = sys.argv[2] if len(sys.argv) > 2 else str(Path(__file__).parent.parent / "vault" / "snapshots")

    init_monitoring(folder_arg, vault_arg)
    app.run(debug=False, port=5000)
