"""
Runtime settings for CipherTrap.

Nothing secret is stored in the code. The vault password comes from the
CIPHERTRAP_VAULT_PASSWORD environment variable, or is prompted for when
running in a terminal. Other settings are optional environment variables
with sensible defaults.
"""

from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

VAULT_DIR = Path(os.environ.get("CIPHERTRAP_VAULT_DIR", PROJECT_ROOT / "vault"))
LOG_DIR = Path(os.environ.get("CIPHERTRAP_LOG_DIR", PROJECT_ROOT / "logs"))
BACKUP_INTERVAL_SECONDS = int(os.environ.get("CIPHERTRAP_BACKUP_INTERVAL", "600"))
MAX_SNAPSHOTS = int(os.environ.get("CIPHERTRAP_MAX_SNAPSHOTS", "10"))

PASSWORD_ENV_VAR = "CIPHERTRAP_VAULT_PASSWORD"


def get_vault_password() -> str:
    """Return the vault password from the environment, or prompt for it."""
    password = os.environ.get(PASSWORD_ENV_VAR)
    if password:
        return password

    if not sys.stdin.isatty():
        raise SystemExit(f"Set the {PASSWORD_ENV_VAR} environment variable first.")

    password = getpass.getpass("Vault password: ")
    if not password:
        raise SystemExit("Password cannot be empty.")
    return password
