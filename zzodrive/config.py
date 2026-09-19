"""Configuration management for zzoDrive."""
import os
import secrets
from pathlib import Path

CONFIG_DIR = Path.home() / ".zzodrive"
CONFIG_FILE = CONFIG_DIR / "config.env"
SALT_FILE = CONFIG_DIR / "salt.bin"

DEFAULT_API_ID = 2040
DEFAULT_API_HASH = "b18441a1ff607e10a989891a5462e627"


def ensure_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        CONFIG_DIR.chmod(0o700)
    except OSError:
        pass


def load():
    """Load config as dict."""
    ensure_dir()
    cfg = {}
    if CONFIG_FILE.exists():
        for line in CONFIG_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            cfg[k.strip()] = v.strip().strip("'\"")
    return cfg


def save(cfg):
    """Save config dict to file."""
    ensure_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        for k, v in cfg.items():
            f.write(f"{k}='{v}'\n")
    try:
        CONFIG_FILE.chmod(0o600)
    except OSError:
        pass


def get(key, default=None):
    return load().get(key) or os.environ.get(key) or default


def set_value(key, value):
    cfg = load()
    cfg[key] = value
    save(cfg)


def delete(key):
    cfg = load()
    cfg.pop(key, None)
    save(cfg)


def get_salt():
    ensure_dir()
    if not SALT_FILE.exists():
        SALT_FILE.write_bytes(secrets.token_bytes(16))
        try:
            SALT_FILE.chmod(0o600)
        except OSError:
            pass
    return SALT_FILE.read_bytes()


def is_configured():
    cfg = load()
    return bool(cfg.get("ZZODRIVE_BOT_TOKEN")) and bool(cfg.get("ZZODRIVE_CHANNEL_ID"))
