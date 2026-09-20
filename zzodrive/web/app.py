"""Flask web app for zzoDrive."""
import io
import asyncio
import re
from pathlib import Path

from flask import (
    after_this_request,
    Flask, render_template, request, redirect, url_for,
    jsonify, send_file, flash, session,
    Response,
    stream_with_context,
)

from .. import config, index, telegram_client, progress, about, folders, auth, client_manager, proxies, cache as cache_module
from .. import i18n



def _safe_filename(name):
    """Sanitize a filename while keeping unicode (Persian, etc).

    Only removes characters that are illegal on any OS: / \ : * ? " < > |
    and null/control chars. Strips leading/trailing spaces and dots.
    """
    import re
    import unicodedata

    if not name:
        return "unnamed"

    # Normalize unicode (NFC) so Persian letters are consistent
    name = unicodedata.normalize("NFC", name)

    # Replace path separators and illegal chars with underscore
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name)

    # Remove leading/trailing dots and spaces (bad on Windows)
    name = name.strip(". ")

    if not name:
        return "unnamed"

    # Cap length to 200 chars (keep extension)
    if len(name) > 200:
        stem = name[:180]
        ext = ""
        if "." in name:
            ext = "." + name.rsplit(".", 1)[-1][:19]
        name = stem + ext

    return name


app = Flask(__name__)


# Cache finished downloads: task_id -> local temp file path
_download_cache = {}
app.secret_key = config.get("ZZODRIVE_SECRET") or "zzodrive-secret-key-change-me"


def human_size(n):
    return telegram_client.human_size(n)


def is_ready():
    return config.is_configured()




# ---------- Security: Host check + CSRF ----------
import ipaddress
import re as _re


def _is_local_host(host):
    """Allow localhost, 127.0.0.1, 192.168.x.x, 10.x.x.x, 172.16-31.x.x"""
    if not host:
        return False
    hostname = host.split(":")[0]
    if hostname in ("localhost", "127.0.0.1", "::1"):
        return True
    try:
        ip = ipaddress.ip_address(hostname)
        return ip.is_private or ip.is_loopback
    except ValueError:
        return False


@app.before_request
def _security_checks():
    # 1) Host header must be a local/private address
    host = request.host
    if not _is_local_host(host):
        return jsonify({"error": "Forbidden host"}), 403

    # 2) CSRF check for state-changing requests
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        # allow uploads (multipart) if Origin/Referer is ours
        origin = request.headers.get("Origin") or request.headers.get("Referer") or ""
        if origin:
            # extract host from origin
            m = _re.match(r"^https?://([^/]+)", origin)
            if m and not _is_local_host(m.group(1)):
                return jsonify({"error": "Cross-origin request blocked"}), 403




# ---------- Auth cookie (set after successful ?token=) ----------
@app.after_request
def _set_auth_cookie(resp):
    if auth.is_lan_mode():
        token = request.args.get("token")
        if token and token == config.get("ZZODRIVE_ACCESS_TOKEN"):
            resp.set_cookie(
                "zzodrive_token", token,
                max_age=60*60*24*365,
                samesite="Strict",
                httponly=True,
            )
    # Security headers
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "same-origin")
    return resp




# ---------- Temp directory cleanup ----------
import glob
import os as _os
import time as _time


_TEMP_DIRS = ("/tmp/zzodrive-dl-", "/tmp/zzodrive-prev-", "/tmp/zzodrive-share-")
_TEMP_MAX_AGE = 3600  # 1 hour
_last_cleanup = 0


def _cleanup_temp_dirs(force=False):
    """Remove stale temp dirs older than _TEMP_MAX_AGE."""
    global _last_cleanup
    now = _time.time()
    if not force and (now - _last_cleanup) < 300:
        return
    _last_cleanup = now

    import tempfile as _tf
    base = _tf.gettempdir()
    for name in ("zzodrive-dl-", "zzodrive-prev-", "zzodrive-share-"):
        pattern = _os.path.join(base, name + "*")
        for path in glob.glob(pattern):
            try:
                mtime = _os.path.getmtime(path)
                if (now - mtime) > _TEMP_MAX_AGE:
                    import shutil
                    if _os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        _os.unlink(path)
            except Exception:
                pass


@app.before_request
def _maybe_cleanup():
    _cleanup_temp_dirs()


