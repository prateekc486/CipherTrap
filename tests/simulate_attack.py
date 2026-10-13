"""
Ransomware-behavior simulator for CipherTrap demonstrations.

IMPORTANT: This operates ONLY inside a temporary/demo directory that you
point it at. It never touches real files outside that folder. It simulates
real ransomware behavior by:
  1. Encrypting files with AES-256-GCM (actual encryption)
  2. Tampering with honeyfiles (high-risk detection trigger)
  3. Rapid file modifications and mass encryption patterns

After running this, files are genuinely encrypted. Use CipherTrap recovery
to restore them and show the judges data protection in action.

Usage:
    python tests/simulate_attack.py /path/to/demo_folder [--encryption-key YOUR_KEY]
"""

from __future__ import annotations

import os
import sys
import time
import hashlib
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


# Simple AES-256-GCM encryption (ransomware-like)
def encrypt_file_aes(file_path: Path, encryption_key: bytes = None) -> None:
    """Encrypt a file with AES-256-GCM (mimics real ransomware encryption)."""
    if encryption_key is None:
        # Default demo key - exactly 32 bytes for AES-256
        encryption_key = b"demo_ransomware_key_32_bytes_123"
    
    try:
        plaintext = file_path.read_bytes()
        
        # Generate random 12-byte nonce
        nonce = os.urandom(12)
        
        # AES-256-GCM encryption
        cipher = Cipher(
            algorithms.AES(encryption_key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        # Write nonce + tag + ciphertext back to file
        encrypted_data = nonce + encryptor.tag + ciphertext
        file_path.write_bytes(encrypted_data)
    except Exception as e:
        print(f"    [!] Encryption error on {file_path.name}: {e}")


def populate_dummy_files(folder: Path, count: int = 15) -> list[Path]:
    """Create harmless dummy text files to act as 'victim' files."""
    files = []
    for i in range(count):
        f = folder / f"document_{i}.txt"
        f.write_text(f"Important document #{i}\nThis is critical business data.\n" * 3)
        files.append(f)
    return files


def simulate_normal_activity(files: list[Path]) -> None:
    """A couple of normal, low-risk file edits."""
    target = files[0]
    target.write_text(target.read_text() + "\nSmall update.\n")
    time.sleep(1)


def trip_honeyfiles(folder: Path) -> None:
    """Ransomware attack: modify/delete honeyfiles to trigger high-risk alert."""
    honeyfile_names = [
        "passwords_backup.txt",
        "financial_records_2024.xlsx",
        "id_documents_scan.pdf",
        "company_confidential.docx",
        "database_credentials.txt",
    ]

    for honey_name in honeyfile_names[:2]:
        honey_path = folder / honey_name
        if honey_path.exists():
            encrypt_file_aes(honey_path)
            time.sleep(0.3)


def simulate_mass_encryption(files: list[Path], encryption_key: bytes = None) -> int:
    """Bulk encryption of victim files (the main ransomware payload)."""
    if encryption_key is None:
        encryption_key = b"demo_ransomware_key_32_bytes_123"

    encrypted_count = 0
    for f in files[:10]:
        if f.exists():
            encrypt_file_aes(f, encryption_key)
            encrypted_count += 1
            time.sleep(0.1)
    return encrypted_count


def show_encrypted_damage(folder: Path) -> None:
    """Show the user the encrypted files (unreadable garbage)."""
    print("\n[ATTACK COMPLETE] Files encrypted with AES-256-GCM")
    text_files = sorted(folder.glob("document_*.txt"))[:2]

    for f in text_files:
        if f.exists():
            encrypted_data = f.read_bytes()[:50]
            print(f"  {f.name}: {encrypted_data.hex()[:40]}...")


def run_simulation(demo_folder: str, encryption_key: str = None) -> None:
    folder = Path(demo_folder).expanduser().resolve()
    if not folder.exists():
        folder.mkdir(parents=True)

    print(f"\n[RANSOMWARE SIMULATION] Target: {folder}")

    # Clear old demo files
    for old_file in folder.glob("document_*.txt"):
        old_file.unlink()
    for old_file in folder.glob("*.locked"):
        old_file.unlink()

    # Generate encryption key
    if encryption_key:
        key = hashlib.sha256(encryption_key.encode()).digest()[:32]
    else:
        key = b"demo_ransomware_key_32_bytes_123"  # Exactly 32 bytes

    # Create victim files
    files = populate_dummy_files(folder)
    print(f"[SETUP] Created {len(files)} files")
    time.sleep(1)

    # Run attack phases
    simulate_normal_activity(files)
    time.sleep(1)

    trip_honeyfiles(folder)
    time.sleep(1)

    encrypted = simulate_mass_encryption(files, key)
    time.sleep(1)

    show_encrypted_damage(folder)

    print(f"\n[COMPLETE] {encrypted} files encrypted with AES-256-GCM")
    print(f"Run: python recovery_my_files.py to restore files\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simulate_attack.py /path/to/demo_folder [--key ENCRYPTION_KEY]")
        sys.exit(1)
    
    demo_path = sys.argv[1]
    enc_key = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--key" else None
    
    run_simulation(demo_path, enc_key)
