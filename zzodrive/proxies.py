"""Saved proxies management (like Telegram)."""
import json
import secrets
import time
from pathlib import Path

from . import config

PROXIES_FILE = config.CONFIG_DIR / "proxies.json"


def _load():
    if not PROXIES_FILE.exists():
        return {"proxies": []}
    try:
        with open(PROXIES_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"proxies": []}


def _save(data):
    PROXIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROXIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    try:
        PROXIES_FILE.chmod(0o600)
    except OSError:
        pass


def list_all():
    """Return saved proxies with 'active' flag. Order is stable."""
    data = _load()
    active_url = config.get("ZZODRIVE_PROXY") or ""
    enabled = config.get("ZZODRIVE_PROXY_ENABLED")
    if enabled is None:
        enabled = "1" if active_url else "0"
    is_on = enabled in ("1", "true", "True", "yes")

    out = []
    for p in data["proxies"]:
        item = dict(p)
        item["active"] = (p["url"] == active_url) and is_on
        out.append(item)
    # keep original order (by created_at ascending — oldest first)
    out.sort(key=lambda x: x.get("created_at", 0))
    return out


def add(name, url):
    """Add a new proxy. Returns the created entry."""
    name = (name or "").strip() or "Proxy"
    url = (url or "").strip()
    if not url:
        raise ValueError("Proxy URL is required")

    data = _load()

    # avoid exact duplicates
    for p in data["proxies"]:
        if p["url"] == url:
            p["name"] = name
            _save(data)
            return p

    entry = {
        "id": secrets.token_urlsafe(8),
        "name": name,
        "url": url,
        "created_at": int(time.time()),
    }
    data["proxies"].append(entry)
    _save(data)
    return entry


def remove(proxy_id):
    data = _load()
    before = len(data["proxies"])
    data["proxies"] = [p for p in data["proxies"] if p["id"] != proxy_id]
    _save(data)

    # if the removed one was active, clear active
    active_url = config.get("ZZODRIVE_PROXY") or ""
    urls = {p["url"] for p in data["proxies"]}
    if active_url and active_url not in urls:
        config.set_many({
            "ZZODRIVE_PROXY": "",
            "ZZODRIVE_PROXY_ENABLED": "0",
        })

    return before > len(data["proxies"])


def activate(proxy_id):
    """Activate a saved proxy."""
    data = _load()
    for p in data["proxies"]:
        if p["id"] == proxy_id:
            # atomic write of both keys
            config.set_many({
                "ZZODRIVE_PROXY": p["url"],
                "ZZODRIVE_PROXY_ENABLED": "1",
            })
            print(f"[proxies] activated: {p['name']} -> {p['url'][:40]}...")
            return p
    return None


def deactivate_all():
    """Turn off proxy without deleting."""
    config.set_value("ZZODRIVE_PROXY_ENABLED", "0")


def get_active():
    url = config.get("ZZODRIVE_PROXY") or ""
    enabled = config.get("ZZODRIVE_PROXY_ENABLED")
    if enabled is None:
        enabled = "1" if url else "0"
    is_on = enabled in ("1", "true", "True", "yes")
    for p in _load()["proxies"]:
        if p["url"] == url:
            item = dict(p)
            item["active"] = is_on
            return item
    return None