@app.context_processor
def inject_globals():
    s = index.stats()
    lang = i18n.get_lang(request)
    is_rtl = lang == "fa"
    return {
        "is_ready": is_ready(),
        "stats": {
            "count": s["count"],
            "total_size": human_size(s["total_size"]),
            "encrypted": s["encrypted"],
        },
        "version": "2.0.0",
        "lang": lang,
        "is_rtl": is_rtl,
        "t": lambda key: i18n.t(lang, key),
        "strings": i18n.all_strings(lang),
        "current_proxy": config.get("ZZODRIVE_PROXY") or "",
        "current_channel": config.get("ZZODRIVE_CHANNEL_ID") or "",
        "about": about.as_dict(),
    }


@app.route("/lang/<code>")
def set_lang(code):
    if code not in ("en", "fa"):
        code = "en"

    # Only allow same-origin referrers; otherwise go to a safe default
    from urllib.parse import urlparse
    target = url_for("dashboard") if is_ready() else url_for("setup")
    ref = request.referrer
    if ref:
        try:
            parsed = urlparse(ref)
            # Host must match ours exactly (no bypass with ?x= or subdomains)
            if parsed.hostname == request.host.split(":")[0]:
                # rebuild target from path+query only (drop scheme/host)
                target = parsed.path or "/"
                if parsed.query:
                    target += "?" + parsed.query
        except Exception:
            pass

    resp = redirect(target)
    resp.set_cookie("lang", code, max_age=60*60*24*365, samesite="Lax")
    return resp


@app.route("/")
def home():
    if not is_ready():
        return redirect(url_for("setup"))
    return redirect(url_for("dashboard"))


