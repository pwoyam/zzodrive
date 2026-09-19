"""Local file index for zzoDrive."""
import json
import time
from pathlib import Path

from . import config

INDEX_FILE = config.CONFIG_DIR / "index.json"


def load() -> dict:
    if not INDEX_FILE.exists():
        return {"files": []}
    try:
        with open(INDEX_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"files": []}


def save(idx: dict):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)


def add(msg_id, name, size, remote_path=None, md5=None,
        encrypted=False, original_size=None):
    idx = load()
    idx["files"] = [f for f in idx["files"] if f["msg_id"] != msg_id]
    idx["files"].append({
        "msg_id": msg_id,
        "name": name,
        "size": size,
        "original_size": original_size if original_size is not None else size,
        "remote_path": remote_path or name,
        "md5": md5,
        "encrypted": encrypted,
        "uploaded_at": int(time.time()),
    })
    save(idx)


def remove(msg_id):
    idx = load()
    idx["files"] = [f for f in idx["files"] if f["msg_id"] != msg_id]
    save(idx)


def find(msg_id):
    for f in load()["files"]:
        if f["msg_id"] == msg_id:
            return f
    return None


def all_files():
    return load()["files"]


def stats():
    files = all_files()
    total = sum(f["size"] for f in files)
    enc = sum(1 for f in files if f.get("encrypted"))
    return {
        "count": len(files),
        "total_size": total,
        "encrypted": enc,
    }
