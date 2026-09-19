"""End-to-end encryption for zzoDrive.

File format (v2):
    [MAGIC:8][VERSION:1][SALT:16][IV:16][HMAC:32][ciphertext...]

- MAGIC: b"ZZODRV2\\x00"
- VERSION: b"\\x02"
- SALT: random 16 bytes (unique per file)
- IV: random 16 bytes
- HMAC: SHA-256 over (MAGIC + VERSION + SALT + IV + ciphertext)
- ciphertext: AES-256-CTR

Key derivation:
    master = PBKDF2-HMAC-SHA256(password, salt, iterations=600_000, dklen=32)
    aes_key = HKDF-SHA256(master, info=b"zzoDrive-aes-v2", length=32)
    hmac_key = HKDF-SHA256(master, info=b"zzoDrive-hmac-v2", length=32)

Legacy v1 files (MAGIC="ZZODRV1\\x00") are still readable.
"""
import secrets
from pathlib import Path

from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# v2
MAGIC_V2 = b"ZZODRV2\x00"
VERSION_V2 = b"\x02"

# v1 (legacy)
MAGIC_V1 = b"ZZODRV1\x00"

IV_LEN = 16
SALT_LEN = 16
HMAC_LEN = 32
CHUNK = 1024 * 1024

PBKDF2_ITER_V2 = 600_000
PBKDF2_ITER_V1 = 200_000

# Public alias (for checking if a file is encrypted)
MAGIC = MAGIC_V2


def _derive_keys_v2(password: str, salt: bytes):
    """Return (aes_key, hmac_key) for v2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITER_V2,
    )
    master = kdf.derive(password.encode("utf-8"))

    aes_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"zzoDrive-aes-v2",
    ).derive(master)

    hmac_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"zzoDrive-hmac-v2",
    ).derive(master)

    return aes_key, hmac_key


def _derive_key_v1(password: str, salt: bytes) -> bytes:
    """Legacy v1 key derivation (uses same key for AES & HMAC)."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITER_V1,
    )
    return kdf.derive(password.encode("utf-8"))


# Legacy v1 helper — kept for backward compatibility
from . import config  # noqa: E402


