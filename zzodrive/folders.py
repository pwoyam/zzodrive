"""Virtual folder management for zzoDrive.

Folders are virtual: they are derived from the remote_path of files.
Empty folders are tracked separately in ~/.zzodrive/folders.json.
"""
import json
from pathlib import Path

from . import config

FOLDERS_FILE = config.CONFIG_DIR / "folders.json"


def _load():
    if not FOLDERS_FILE.exists():
        return {"empty_folders": []}
    try:
        with open(FOLDERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"empty_folders": []}


def _save(data):
    with open(FOLDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_empty(name):
    """Register an empty folder."""
    name = name.strip("/")
    if not name:
        return
    data = _load()
    if name not in data["empty_folders"]:
        data["empty_folders"].append(name)
        _save(data)


def remove_empty(name):
    data = _load()
    data["empty_folders"] = [f for f in data["empty_folders"] if f != name]
    _save(data)


def rename_empty(old, new):
    data = _load()
    for i, f in enumerate(data["empty_folders"]):
        if f == old:
            data["empty_folders"][i] = new
        elif f.startswith(old + "/"):
            data["empty_folders"][i] = new + f[len(old):]
    _save(data)


def empty_folders():
    return _load()["empty_folders"]


def all_folders(file_paths):
    """Return a set of every folder path in the system."""
    folders = set()
    for rp in file_paths:
        rp = rp.strip("/")
        parts = rp.split("/")
        for i in range(1, len(parts)):
            folders.add("/".join(parts[:i]))
    for ef in empty_folders():
        ef = ef.strip("/")
        if not ef:
            continue
        folders.add(ef)
        parts = ef.split("/")
        for i in range(1, len(parts)):
            folders.add("/".join(parts[:i]))
    return folders


def children_of(prefix, file_paths):
    """Direct child folder names of `prefix` (one level, no nesting)."""
    prefix = (prefix or "").strip("/")
    all_f = all_folders(file_paths)
    children = set()
    for folder in all_f:
        if prefix:
            if not folder.startswith(prefix + "/"):
                continue
            rest = folder[len(prefix) + 1:]
        else:
            rest = folder
        if not rest:
            continue
        children.add(rest.split("/")[0])
    return sorted(children)


def files_in(prefix, files):
    """Return files directly inside `prefix` (not recursive)."""
    prefix = (prefix or "").strip("/")
    out = []
    for f in files:
        rp = f.get("remote_path", f["name"]).strip("/")
        if prefix:
            if not rp.startswith(prefix + "/"):
                continue
            rest = rp[len(prefix) + 1:]
        else:
            rest = rp
        if "/" not in rest:
            out.append(f)
    return out


def normalize(path):
    """Normalize a folder path (strip slashes, collapse '//')."""
    parts = [p for p in (path or "").split("/") if p]
    return "/".join(parts)
