"""
Simple attack test on a COPY of your important files.

Copies my_important_files/ to attack_test/, then encrypts every file in the
copy. Your original files in my_important_files/ are never modified.

Usage:
    python tests/attack_copy.py
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from simulate_attack import DEMO_MARKER, encrypt_file

TARGET = Path("attack_test")


def main() -> None:
    parser = argparse.ArgumentParser(description="Attack a copy of a folder (originals untouched).")
    parser.add_argument("folder", nargs="?", default="my_important_files", help="folder to copy and attack")
    args = parser.parse_args()
    SOURCE = Path(args.folder).expanduser().resolve()

    if not SOURCE.is_dir():
        sys.exit(f"Error: {SOURCE} not found. Create it and add a file first.")
    if SOURCE == TARGET.resolve():
        sys.exit("Error: choose your real folder, not the attack_test copy.")

    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET)
    (TARGET / DEMO_MARKER).touch()

    key = os.urandom(32)  # discarded after this run
    files = [p for p in TARGET.rglob("*") if p.is_file() and p.name != DEMO_MARKER]
    for path in files:
        encrypt_file(path, key)
        print(f"[ATTACK] Encrypted copy: {path}")

    print(f"\nDone. {len(files)} copied file(s) encrypted in {TARGET}.")
    print(f"Your originals in {SOURCE} are untouched.")


if __name__ == "__main__":
    main()