def derive_key(password: str) -> bytes:
    """LEGACY: v1 key derivation using local salt. Do not use for new files."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=config.get_salt(),
        iterations=PBKDF2_ITER_V1,
    )
    return kdf.derive(password.encode("utf-8"))


# ---------- Encrypt (v2) ----------

def encrypt_file(input_path: Path, output_path: Path, password: str):
    """Encrypt input_path -> output_path (v2 format)."""
    salt = secrets.token_bytes(SALT_LEN)
    iv = secrets.token_bytes(IV_LEN)

    aes_key, hmac_key = _derive_keys_v2(password, salt)

    enc = Cipher(algorithms.AES(aes_key), modes.CTR(iv)).encryptor()
    mac = hmac.HMAC(hmac_key, hashes.SHA256())

    with open(input_path, "rb") as fin, open(output_path, "wb") as fout:
        # write header
        fout.write(MAGIC_V2)
        fout.write(VERSION_V2)
        fout.write(salt)
        fout.write(iv)
        hmac_pos = fout.tell()
        fout.write(b"\x00" * HMAC_LEN)  # placeholder

        # HMAC covers MAGIC+VERSION+SALT+IV
        mac.update(MAGIC_V2)
        mac.update(VERSION_V2)
        mac.update(salt)
        mac.update(iv)

        # encrypt body
        while True:
            chunk = fin.read(CHUNK)
            if not chunk:
                break
            ct = enc.update(chunk)
            if ct:
                mac.update(ct)
                fout.write(ct)
        final = enc.finalize()
        if final:
            mac.update(final)
            fout.write(final)

        # write MAC
        mac_val = mac.finalize()
        fout.seek(hmac_pos)
        fout.write(mac_val)


# ---------- Decrypt (auto-detect v1/v2) ----------

def decrypt_file(input_path: Path, output_path: Path, password: str):
    """Decrypt a file. Auto-detects v1 (legacy) or v2 format."""
    with open(input_path, "rb") as f:
        magic = f.read(len(MAGIC_V2))

    if magic == MAGIC_V2:
        _decrypt_v2(input_path, output_path, password)
    elif magic == MAGIC_V1:
        _decrypt_v1(input_path, output_path, password)
    else:
        raise ValueError("Not a zzoDrive encrypted file")


def _decrypt_v2(input_path: Path, output_path: Path, password: str):
    with open(input_path, "rb") as f:
        magic = f.read(len(MAGIC_V2))
        version = f.read(1)
        salt = f.read(SALT_LEN)
        iv = f.read(IV_LEN)
        stored_mac = f.read(HMAC_LEN)
        if len(salt) != SALT_LEN or len(iv) != IV_LEN or len(stored_mac) != HMAC_LEN:
            raise ValueError("Truncated encrypted file (v2)")

    if version != VERSION_V2:
        raise ValueError(f"Unsupported v2 version byte: {version!r}")

    aes_key, hmac_key = _derive_keys_v2(password, salt)

    # verify HMAC first
    mac = hmac.HMAC(hmac_key, hashes.SHA256())
    mac.update(magic)
    mac.update(version)
    mac.update(salt)
    mac.update(iv)
    with open(input_path, "rb") as f:
        f.seek(len(MAGIC_V2) + 1 + SALT_LEN + IV_LEN + HMAC_LEN)
        while True:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            mac.update(chunk)
    mac.verify(stored_mac)  # raises InvalidSignature if tampered

    # decrypt
    dec = Cipher(algorithms.AES(aes_key), modes.CTR(iv)).decryptor()
    with open(input_path, "rb") as fin, open(output_path, "wb") as fout:
        fin.seek(len(MAGIC_V2) + 1 + SALT_LEN + IV_LEN + HMAC_LEN)
        while True:
            chunk = fin.read(CHUNK)
            if not chunk:
                break
            fout.write(dec.update(chunk))
        fout.write(dec.finalize())


def _decrypt_v1(input_path: Path, output_path: Path, password: str):
    """Decrypt legacy v1 files (uses local salt from config)."""
    with open(input_path, "rb") as f:
        f.read(len(MAGIC_V1))  # magic
        iv = f.read(IV_LEN)
        stored_mac = f.read(HMAC_LEN)
        if len(iv) != IV_LEN or len(stored_mac) != HMAC_LEN:
            raise ValueError("Truncated encrypted file (v1)")

    key = _derive_key_v1(password, config.get_salt())

    # verify
    mac = hmac.HMAC(key, hashes.SHA256())
    with open(input_path, "rb") as f:
        f.seek(len(MAGIC_V1) + IV_LEN + HMAC_LEN)
        while True:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            mac.update(chunk)
    mac.verify(stored_mac)

    # decrypt
    dec = Cipher(algorithms.AES(key), modes.CTR(iv)).decryptor()
    with open(input_path, "rb") as fin, open(output_path, "wb") as fout:
        fin.seek(len(MAGIC_V1) + IV_LEN + HMAC_LEN)
        while True:
            chunk = fin.read(CHUNK)
            if not chunk:
                break
            fout.write(dec.update(chunk))
        fout.write(dec.finalize())


# ---------- Helpers ----------

def is_encrypted(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            head = f.read(len(MAGIC_V2))
            return head == MAGIC_V2 or head == MAGIC_V1
    except OSError:
        return False


def detect_version(path: Path):
    """Return 1, 2, or None."""
    try:
        with open(path, "rb") as f:
            head = f.read(len(MAGIC_V2))
        if head == MAGIC_V2:
            return 2
        if head == MAGIC_V1:
            return 1
        return None
    except OSError:
        return None
