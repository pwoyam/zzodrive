"""Local file index for zzoDrive.

Atomic writes + file lock to prevent corruption.
"""
import json
import os
import tempfile
import threading
import time
from pathlib import Path

from . import config

INDEX_FILE = config.CONFIG_DIR / "index.json"
_LOCK = threading.RLock()


def _ensure_dir():
    config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _backup_path():
    return INDEX_FILE.with_suffix(".json.bak")


def load():
    """Load the index. Returns {'files': [...]}."""
    with _LOCK:
        _ensure_dir()

        # try main file
        if INDEX_FILE.exists():
            try:
                with open(INDEX_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "files" in data:
                        return data
            except (json.JSONDecodeError, IOError) as e:
                print(f"[index] main file corrupt: {e}")

        # fallback to backup
        bak = _backup_path()
        if bak.exists():
            try:
                with open(bak, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "files" in data:
                        print("[index] restored from backup")
                        # restore main from backup
                        try:
                            os.replace(bak, INDEX_FILE)
                        except OSError:
                            pass
                        return data
            except (json.JSONDecodeError, IOError) as e:
                print(f"[index] backup corrupt: {e}")

        # nothing worked — start fresh
        return {"files": []}


def save(idx):
    """Atomic write + backup."""
    with _LOCK:
        _ensure_dir()

        # 1) write to temp file in same dir (same filesystem)
        fd, tmp_path = tempfile.mkstemp(
            prefix="index-", suffix=".json.tmp",
            dir=str(config.CONFIG_DIR),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(idx, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            # 2) backup current file if it exists
            if INDEX_FILE.exists():
                try:
                    os.replace(INDEX_FILE, _backup_path())
                except OSError:
                    pass

            # 3) atomic rename temp -> main
            os.replace(tmp_path, INDEX_FILE)
        except Exception:
            # cleanup temp
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise


def add(msg_id, name, size, remote_path=None, md5=None,
        encrypted=False, original_size=None, chunks=None):
    idx = load()
    idx["files"] = [f for f in idx["files"] if f["msg_id"] != msg_id]
    entry = {
        "msg_id": msg_id,
        "name": name,
        "size": size,
        "original_size": original_size if original_size is not None else size,
        "remote_path": remote_path or name,
        "md5": md5,
        "encrypted": encrypted,
        "uploaded_at": int(time.time()),
    }
    if chunks:
        entry["chunks"] = chunks
    idx["files"].append(entry)
    save(idx)


def remove(msg_id):
    with _LOCK:
        idx = load()
        idx["files"] = [f for f in idx["files"] if f["msg_id"] != msg_id]
        save(idx)


def find(msg_id):
    with _LOCK:
        for f in load()["files"]:
            if f["msg_id"] == msg_id:
                return f
        return None


def all_files():
    with _LOCK:
        return list(load()["files"])


def stats():
    with _LOCK:
        files = load()["files"]
        total = sum(f["size"] for f in files)
        enc = sum(1 for f in files if f.get("encrypted"))
        return {"count": len(files), "total_size": total, "encrypted": enc}
