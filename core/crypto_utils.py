"""
Cryptography module for CipherTrap.

Provides:
- Argon2id-based key derivation from a user password
- AES-256-GCM authenticated encryption/decryption for files
- SHA-256 hashing helper for integrity checks

Design notes:
- Every encryption call generates a fresh random 12-byte nonce (never reused).
- AES-GCM gives both confidentiality AND integrity (authentication tag),
  so tampering with ciphertext is detected automatically on decrypt.
- The server/app never needs to store the plaintext password -- only the
  derived key lives in memory during a session, and the salt is stored
  alongside the encrypted data so the key can be re-derived later.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

from argon2.low_level import Type, hash_secret_raw
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# --- Argon2id parameters ---
# These are reasonable defaults for a desktop app (not a high-throughput
# server). Tune time_cost/memory_cost down only if target hardware is weak.
ARGON2_TIME_COST = 3          # number of iterations
ARGON2_MEMORY_COST = 65536    # 64 MB
ARGON2_PARALLELISM = 4
ARGON2_KEY_LEN = 32           # 256-bit key for AES-256
ARGON2_SALT_LEN = 16
AES_NONCE_LEN = 12            # recommended nonce size for AES-GCM


class DecryptionError(Exception):
    """Raised when decryption fails due to tampering or a wrong key."""


@dataclass(frozen=True, slots=True)
class EncryptedPayload:
    """Container for everything needed to decrypt a file later."""

    ciphertext: bytes   # includes the GCM authentication tag (appended by AESGCM)
    nonce: bytes
    salt: bytes

    def to_bytes(self) -> bytes:
        """
        Serialize as: [1 byte salt_len][salt][12 byte nonce][ciphertext+tag]
        A simple, dependency-free binary format suitable for writing to disk.
        """
        if len(self.salt) > 255:
            raise ValueError("salt too long to serialize with 1-byte length prefix")
        return bytes([len(self.salt)]) + self.salt + self.nonce + self.ciphertext

    @classmethod
    def from_bytes(cls, data: bytes) -> "EncryptedPayload":
        if len(data) < 1:
            raise ValueError("payload too short to contain a salt length byte")
        salt_len = data[0]
        offset = 1
        salt = data[offset: offset + salt_len]
        offset += salt_len
        nonce = data[offset: offset + AES_NONCE_LEN]
        offset += AES_NONCE_LEN
        ciphertext = data[offset:]
        if len(salt) != salt_len or len(nonce) != AES_NONCE_LEN:
            raise ValueError("payload is truncated or corrupted")
        return cls(ciphertext=ciphertext, nonce=nonce, salt=salt)


def generate_salt() -> bytes:
    """Generate a new random salt for Argon2id key derivation."""
    return os.urandom(ARGON2_SALT_LEN)


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit AES key from a password using Argon2id.

    The same password + salt will always produce the same key, so the
    salt must be stored (it's not secret) alongside the encrypted data
    to allow re-deriving the key later.
    """
    if not password:
        raise ValueError("password must not be empty")
    if len(salt) != ARGON2_SALT_LEN:
        raise ValueError(f"salt must be exactly {ARGON2_SALT_LEN} bytes")

    key = hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=ARGON2_KEY_LEN,
        type=Type.ID,  # Argon2id
    )
    return key


def encrypt_file(data: bytes, key: bytes, *, salt: bytes) -> EncryptedPayload:
    """
    Encrypt raw file bytes using AES-256-GCM.

    A fresh random nonce is generated for every call -- never reuse a
    nonce with the same key, as doing so breaks AES-GCM's security
    guarantees completely.
    """
    if len(key) != 32:
        raise ValueError("key must be 32 bytes (256 bits) for AES-256")

    nonce = os.urandom(AES_NONCE_LEN)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, data, associated_data=None)

    return EncryptedPayload(ciphertext=ciphertext, nonce=nonce, salt=salt)


def decrypt_file(payload: EncryptedPayload, key: bytes) -> bytes:
    """
    Decrypt an EncryptedPayload using AES-256-GCM.

    Raises DecryptionError if the ciphertext was tampered with, the wrong
    key was supplied, or the data is otherwise corrupted. This is the
    mechanism CipherTrap uses to detect tampered backups.
    """
    if len(key) != 32:
        raise ValueError("key must be 32 bytes (256 bits) for AES-256")

    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(payload.nonce, payload.ciphertext, associated_data=None)
    except InvalidTag as exc:
        raise DecryptionError(
            "Decryption failed: data has been tampered with, or the key/password is wrong."
        ) from exc

    return plaintext


def encrypt_file_with_password(data: bytes, password: str) -> bytes:
    """
    Convenience wrapper: derive a key from a password and encrypt in one
    call. Returns a self-contained serialized blob (salt+nonce+ciphertext)
    that can be written straight to disk.
    """
    salt = generate_salt()
    key = derive_key(password, salt)
    payload = encrypt_file(data, key, salt=salt)
    return payload.to_bytes()


def decrypt_file_with_password(blob: bytes, password: str) -> bytes:
    """
    Convenience wrapper: parse a serialized blob, re-derive the key from
    the password using the embedded salt, and decrypt.
    """
    payload = EncryptedPayload.from_bytes(blob)
    key = derive_key(password, payload.salt)
    return decrypt_file(payload, key)


def sha256_hash(data: bytes) -> str:
    """Return the hex-encoded SHA-256 hash of the given bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_hash_file(path: str) -> str:
    """Compute the SHA-256 hash of a file on disk, streaming in chunks."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()