@app.route("/setup", methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        token = request.form.get("token", "").strip()
        channel = request.form.get("channel", "").strip()
        password = request.form.get("password", "").strip()

        if not token or not channel:
            flash("Token and Channel ID are required.", "error")
            return redirect(url_for("setup"))

        config.set_value("ZZODRIVE_BOT_TOKEN", token)
        config.set_value("ZZODRIVE_CHANNEL_ID", channel)
        if password:
            config.set_value("ZZODRIVE_PASSWORD", password)
        proxy = request.form.get("proxy", "").strip()
        if proxy:
            config.set_value("ZZODRIVE_PROXY", proxy)
        else:
            config.delete("ZZODRIVE_PROXY")

        # verify login
        try:
            me = telegram_client.login(token)
            flash(f"Connected as @{me.username}", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash(f"Login failed: {e}", "error")
            return redirect(url_for("setup"))

    return render_template("setup.html")


@app.route("/dashboard")
def dashboard():
    if not is_ready():
        return redirect(url_for("setup"))
    return render_template("dashboard.html")


# ---------- API: files ----------

@app.route("/api/folders/list")
def api_folders_list():
    """Return all folders (for the "move to" picker)."""
    all_files = index.all_files()
    paths = [f.get("remote_path", f["name"]) for f in all_files]
    folder_set = folders.all_folders(paths)
    return jsonify({"folders": sorted(folder_set)})


@app.route("/api/files/move", methods=["POST"])
def api_files_move():
    """Move one or more files to a new folder."""
    import threading
    data = request.get_json() or {}
    ids = data.get("ids") or []
    dest = folders.normalize(data.get("dest", ""))

    if not ids:
        return jsonify({"error": "no file ids"}), 400

    idx = index.load()
    moved = 0
    affected = []
    for f in idx["files"]:
        if f["msg_id"] not in ids:
            continue
        old_path = f.get("remote_path", f["name"])
        name = old_path.split("/")[-1]
        new_path = (dest + "/" + name) if dest else name
        f["remote_path"] = new_path
        moved += 1
        affected.append((f["msg_id"], new_path))

    index.save(idx)

    # update Telegram captions in background
    def _bg():
        try:
            telegram_client.update_captions(affected)
        except Exception as e:
            print(f"[move captions] {e}")

    if affected:
        threading.Thread(target=_bg, daemon=True).start()

    return jsonify({"ok": True, "moved": moved, "dest": dest})


@app.route("/api/folders/create", methods=["POST"])
def api_folder_create():
    data = request.get_json() or {}
    parent = folders.normalize(data.get("parent", ""))
    name = (data.get("name") or "").strip().strip("/")

    if not name:
        return jsonify({"error": "Folder name required"}), 400
    if "/" in name or name in (".", ".."):
        return jsonify({"error": "Invalid folder name"}), 400

    full = (parent + "/" + name) if parent else name
    folders.add_empty(full)
    return jsonify({"ok": True, "path": full})


@app.route("/api/folders/rename", methods=["POST"])
def api_folder_rename():
    data = request.get_json() or {}
    old = folders.normalize(data.get("old", ""))
    new_name = (data.get("new_name") or "").strip().strip("/")

    if not old:
        return jsonify({"error": "old path required"}), 400
    if not new_name or "/" in new_name:
        return jsonify({"error": "Invalid folder name"}), 400

    parent = "/".join(old.split("/")[:-1])
    new = (parent + "/" + new_name) if parent else new_name

    if new == old:
        return jsonify({"ok": True, "path": new})

    # rename all files under old prefix
    idx = index.load()
    affected = [f for f in idx["files"]
                if f.get("remote_path", f["name"]).startswith(old + "/")]
    for f in affected:
        rp = f.get("remote_path", f["name"])
        f["remote_path"] = new + rp[len(old):]
    index.save(idx)

    # rename in empty folders
    folders.rename_empty(old, new)

    # rename Telegram captions in background
    import threading
    def _bg():
        try:
            telegram_client.rename_folder_captions(old, new)
        except Exception as e:
            print(f"[folder rename caption] {e}")
    if affected:
        threading.Thread(target=_bg, daemon=True).start()

    return jsonify({"ok": True, "old": old, "new": new, "affected": len(affected)})


@app.route("/api/folders/delete", methods=["POST"])
def api_folder_delete():
    data = request.get_json() or {}
    target = folders.normalize(data.get("path", ""))

    if not target:
        return jsonify({"error": "path required"}), 400

    # find all files under this prefix
    idx = index.load()
    affected = [f for f in idx["files"]
                if f.get("remote_path", f["name"]).startswith(target + "/")]

    # delete from Telegram
    import threading
    def _bg():
        for f in affected:
            try:
                telegram_client.delete_file(f["msg_id"])
            except Exception as e:
                print(f"[folder delete] {e}")
    if affected:
        threading.Thread(target=_bg, daemon=True).start()

    # remove from local index
    idx["files"] = [f for f in idx["files"]
                    if not f.get("remote_path", f["name"]).startswith(target + "/")]
    index.save(idx)

    # remove from empty folders
    data_f = folders._load()
    data_f["empty_folders"] = [
        ef for ef in data_f["empty_folders"]
        if ef != target and not ef.startswith(target + "/")
    ]
    folders._save(data_f)

    return jsonify({"ok": True, "deleted_files": len(affected)})


@app.route("/api/files")
def api_files():
    all_files = index.all_files()
    q = request.args.get("q", "").lower().strip()
    folder = folders.normalize(request.args.get("folder", ""))

    # if searching, ignore folder scope (search all)
    if q:
        files = [f for f in all_files
                 if q in f["name"].lower()
                 or q in f.get("remote_path", "").lower()]
        scoped_folders = []
    else:
        # file list at this level
        files = folders.files_in(folder, all_files)
        # folder list at this level
        all_paths = [f.get("remote_path", f["name"]) for f in all_files]
        scoped_folders = folders.children_of(folder, all_paths)

    # sort
    sort = request.args.get("sort", "name-asc")
    if sort == "name-asc":
        files = sorted(files, key=lambda x: x.get("remote_path", x["name"]).lower())
    elif sort == "name-desc":
        files = sorted(files, key=lambda x: x.get("remote_path", x["name"]).lower(), reverse=True)
    elif sort == "size-desc":
        files = sorted(files, key=lambda x: x.get("size", 0), reverse=True)
    elif sort == "size-asc":
        files = sorted(files, key=lambda x: x.get("size", 0))
    elif sort == "date-desc":
        files = sorted(files, key=lambda x: x.get("uploaded_at", 0), reverse=True)
    elif sort == "date-asc":
        files = sorted(files, key=lambda x: x.get("uploaded_at", 0))
    else:
        files = sorted(files, key=lambda x: x.get("remote_path", x["name"]).lower())

    out = []
    for f in files:
        out.append({
            "id": f["msg_id"],
            "name": f["name"],
            "path": f.get("remote_path", f["name"]),
            "size": f["size"],
            "size_human": human_size(f["size"]),
            "encrypted": f.get("encrypted", False),
            "uploaded_at": f.get("uploaded_at", 0),
        })
    folder_items = []
    for name in scoped_folders:
        full = (folder + "/" + name) if folder else name
        folder_items.append({
            "name": name,
            "path": full,
        })

    return jsonify({
        "files": out,
        "count": len(out),
        "folders": folder_items,
        "current_folder": folder,
    })


@app.route("/api/upload", methods=["POST"])
def api_upload():
    import tempfile
    import threading
    import uuid

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400

    encrypted = request.form.get("encrypt") == "1"

    # Early check: encryption requested but no password
    if encrypted and not config.get("ZZODRIVE_PASSWORD"):
        return jsonify({
            "error": "Encryption password not set. Set it in Settings → Encryption."
        }), 400

    # Early check: file size (Telegram bot limit is 2 GB)
    # Note: request.content_length includes multipart overhead, so use a generous cap
    MAX_BYTES = 2 * 1024 * 1024 * 1024
    if request.content_length and request.content_length > MAX_BYTES:
        return jsonify({
            "error": f"File too large (max 2 GB for Telegram bots)"
        }), 413
    folder = folders.normalize(request.form.get("folder", ""))
    subpath = (request.form.get("path") or f.filename).strip("/")
    # if client sends a full relative path (folder/sub/file), respect it
    if folder:
        rel_path = (folder + "/" + subpath) if subpath else folder
    else:
        rel_path = subpath
    task_id = uuid.uuid4().hex

    safe_name = _safe_filename(f.filename)
    tmp = Path(tempfile.mkdtemp()) / safe_name
    try:
        f.save(str(tmp))
    except Exception as e:
        return jsonify({"error": f"Could not save file: {e}"}), 500

    def _bg():
        try:
            telegram_client.upload_file(
                tmp, remote_path=rel_path, encrypted=encrypted, task_id=task_id,
            )
        except Exception as e:
            progress.complete(task_id, "error", str(e))
        finally:
            tmp.unlink(missing_ok=True)
            progress.cleanup_old()

    threading.Thread(target=_bg, daemon=True).start()

    return jsonify({"ok": True, "task_id": task_id, "name": f.filename})


@app.route("/api/progress/<task_id>")
def api_progress(task_id):
    p = progress.get(task_id)
    if not p:
        return jsonify({"error": "not found"}), 404
    p["speed_human"] = _human_speed(p.get("speed", 0))
    p["current_human"] = human_size(p.get("current", 0))
    p["total_human"] = human_size(p.get("total", 0))
    return jsonify(p)


def _human_speed(bps):
    if bps < 1024:
        return f"{bps:.0f} B/s"
    if bps < 1024 * 1024:
        return f"{bps/1024:.1f} KB/s"
    return f"{bps/(1024*1024):.1f} MB/s"


# preview cache: msg_id -> (bytes, timestamp)
_preview_cache = {}
_preview_lock = __import__("threading").Lock()
PREVIEW_CACHE_TTL = 3600  # 1 hour
PREVIEW_MAX_SIZE = 50 * 1024 * 1024  # 50 MB


# Safe MIME types that can be served inline
SAFE_PREVIEW_MIMES = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp",
    "video/mp4", "video/webm", "video/ogg",
    "audio/mpeg", "audio/ogg", "audio/wav", "audio/webm",
    "application/pdf",
}


def _safe_preview_mime(name):
    """Return a MIME only if it is safe to serve inline; else None."""
    import mimetypes
    mime, _ = mimetypes.guess_type(name)
    if not mime:
        return None
    if mime not in SAFE_PREVIEW_MIMES:
        return None
    return mime


@app.route("/api/preview/<int:msg_id>")
def api_preview(msg_id):
    """Return the file for inline preview (cached in memory)."""
    import time
    entry = index.find(msg_id)
    if not entry:
        return jsonify({"error": "not found"}), 404

    # Reject unsafe MIME types (HTML, SVG, JS, etc.)
    safe_mime = _safe_preview_mime(entry["name"])
    if not safe_mime:
        return jsonify({"error": "Preview not supported for this file type"}), 415

    size = entry.get("size", 0)
    if size > PREVIEW_MAX_SIZE:
        return jsonify({"error": "File too large to preview (>50MB)"}), 413

    now = time.time()

    # cache hit? serve from disk
    with _preview_lock:
        cached = _preview_cache.get(msg_id)
        if cached and (now - cached[1]) < PREVIEW_CACHE_TTL:
            cached_path = Path(cached[0])
            if cached_path.exists():
                resp = send_file(str(cached_path), mimetype=safe_mime, conditional=True)
                resp.headers["X-Cache"] = "HIT"
                resp.headers["X-Content-Type-Options"] = "nosniff"
                resp.headers["Content-Security-Policy"] = "default-src 'none'; img-src 'self'; media-src 'self'; object-src 'none'; script-src 'none';"
                return resp

    # download
    import tempfile
    tmp_dir = Path(tempfile.mkdtemp(prefix="zzodrive-prev-"))
    tmp_file = tmp_dir / _safe_filename(entry["name"])

    try:
        telegram_client.download_to_file(msg_id, tmp_file)
    except Exception as e:
        try:
            tmp_file.unlink(missing_ok=True)
            tmp_dir.rmdir()
        except Exception:
            pass
        return jsonify({"error": str(e)}), 500

    # store path in cache (not bytes!)
    with _preview_lock:
        _preview_cache[msg_id] = (str(tmp_file), now)
        # cap cache to 20 entries — evict oldest + delete its file
        if len(_preview_cache) > 20:
            oldest_key = min(_preview_cache.keys(), key=lambda k: _preview_cache[k][1])
            old_path = Path(_preview_cache[oldest_key][0])
            del _preview_cache[oldest_key]
            try:
                old_path.unlink(missing_ok=True)
                old_path.parent.rmdir()
            except Exception:
                pass

    @after_this_request
    def _cleanup(resp):
        # NOTE: file stays in cache, not deleted here (for next request)
        return resp

    resp = send_file(str(tmp_file), mimetype=safe_mime, conditional=True)
    resp.headers["X-Cache"] = "MISS"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Content-Security-Policy"] = "default-src 'none'; img-src 'self'; media-src 'self'; object-src 'none'; script-src 'none';"
    return resp


@app.route("/api/stream/<int:msg_id>")
def api_stream(msg_id):
    """Stream media to browser with Range support (direct, no queue)."""
    import queue as _queue

    entry = index.find(msg_id)
    if not entry:
        return jsonify({"error": "not found"}), 404

    name = entry["name"].lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    if ext not in ("mp4", "webm", "mkv", "mov", "m4v", "mp3", "m4a", "ogg", "wav", "opus"):
        return jsonify({"error": "unsupported media type"}), 415

    total_size = entry.get("size", 0)
    if total_size == 0:
        return jsonify({"error": "invalid size"}), 400

    range_header = request.headers.get("Range")
    start = 0
    end = total_size - 1
    is_range = False
    if range_header:
        m = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if m:
            start = int(m.group(1))
            if m.group(2):
                end = int(m.group(2))
            if end >= total_size:
                end = total_size - 1
            is_range = True

    length = end - start + 1
    print(f"[stream] msg={msg_id} range={start}-{end}/{total_size}")

    mimes = {
        "mp4": "video/mp4", "webm": "video/webm", "mkv": "video/x-matroska",
        "mov": "video/quicktime", "m4v": "video/x-m4v",
        "mp3": "audio/mpeg", "m4a": "audio/mp4",
        "ogg": "audio/ogg", "wav": "audio/wav", "opus": "audio/opus",
    }
    content_type = mimes.get(ext, "application/octet-stream")

    def generate():
        q = _queue.Queue(maxsize=64)
        STOP = object()

        async def _produce():
            try:
                channel_id = int(config.get("ZZODRIVE_CHANNEL_ID"))
                client = await client_manager._get_client()
                msg = await client.get_messages(channel_id, ids=msg_id)
                if not msg or not msg.document:
                    raise FileNotFoundError("message not found")

                remaining = length
                async for chunk in client.iter_download(
                    msg.document,
                    offset=start,
                    request_size=2 * 1024 * 1024,
                ):
                    if not chunk:
                        break
                    data = chunk[:min(len(chunk), remaining)]
                    block = 256 * 1024
                    for i in range(0, len(data), block):
                        q.put(data[i:i+block])
                    remaining -= len(data)
                    if remaining <= 0:
                        break
            except Exception as e:
                print(f"[stream] error: {e}")
            finally:
                q.put(STOP)

        client_manager._ensure_loop()
        asyncio.run_coroutine_threadsafe(_produce(), client_manager._LOOP)

        while True:
            try:
                item = q.get(timeout=60)
            except _queue.Empty:
                print("[stream] timeout")
                break
            if item is STOP:
                break
            yield item

    status = 206 if is_range else 200
    headers = {
        "Content-Type": content_type,
        "Accept-Ranges": "bytes",
        "Content-Length": str(length),
        "Cache-Control": "no-store",
    }
    if is_range:
        headers["Content-Range"] = f"bytes {start}-{end}/{total_size}"

    return Response(
        stream_with_context(generate()),
        status=status,
        headers=headers,
    )


@app.route("/api/stream/info/<int:msg_id>")
def api_stream_info(msg_id):
    """Check if a file is streamable."""
    entry = index.find(msg_id)
    if not entry:
        return jsonify({"streamable": False}), 404
    name = entry["name"].lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    streamable = ext in ("mp4", "webm", "mkv", "mov", "m4v", "mp3", "m4a", "ogg", "wav", "opus")
    return jsonify({
        "streamable": streamable,
        "size": entry.get("size", 0),
        "name": entry.get("name", ""),
        "url": f"/api/stream/{msg_id}" if streamable else None,
    })


@app.route("/api/download/start/<int:msg_id>", methods=["POST"])
def api_download_start(msg_id):
    """Start a background download and return a task_id."""
    import tempfile
    import threading
    import uuid

    entry = index.find(msg_id)
    if not entry:
        return jsonify({"error": "file not found"}), 404

    name = entry["name"]
    task_id = uuid.uuid4().hex

    tmp_dir = Path(tempfile.mkdtemp(prefix="zzodrive-dl-"))
    tmp_file = tmp_dir / _safe_filename(name)

    def _bg():
        try:
            telegram_client.download_to_file(msg_id, tmp_file, task_id=task_id)
            _download_cache[task_id] = str(tmp_file)
        except Exception as e:
            progress.complete(task_id, "error", str(e))

    threading.Thread(target=_bg, daemon=True).start()

    return jsonify({
        "ok": True,
        "task_id": task_id,
        "name": name,
        "size": entry.get("size", 0),
    })


@app.route("/api/download/finish/<task_id>")
def api_download_finish(task_id):
    """Stream the finished file to the browser."""
    path = _download_cache.pop(task_id, None)
    if not path:
        return jsonify({"error": "not ready"}), 404

    p = Path(path)
    if not p.exists():
        return jsonify({"error": "file missing"}), 404

    @after_this_request
    def _cleanup(resp):
        try:
            p.unlink(missing_ok=True)
            p.parent.rmdir()
        except Exception:
            pass
        return resp

    return send_file(
        str(p),
        as_attachment=True,
        download_name=p.name,
        conditional=True,
    )


@app.route("/api/download/<int:msg_id>")
def api_download(msg_id):
    """Stream a file to the browser without loading it into RAM."""
    import tempfile
    entry = index.find(msg_id)
    name = entry["name"] if entry else f"file_{msg_id}.bin"

    tmp_dir = Path(tempfile.mkdtemp(prefix="zzodrive-dl-"))
    tmp_file = tmp_dir / _safe_filename(name)

    try:
        telegram_client.download_to_file(msg_id, tmp_file)
    except Exception as e:
        try:
            tmp_file.unlink(missing_ok=True)
            tmp_dir.rmdir()
        except Exception:
            pass
        return jsonify({"error": str(e)}), 500

    # clean up after the response is sent
    @after_this_request
    def _cleanup(resp):
        try:
            tmp_file.unlink(missing_ok=True)
            tmp_dir.rmdir()
        except Exception:
            pass
        return resp

    return send_file(
        str(tmp_file),
        as_attachment=True,
        download_name=name,
        conditional=True,
    )


@app.route("/api/delete/<int:msg_id>", methods=["POST"])
def api_delete(msg_id):
    try:
        telegram_client.delete_file(msg_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats")
def api_stats():
    return jsonify(index.stats())


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "POST":
        data = request.get_json() or {}
        if "password" in data:
            old_pwd = config.get("ZZODRIVE_PASSWORD") or ""
            new_pwd = data["password"] or ""

            # If password changes, count encrypted files for warning
            if new_pwd != old_pwd:
                enc_count = sum(
                    1 for f in index.all_files() if f.get("encrypted")
                )

                # If changing to a NEW non-empty password and there are
                # already-encrypted files, refuse unless `force` is set.
                if old_pwd and new_pwd and enc_count > 0:
                    if not data.get("force"):
                        return jsonify({
                            "error": (
                                f"You have {enc_count} encrypted file(s). "
                                "Changing the password will make them "
                                "unreadable. Send {force: true} to confirm."
                            ),
                            "encrypted_count": enc_count,
                        }), 409

            if new_pwd:
                config.set_value("ZZODRIVE_PASSWORD", new_pwd)
            else:
                config.delete("ZZODRIVE_PASSWORD")
        return jsonify({"ok": True})

    enc_count = sum(1 for f in index.all_files() if f.get("encrypted"))
    return jsonify({
        "token_set": bool(config.get("ZZODRIVE_BOT_TOKEN")),
        "channel": config.get("ZZODRIVE_CHANNEL_ID") or "",
        "password_set": bool(config.get("ZZODRIVE_PASSWORD")),
        "encrypted_count": enc_count,
    })


@app.route("/api/proxies", methods=["GET"])
def api_proxies_list():
    """List saved proxies."""
    return jsonify({"proxies": proxies.list_all()})


@app.route("/api/proxies", methods=["POST"])
def api_proxies_add():
    """Add a new proxy."""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL required"}), 400
    try:
        entry = proxies.add(name, url)
        return jsonify({"ok": True, "proxy": entry})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/proxies/<proxy_id>", methods=["DELETE"])
def api_proxies_delete(proxy_id):
    """Delete a saved proxy."""
    ok = proxies.remove(proxy_id)
    return jsonify({"ok": ok})


@app.route("/api/proxies/<proxy_id>/activate", methods=["POST"])
def api_proxies_activate(proxy_id):
    """Activate a saved proxy."""
    print(f"[activate] proxy_id={proxy_id}")

    entry = proxies.activate(proxy_id)
    if not entry:
        print(f"[activate] not found")
        return jsonify({"error": "not found"}), 404

    # چک کن config واقعاً عوض شده
    new_url = config.get("ZZODRIVE_PROXY") or ""
    print(f"[activate] config now: {new_url[:50]}...")

    client_manager.reset()
    print(f"[activate] client reset")

    # test connection
    try:
        telegram_client.login(config.get("ZZODRIVE_BOT_TOKEN") or "")
        print(f"[activate] connection OK")
        return jsonify({"ok": True, "proxy": entry})
    except Exception as e:
        print(f"[activate] connection failed: {e}")
        return jsonify({"ok": False, "error": str(e), "proxy": entry}), 400


@app.route("/api/proxies/deactivate", methods=["POST"])
def api_proxies_deactivate():
    """Turn off proxy without deleting."""
    proxies.deactivate_all()
    client_manager.reset()
    return jsonify({"ok": True})


@app.route("/api/proxy", methods=["GET", "POST"])
def api_proxy():
    if request.method == "POST":
        data = request.get_json() or {}
        proxy = (data.get("proxy") or "").strip()
        enabled = data.get("enabled", None)

        if proxy:
            config.set_value("ZZODRIVE_PROXY", proxy)
        else:
            config.delete("ZZODRIVE_PROXY")

        if enabled is not None:
            config.set_value("ZZODRIVE_PROXY_ENABLED", "1" if enabled else "0")

        # reset client to force reconnect with new settings
        client_manager.reset()

        # test connection
        try:
            from .. import telegram_client
            telegram_client.login(config.get("ZZODRIVE_BOT_TOKEN") or "")
            return jsonify({"ok": True, "proxy": proxy, "message": "Connected"})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 400

    enabled = config.get("ZZODRIVE_PROXY_ENABLED")
    if enabled is None:
        enabled = "1" if config.get("ZZODRIVE_PROXY") else "0"

    return jsonify({
        "proxy": config.get("ZZODRIVE_PROXY") or "",
        "has_proxy": bool(config.get("ZZODRIVE_PROXY")),
        "enabled": enabled in ("1", "true", "True", "yes"),
    })


@app.route("/api/proxy/toggle", methods=["POST"])
def api_proxy_toggle():
    """Quickly toggle proxy on/off without changing URL."""
    data = request.get_json() or {}
    enabled = bool(data.get("enabled", False))
    config.set_value("ZZODRIVE_PROXY_ENABLED", "1" if enabled else "0")
    client_manager.reset()
    return jsonify({"ok": True, "enabled": enabled})


@app.route("/api/proxy/test", methods=["POST"])
def api_proxy_test():
    """Test a proxy URL WITHOUT saving it.

    Runs a one-off TelegramClient in a temporary session file
    so the running config and cached client are not touched.
    """
    import asyncio
    import tempfile

    from telethon import TelegramClient
    from .. import proxy as proxy_mod

    data = request.get_json() or {}
    proxy_url = (data.get("proxy") or "").strip()
    token = config.get("ZZODRIVE_BOT_TOKEN")
    if not token:
        return jsonify({"ok": False, "error": "Bot token not set"}), 400

    # Build kwargs from the provided proxy (may be empty)
    kwargs = {}
    if proxy_url:
        try:
            conn, pt = proxy_mod.make_connection(proxy_url)
            if conn is not None:
                kwargs["connection"] = conn
            if pt is not None:
                kwargs["proxy"] = pt
        except Exception as e:
            return jsonify({"ok": False, "error": f"Invalid proxy: {e}"}), 400

    # Use a throwaway session so we don't touch the active one
    with tempfile.TemporaryDirectory(prefix="zzodrive-test-") as td:
        session_path = Path(td) / "test_session"

        async def _do_test():
            client = TelegramClient(
                str(session_path),
                config.DEFAULT_API_ID,
                config.DEFAULT_API_HASH,
                **kwargs,
            )
            try:
                await asyncio.wait_for(client.start(bot_token=token), timeout=20)
                me = await client.get_me()
                return {"id": me.id, "username": me.username}
            finally:
                try:
                    await client.disconnect()
                except Exception:
                    pass

        try:
            loop = asyncio.new_event_loop()
            try:
                info = loop.run_until_complete(_do_test())
            finally:
                loop.close()
            return jsonify({"ok": True, "message": "Connected", "user": info})
        except asyncio.TimeoutError:
            return jsonify({"ok": False, "error": "Timeout (20s)"}), 400
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 400




@app.route("/api/lan/token", methods=["GET", "POST"])
def api_lan_token():
    """Get or regenerate the LAN access token."""
    if request.method == "POST":
        action = (request.get_json() or {}).get("action")
        if action == "regenerate":
            new_token = auth.regenerate_token()
            return jsonify({"ok": True, "token": new_token})
        if action == "disable":
            config.delete("ZZODRIVE_ACCESS_TOKEN")
            return jsonify({"ok": True, "disabled": True})

    if auth.is_lan_mode():
        return jsonify({
            "enabled": True,
            "token": config.get("ZZODRIVE_ACCESS_TOKEN"),
        })
    return jsonify({"enabled": False, "token": None})


@app.route("/api/lan/enable", methods=["POST"])
def api_lan_enable():
    """Enable LAN mode with a generated token."""
    token = auth.get_or_create_token()
    return jsonify({"ok": True, "token": token})


@app.route("/api/cache/info")
def api_cache_info():
    """Return cache info."""
    info = cache_module.cache.info()

    def _hs(n):
        for u in ["B", "KB", "MB", "GB", "TB"]:
            if n < 1024:
                return f"{n:.1f} {u}"
            n /= 1024
        return f"{n:.1f} PB"

    info["total_size_human"] = _hs(info["total_size"])
    info["max_size_human"] = _hs(info["max_size"])
    return jsonify(info)


@app.route("/api/lru/clear", methods=["POST"])
def api_lru_clear():
    """Clear all cached files (LRU cache)."""
    count, size = cache_module.cache.clear()
    def _hs(n):
        for u in ["B", "KB", "MB", "GB", "TB"]:
            if n < 1024:
                return f"{n:.1f} {u}"
            n /= 1024
        return f"{n:.1f} PB"
    return jsonify({
        "ok": True,
        "removed": count,
        "freed_human": _hs(size),
    })


@app.route("/api/reset", methods=["POST"])
def api_reset():
    from .. import index as idx_mod
    idx_mod.save({"files": []})
    return jsonify({"ok": True})
