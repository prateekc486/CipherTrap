"""
CipherTrap - main entry point / live demo.

Watches a folder, deploys honeyfiles, and continuously prints the current
risk score as filesystem activity happens. Run this in one terminal, then
run tests/simulate_attack.py against the SAME folder in another terminal
(or just let this script run the simulation itself with --simulate).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.monitor import FolderMonitor
from core.risk_engine import score_activity, filter_file_only_stats
from core.honeyfiles import deploy_honeyfiles, cleanup_honeyfiles
from core.integrity import AuditLog


def main() -> None:
    parser = argparse.ArgumentParser(description="CipherTrap live folder monitor + risk scorer")
    parser.add_argument("folder", help="Folder to protect/monitor")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between risk score checks")
    parser.add_argument("--honeyfiles", type=int, default=3, help="Number of honeyfiles to deploy")
    args = parser.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)

    print(f"CipherTrap watching: {folder}")
    honeyfiles = deploy_honeyfiles(folder, count=args.honeyfiles)
    print(f"Deployed {len(honeyfiles)} honeyfiles: {[h.path.name for h in honeyfiles]}")

    audit_log = AuditLog(Path(__file__).parent / "logs" / "audit_log.jsonl")
    audit_log.append("monitoring_started", {"folder": str(folder), "honeyfile_count": len(honeyfiles)})

    directory_paths: set[Path] = set()
    changed_extensions: set[str] = set()

    def on_event(event):
        if event.is_directory:
            directory_paths.add(event.path)
        elif event.path.suffix:
            changed_extensions.add(event.path.suffix)

    monitor = FolderMonitor(folder, callback=on_event, debounce_seconds=0.25)
    monitor.start()

    print("\nMonitoring... press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(args.interval)
            raw_stats = filter_file_only_stats(monitor.all_raw_stats(), directory_paths)

            # Sample a few recently-touched files to estimate entropy
            samples = []
            for stat in sorted(raw_stats, key=lambda s: s.last_seen, reverse=True)[:5]:
                try:
                    if stat.path.exists() and stat.path.is_file():
                        samples.append(stat.path.read_bytes()[:4096])
                except OSError:
                    continue

            assessment = score_activity(
                raw_stats=raw_stats,
                honeyfiles=honeyfiles,
                changed_extensions=changed_extensions,
                sampled_file_bytes=samples,
            )

            print(f"[{time.strftime('%H:%M:%S')}] Risk score: {assessment.score:3d}  ({assessment.level})")
            if assessment.reasons:
                for reason in assessment.reasons:
                    print(f"    - {reason}")
                audit_log.append("risk_assessment", assessment.as_dict())

            if assessment.score >= 60:
                print("    !!! HIGH RISK - consider restoring from last clean snapshot !!!")

    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        monitor.stop()
        monitor.join(timeout=2)
        cleanup_honeyfiles(honeyfiles)
        audit_log.append("monitoring_stopped", {"folder": str(folder)})
        print("Stopped. Honeyfiles cleaned up.")


if __name__ == "__main__":
    main()
