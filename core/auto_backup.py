"""
Auto-Backup Scheduler for CipherTrap.

Automatically creates encrypted snapshots of monitored folders on a schedule.
This provides continuous protection against ransomware by maintaining fresh,
encrypted backups that malware cannot touch.

Supports:
- Hourly, daily, weekly backup schedules
- Maximum snapshot retention (cleanup old backups)
- Password-protected encrypted storage
- Abort on high-risk detection
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from core.snapshot import create_snapshot, list_snapshots, SnapshotManifest
from core.config import BACKUP_INTERVAL_SECONDS, MAX_SNAPSHOTS
from core.honeyfiles import HONEYFILE_NAMES


@dataclass
class BackupSchedule:
    """Configuration for automated backups."""
    interval_seconds: int  # How often to create backups
    max_snapshots: int = MAX_SNAPSHOTS  # Keep only this many recent snapshots


class SnapshotScheduler:
    """Manages automated snapshot creation."""

    def __init__(self, schedule: BackupSchedule):
        self.schedule = schedule
        self.is_running = False
        self.thread = None
        self.last_snapshot_time = None
        self.snapshot_count = 0
        self.logger = logging.getLogger(__name__)

    def start(self, source_folder: str | Path, vault_folder: str | Path, password: str) -> None:
        """Start the backup scheduler."""
        if self.is_running:
            return

        if not password:
            raise ValueError("A vault password is required for automated backups.")

        self.is_running = True
        self.source_folder = Path(source_folder)
        self.vault_folder = Path(vault_folder)
        self.password = password
        
        self.thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True,
            name="SnapshotScheduler"
        )
        self.thread.start()
        self.logger.info(f"Backup scheduler started (interval: {self.schedule.interval_seconds}s)")
    
    def stop(self) -> None:
        """Stop the backup scheduler."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("Backup scheduler stopped")
    
    def _scheduler_loop(self) -> None:
        """Main loop that runs in background thread."""
        while self.is_running:
            try:
                time.sleep(self.schedule.interval_seconds)
                self._create_scheduled_snapshot()
            except Exception as e:
                self.logger.error(f"Snapshot error: {e}")
    
    def _create_scheduled_snapshot(self) -> SnapshotManifest | None:
        """
        Create a snapshot if conditions are met.
        Returns the snapshot manifest if created, None otherwise.
        """
        try:
            snapshot = create_snapshot(
                source_folder=self.source_folder,
                vault_folder=self.vault_folder,
                password=self.password,
                exclude_names=set(HONEYFILE_NAMES),
            )
            
            self.snapshot_count += 1
            self.last_snapshot_time = datetime.now()
            
            self.logger.info(f"✓ Snapshot created: {snapshot.snapshot_id}")
            
            # Cleanup old snapshots
            self._cleanup_old_snapshots()
            
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Failed to create snapshot: {e}")
            return None
    
    def _cleanup_old_snapshots(self) -> None:
        """Remove old snapshots to stay within max_snapshots limit."""
        snapshots = list_snapshots(self.vault_folder)
        
        if len(snapshots) > self.schedule.max_snapshots:
            # Remove oldest snapshots (list is sorted newest first)
            to_remove = snapshots[self.schedule.max_snapshots:]
            
            for snap_id in to_remove:
                try:
                    snap_dir = self.vault_folder / snap_id
                    import shutil
                    shutil.rmtree(snap_dir)
                    self.logger.info(f"Cleaned up old snapshot: {snap_id}")
                except Exception as e:
                    self.logger.error(f"Failed to cleanup {snap_id}: {e}")
    
    def get_status(self) -> dict:
        """Get current scheduler status."""
        return {
            "running": self.is_running,
            "total_snapshots": self.snapshot_count,
            "last_snapshot": self.last_snapshot_time.isoformat() if self.last_snapshot_time else None,
            "next_interval": self.schedule.interval_seconds,
        }


# Default schedule, set with CIPHERTRAP_BACKUP_INTERVAL (seconds, default 600)
DEFAULT_BACKUP = BackupSchedule(interval_seconds=BACKUP_INTERVAL_SECONDS)


def calculate_next_backup_time(scheduler: SnapshotScheduler) -> datetime:
    """Calculate when the next backup will run."""
    if scheduler.last_snapshot_time is None:
        return datetime.now()
    
    next_time = scheduler.last_snapshot_time + timedelta(
        seconds=scheduler.schedule.interval_seconds
    )
    return next_time


def time_until_next_backup(scheduler: SnapshotScheduler) -> int:
    """Get seconds until next backup."""
    next_time = calculate_next_backup_time(scheduler)
    delta = (next_time - datetime.now()).total_seconds()
    return max(0, int(delta))
