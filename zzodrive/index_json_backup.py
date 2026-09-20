"""Local file index using SQLite with WAL mode.

Keeps the same API as the old JSON-based index:
    load, save, add, remove, find, all_files, stats
"""
import json
import os
import sqlite3
import threading
import time
from pathlib import Path

from . import config

INDEX_DB = config.CONFIG_DIR / "index.db"
INDEX_JSON = config.CONFIG_DIR / "index.json"
_LOCK = threading.RLock()


def _ensure_dir():
    config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _connect():
    conn = sqlite3.connect(str(INDEX_DB), check_same_thread=False, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn


def _init_schema(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS files (
            msg_id        INTEGER PRIMARY KEY,
            name          TEXT    NOT NULL,
            size          INTEGER NOT NULL,
            original_size INTEGER,
            remote_path   TEXT,
            md5           TEXT,
            encrypted     INTEGER NOT NULL DEFAULT 0,
            uploaded_at   INTEGER NOT NULL,
            chunks        TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_name   ON files(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rpath  ON files(remote_path)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_up_at  ON files(uploaded_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_enc    ON files(encrypted)")
    conn.commit()


def _row_to_dict(row):
    if row is None:
        return None
    d = {
        "msg_id": row["msg_id"],
        "name": row["name"],
        "size": row["size"],
        "original_size": row["original_size"] if row["original_size"] is not None else row["size"],
        "remote_path": row["remote_path"] or row["name"],
        "md5": row["md5"],
        "encrypted": bool(row["encrypted"]),
        "uploaded_at": row["uploaded_at"],
    }
    if row["chunks"]:
        try:
            d["chunks"] = json.loads(row["chunks"])
        except (json.JSONDecodeError, TypeError):
            pass
    return d


def _migrate_from_json(conn):
    if not INDEX_JSON.exists():
        return
    cur = conn.execute("SELECT COUNT(*) AS n FROM files")
    if cur.fetchone()["n"] > 0:
        return
    try:
        with open(INDEX_JSON, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return
    files = data.get("files", [])
    if not files:
        return
    for f in files:
        chunks_json = None
        if f.get("chunks"):
            chunks_json = json.dumps(f["chunks"])
        conn.execute("""
            INSERT OR REPLACE INTO files
            (msg_id, name, size, original_size, remote_path, md5,
             encrypted, uploaded_at, chunks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f["msg_id"],
            f["name"],
            f["size"],
            f.get("original_size", f["size"]),
            f.get("remote_path", f["name"]),
            f.get("md5"),
            1 if f.get("encrypted") else 0,
            f.get("uploaded_at", int(time.time())),
            chunks_json,
        ))
    conn.commit()
    try:
        bak = INDEX_JSON.with_suffix(".json.migrated")
        INDEX_JSON.rename(bak)
    except OSError:
        pass
    print("[index] migrated " + str(len(files)) + " files from index.json to SQLite")


_initialized = False


def _get_conn():
    global _initialized
    _ensure_dir()
    conn = _connect()
    if not _initialized:
        _init_schema(conn)
        _migrate_from_json(conn)
        _initialized = True
    else:
        _init_schema(conn)
    return conn


def load():
    with _LOCK:
        conn = _get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM files ORDER BY uploaded_at ASC"
            ).fetchall()
            return {"files": [_row_to_dict(r) for r in rows]}
        finally:
            conn.close()


def save(idx):
    with _LOCK:
        conn = _get_conn()
        try:
            conn.execute("BEGIN")
            conn.execute("DELETE FROM files")
            for f in idx.get("files", []):
                chunks_json = None
                if f.get("chunks"):
                    chunks_json = json.dumps(f["chunks"])
                conn.execute("""
                    INSERT OR REPLACE INTO files
                    (msg_id, name, size, original_size, remote_path, md5,
                     encrypted, uploaded_at, chunks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f["msg_id"], f["name"], f["size"],
                    f.get("original_size", f["size"]),
                    f.get("remote_path", f["name"]),
                    f.get("md5"),
                    1 if f.get("encrypted") else 0,
                    f.get("uploaded_at", int(time.time())),
                    chunks_json,
                ))
            conn.commit()
        finally:
            conn.close()


def add(msg_id, name, size, remote_path=None, md5=None,
        encrypted=False, original_size=None, chunks=None):
    with _LOCK:
        conn = _get_conn()
        try:
            chunks_json = None
            if chunks:
                chunks_json = json.dumps(chunks)
            conn.execute("""
                INSERT OR REPLACE INTO files
                (msg_id, name, size, original_size, remote_path, md5,
                 encrypted, uploaded_at, chunks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                msg_id, name, size,
                original_size if original_size is not None else size,
                remote_path or name,
                md5,
                1 if encrypted else 0,
                int(time.time()),
                chunks_json,
            ))
            conn.commit()
        finally:
            conn.close()


def remove(msg_id):
    with _LOCK:
        conn = _get_conn()
        try:
            conn.execute("DELETE FROM files WHERE msg_id = ?", (msg_id,))
            conn.commit()
        finally:
            conn.close()


def find(msg_id):
    with _LOCK:
        conn = _get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM files WHERE msg_id = ?", (msg_id,)
            ).fetchone()
            return _row_to_dict(row)
        finally:
            conn.close()


def all_files():
    with _LOCK:
        return load()["files"]


def stats():
    with _LOCK:
        conn = _get_conn()
        try:
            row = conn.execute("""
                SELECT COUNT(*) AS n,
                       COALESCE(SUM(size), 0) AS total,
                       COALESCE(SUM(encrypted), 0) AS enc
                FROM files
            """).fetchone()
            return {
                "count": row["n"],
                "total_size": row["total"],
                "encrypted": row["enc"],
            }
        finally:
            conn.close()


def search(q):
    if not q:
        return all_files()
    like = "%" + q + "%"
    with _LOCK:
        conn = _get_conn()
        try:
            rows = conn.execute("""
                SELECT * FROM files
                WHERE name LIKE ? OR remote_path LIKE ?
                ORDER BY uploaded_at DESC
            """, (like, like)).fetchall()
            return [_row_to_dict(r) for r in rows]
        finally:
            conn.close()


def files_in_prefix(prefix):
    if prefix:
        pat = prefix.rstrip("/") + "/%"
    else:
        pat = "%"
    with _LOCK:
        conn = _get_conn()
        try:
            rows = conn.execute("""
                SELECT * FROM files
                WHERE remote_path LIKE ?
                ORDER BY remote_path ASC
            """, (pat,)).fetchall()
            return [_row_to_dict(r) for r in rows]
        finally:
            conn.close()
