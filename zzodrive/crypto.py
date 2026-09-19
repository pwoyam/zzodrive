"""End-to-end encryption for zzoDrive."""
import secrets
from pathlib import Path

from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from . import config

MAGIC = b"ZZODRV1\x00"
IV_LEN = 16
HMAC_LEN = 32
CHUNK = 1024 * 1024


def derive_key(password: str) -> bytes:
    """Derive 32-byte AES key from password."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=config.get_salt(),
        iterations=200_000,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_file(input_path: Path, output_path: Path, key: bytes):
    """Encrypt input_path -> output_path (AES-256-CTR + HMAC-SHA256)."""
    iv = secrets.token_bytes(IV_LEN)
    enc = Cipher(algorithms.AES(key), modes.CTR(iv)).encryptor()
    mac = hmac.HMAC(key, hashes.SHA256())

    with open(input_path, "rb") as fin, open(output_path, "wb") as fout:
        fout.write(MAGIC)
        fout.write(iv)
        pos = fout.tell()
        fout.write(b"\x00" * HMAC_LEN)

        while True:
            c = fin.read(CHUNK)
            if not c:
                break
            ct = enc.update(c)
            if ct:
                mac.update(ct)
                fout.write(ct)

        final = enc.finalize()
        if final:
            mac.update(final)
            fout.write(final)

        mv = mac.finalize()
        fout.seek(pos)
        fout.write(mv)


def decrypt_file(input_path: Path, output_path: Path, key: bytes):
    """Verify HMAC then decrypt."""
    with open(input_path, "rb") as f:
        if f.read(len(MAGIC)) != MAGIC:
            raise ValueError("Not a zzoDrive encrypted file")
        iv = f.read(IV_LEN)
        stored_mac = f.read(HMAC_LEN)

    mac = hmac.HMAC(key, hashes.SHA256())
    with open(input_path, "rb") as f:
        f.seek(len(MAGIC) + IV_LEN + HMAC_LEN)
        while True:
            c = f.read(CHUNK)
            if not c:
                break
            mac.update(c)
    mac.verify(stored_mac)

    dec = Cipher(algorithms.AES(key), modes.CTR(iv)).decryptor()
    with open(input_path, "rb") as fin, open(output_path, "wb") as fout:
        fin.seek(len(MAGIC) + IV_LEN + HMAC_LEN)
        while True:
            c = fin.read(CHUNK)
            if not c:
                break
            fout.write(dec.update(c))
        fout.write(dec.finalize())


def is_encrypted(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(len(MAGIC)) == MAGIC
    except OSError:
        return False
