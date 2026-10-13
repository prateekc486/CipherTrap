"""
Unit Tests for CipherTrap - Ransomware Detection & Recovery System.

Test coverage:
- Honeyfile deployment and integrity checking
- Snapshot creation and recovery
- Encryption/decryption
- Risk scoring
- Threat intelligence detection
- Auto-backup scheduling
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.honeyfiles import deploy_honeyfiles, check_honeyfile_integrity, is_honeyfile
from core.snapshot import create_snapshot
from core.recovery import restore_snapshot
from core.crypto_utils import encrypt_file_with_password, decrypt_file_with_password
from core.threat_intelligence import detect_malware_signature, analyze_file_entropy
from core.auto_backup import BackupSchedule, SnapshotScheduler


class TestHoneyfiles:
    """Test honeyfile deployment and detection."""
    
    def test_deploy_honeyfiles(self):
        """Test honeyfile creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            honeys = deploy_honeyfiles(tmpdir, count=3)
            assert len(honeys) == 3
            
            for honey in honeys:
                assert honey.path.exists()
                assert honey.original_hash is not None
                assert len(honey.original_hash) == 64  # SHA-256
    
    def test_honeyfile_integrity_check(self):
        """Test detection of honeyfile tampering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            honeys = deploy_honeyfiles(tmpdir, count=1)
            honey = honeys[0]
            
            # Should pass initially
            assert check_honeyfile_integrity(honey) is True
            
            # Modify the honeyfile
            honey.path.write_text("TAMPERED!")
            
            # Should fail now
            assert check_honeyfile_integrity(honey) is False
    
    def test_is_honeyfile(self):
        """Test honeyfile identification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            honeys = deploy_honeyfiles(tmpdir, count=1)
            regular_file = Path(tmpdir) / "regular.txt"
            regular_file.write_text("Normal file")
            
            assert is_honeyfile(honeys[0].path, honeys) is True
            assert is_honeyfile(regular_file, honeys) is False


class TestEncryption:
    """Test encryption and decryption."""
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption followed by decryption returns original."""
        plaintext = b"This is secret data!"
        password = "test_password_123"
        
        encrypted = encrypt_file_with_password(plaintext, password)
        decrypted = decrypt_file_with_password(encrypted, password)
        
        assert decrypted == plaintext
    
    def test_decrypt_wrong_password(self):
        """Test that wrong password fails to decrypt."""
        plaintext = b"Secret message"
        password = "correct_password"
        wrong_password = "wrong_password"
        
        encrypted = encrypt_file_with_password(plaintext, password)
        
        with pytest.raises(Exception):  # Should fail
            decrypt_file_with_password(encrypted, wrong_password)
    
    def test_encryption_produces_different_output(self):
        """Test that same plaintext encrypts differently each time (nonce)."""
        plaintext = b"Same data"
        password = "password"
        
        encrypted1 = encrypt_file_with_password(plaintext, password)
        encrypted2 = encrypt_file_with_password(plaintext, password)
        
        assert encrypted1 != encrypted2  # Different due to nonce


class TestSnapshot:
    """Test snapshot creation and restoration."""
    
    def test_create_snapshot(self):
        """Test snapshot creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            vault = Path(tmpdir) / "vault"
            source.mkdir()
            vault.mkdir()
            
            # Create test files
            (source / "file1.txt").write_text("Content 1")
            (source / "file2.txt").write_text("Content 2")
            
            snapshot = create_snapshot(source, vault, "password")
            
            assert snapshot.snapshot_id is not None
            assert len(snapshot.files) == 2
            assert "file1.txt" in snapshot.files
            assert "file2.txt" in snapshot.files
    
    def test_restore_snapshot(self):
        """Test snapshot restoration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            vault = Path(tmpdir) / "vault"
            restore = Path(tmpdir) / "restored"
            source.mkdir()
            vault.mkdir()
            restore.mkdir()
            
            # Create and backup files
            (source / "doc.txt").write_text("Original content")
            snapshot = create_snapshot(source, vault, "password")
            
            # Restore
            result = restore_snapshot(vault, snapshot.snapshot_id, restore, "password")
            
            assert len(result.restored_files) == 1
            assert len(result.failed_files) == 0
            assert (restore / "doc.txt").read_text() == "Original content"


class TestThreatIntelligence:
    """Test malware detection."""
    
    def test_detect_no_malware(self):
        """Test when no malware is detected."""
        result = detect_malware_signature([], [], [])
        
        assert len(result.detected_malware) == 0
        assert result.severity == 0.0
    
    def test_entropy_analysis(self):
        """Test file entropy calculation."""
        # Low entropy (plaintext)
        plaintext = b"Hello world" * 10
        entropy_plain = analyze_file_entropy(plaintext)
        
        # High entropy (random)
        import random
        random_data = bytes([random.randint(0, 255) for _ in range(1000)])
        entropy_random = analyze_file_entropy(random_data)
        
        assert entropy_random > entropy_plain
        assert entropy_plain < 0.5
        assert entropy_random > 0.7


class TestAutoBackup:
    """Test automatic backup scheduling."""
    
    def test_backup_schedule_creation(self):
        """Test schedule initialization."""
        schedule = BackupSchedule(interval_seconds=3600, max_snapshots=10)
        
        assert schedule.interval_seconds == 3600
        assert schedule.max_snapshots == 10
    
    def test_scheduler_initialization(self):
        """Test scheduler creation."""
        schedule = BackupSchedule(interval_seconds=3600)
        scheduler = SnapshotScheduler(schedule)
        
        assert scheduler.is_running is False
        assert scheduler.snapshot_count == 0
    
    def test_scheduler_get_status(self):
        """Test scheduler status reporting."""
        schedule = BackupSchedule(interval_seconds=3600)
        scheduler = SnapshotScheduler(schedule)
        
        status = scheduler.get_status()
        
        assert "running" in status
        assert "total_snapshots" in status
        assert status["total_snapshots"] == 0


class TestIntegration:
    """Integration tests for full workflow."""
    
    def test_full_protection_workflow(self):
        """Test: Deploy honeyfiles -> Create snapshot -> "Modify files" -> Restore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "protected"
            vault = Path(tmpdir) / "vault"
            restored = Path(tmpdir) / "restored"
            
            source.mkdir()
            vault.mkdir()
            restored.mkdir()
            
            # Step 1: Deploy honeyfiles
            honeys = deploy_honeyfiles(source, count=2)
            assert len(honeys) == 2
            
            # Step 2: Create clean backup
            (source / "important.txt").write_text("Critical data")
            snapshot = create_snapshot(source, vault, "secret_pass")
            assert len(snapshot.files) >= 1
            
            # Step 3: "Ransomware" modifies files
            (source / "important.txt").write_text("ENCRYPTED_GARBAGE_12345")
            honeys[0].path.write_text("CORRUPTED")
            
            # Step 4: Detect tampering
            assert check_honeyfile_integrity(honeys[0]) is False
            
            # Step 5: Restore from backup
            result = restore_snapshot(vault, snapshot.snapshot_id, restored, "secret_pass")
            assert len(result.restored_files) > 0
            assert (restored / "important.txt").read_text() == "Critical data"


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
