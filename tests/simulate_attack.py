"""
Ransomware behaviour simulator for CipherTrap demonstrations.

Only runs on a demo folder. The folder must either not exist yet (it will be
created with a marker file) or already contain the marker file. Any other
folder is refused, so real files cannot be encrypted by accident.

Usage:
    python tests/simulate_attack.py demo_folder
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

DEMO_MARKER = ".ciphertrap_demo"
HONEYFILE_NAMES = ["passwords_backup.txt", "financial_records_2024.xlsx"]


def encrypt_file(file_path: Path, key: bytes) -> None:
    """Encrypt a file in place with AES-256-GCM and discard the key."""
    plaintext = file_path.read_bytes()
    nonce = os.urandom(12)
    encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend()).encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    file_path.write_bytes(nonce + encryptor.tag + ciphertext)


def prepare_demo_folder(folder: Path) -> None:
    """Create the demo folder, or confirm an existing one is a demo folder."""
    marker = folder / DEMO_MARKER
    if folder.exists() and not marker.exists():
        sys.exit(f"Refusing to run: {folder} is not a demo folder (missing {DEMO_MARKER}).")
    folder.mkdir(parents=True, exist_ok=True)
    marker.touch()


def create_victim_files(folder: Path, count: int = 15) -> list[Path]:
    files = []
    for i in range(count):
        path = folder / f"document_{i}.txt"
        path.write_text(f"Important document #{i}\nThis is critical business data.\n" * 3)
        files.append(path)
    return files


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: python tests/simulate_attack.py demo_folder")

    folder = Path(sys.argv[1]).expanduser().resolve()
    prepare_demo_folder(folder)

    # A fresh random key per run, never stored. Without it the files cannot be
    # decrypted, which is why recovery must come from the vault snapshot.
    key = os.urandom(32)

    victims = create_victim_files(folder)
    print(f"[SETUP] Created {len(victims)} files in {folder}")
    time.sleep(1)

    # Phase 1: a small legitimate edit (low risk)
    victims[0].write_text(victims[0].read_text() + "\nSmall update.\n")
    time.sleep(1)

    # Phase 2: touch honeyfiles if they exist (high risk)
    for name in HONEYFILE_NAMES:
        honeyfile = folder / name
        if honeyfile.exists():
            encrypt_file(honeyfile, key)
            print(f"[ALERT] Honeyfile modified: {name}")
            time.sleep(0.3)

    # Phase 3: mass encryption of victim files
    encrypted = 0
    for path in victims[:10]:
        encrypt_file(path, key)
        encrypted += 1
        time.sleep(0.1)
    print(f"[ATTACK] {encrypted} files encrypted with AES-256-GCM")

    # Show what an attacker leaves behind
    for path in victims[:2]:
        print(f"  {path.name}: {path.read_bytes()[:20].hex()}...")

    print("[COMPLETE] Run recovery_my_files.py with a snapshot ID to restore.")


if __name__ == "__main__":
    main()
