"""BBH Founder Vault: authenticated file encryption."""

import os
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


MAGIC = b"BBHFV1"
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
HEADER_SIZE = len(MAGIC) + SALT_SIZE + NONCE_SIZE


class VaultError(Exception):
    """Base exception for Vault operations."""


class InvalidVaultFile(VaultError):
    """The file is malformed or has an unsupported format."""


def _validate_password(password):
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("Vault passphrase must contain at least 12 characters.")
    return password.encode("utf-8")


def _derive_key(password_bytes, salt):
    kdf = Scrypt(
        salt=salt,
        length=KEY_SIZE,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
    )
    return kdf.derive(password_bytes)


def encrypt_bytes(data, password):
    """Encrypt bytes using AES-256-GCM."""
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")

    password_bytes = _validate_password(password)
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)

    header = MAGIC + salt + nonce
    key = _derive_key(password_bytes, salt)

    ciphertext = AESGCM(key).encrypt(nonce, data, header)
    return header + ciphertext


def decrypt_bytes(encrypted, password):
    """Authenticate and decrypt a Vault payload."""
    if not isinstance(encrypted, bytes):
        raise TypeError("encrypted data must be bytes")

    if len(encrypted) < HEADER_SIZE + 16:
        raise InvalidVaultFile("Encrypted file is too short.")

    if encrypted[:len(MAGIC)] != MAGIC:
        raise InvalidVaultFile("Unknown Vault file format.")

    password_bytes = _validate_password(password)

    offset = len(MAGIC)
    salt = encrypted[offset:offset + SALT_SIZE]
    offset += SALT_SIZE

    nonce = encrypted[offset:offset + NONCE_SIZE]
    header = encrypted[:HEADER_SIZE]
    ciphertext = encrypted[HEADER_SIZE:]

    key = _derive_key(password_bytes, salt)

    try:
        return AESGCM(key).decrypt(nonce, ciphertext, header)
    except InvalidTag as exc:
        raise VaultError(
            "Authentication failed: wrong passphrase or modified file."
        ) from exc


def _write_new_file(path, data):
    """Create a new private file; never overwrite an existing file."""
    path = Path(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(str(path), flags, 0o600)

    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def encrypt_file(source, destination, password):
    source = Path(source)
    destination = Path(destination)

    if destination.exists():
        raise FileExistsError(destination)

    encrypted = encrypt_bytes(source.read_bytes(), password)
    _write_new_file(destination, encrypted)
    return destination


def decrypt_file(source, destination, password):
    source = Path(source)
    destination = Path(destination)

    if destination.exists():
        raise FileExistsError(destination)

    plaintext = decrypt_bytes(source.read_bytes(), password)
    _write_new_file(destination, plaintext)
    return destination
