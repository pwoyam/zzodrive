"""Flask web app for zzoDrive."""
import io
from pathlib import Path

from werkzeug.utils import secure_filename
from flask import (
    Flask, render_template, request, redirect, url_for,
    jsonify, send_file, flash, session,
)

from .. import config, index, telegram_client, progress, about, folders
from .. import i18n

app = Flask(__name__)


# Cache finished downloads: task_id -> local temp file path
_download_cache = {}
app.secret_key = config.get("ZZODRIVE_SECRET") or "zzodrive-secret-key-change-me"


def human_size(n):
    return telegram_client.human_size(n)


def is_ready():
    return config.is_configured()


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
        "version": "1.1.0",
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
    # If the referrer is a valid page on our site, return there; else go to dashboard
    target = request.referrer
    if not target or request.host not in target:
        target = url_for("dashboard") if is_ready() else url_for("setup")
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
    folder = folders.normalize(request.form.get("folder", ""))
    subpath = (request.form.get("path") or f.filename).strip("/")
    # if client sends a full relative path (folder/sub/file), respect it
    if folder:
        rel_path = (folder + "/" + subpath) if subpath else folder
    else:
        rel_path = subpath
    task_id = uuid.uuid4().hex

    safe_name = secure_filename(f.filename) or "file"
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


@app.route("/api/preview/<int:msg_id>")
def api_preview(msg_id):
    """Return the file for inline preview (cached in memory)."""
    import time
    entry = index.find(msg_id)
    if not entry:
        return jsonify({"error": "not found"}), 404

    size = entry.get("size", 0)
    if size > PREVIEW_MAX_SIZE:
        return jsonify({"error": "File too large to preview (>50MB)"}), 413

    now = time.time()

    # cache hit?
    with _preview_lock:
        cached = _preview_cache.get(msg_id)
        if cached and (now - cached[1]) < PREVIEW_CACHE_TTL:
            import mimetypes
            mime, _ = mimetypes.guess_type(entry["name"])
            mime = mime or "application/octet-stream"
            resp = send_file(io.BytesIO(cached[0]), mimetype=mime)
            resp.headers["X-Cache"] = "HIT"
            return resp

    # download
    import tempfile
    tmp_dir = Path(tempfile.mkdtemp(prefix="zzodrive-prev-"))
    tmp_file = tmp_dir / entry["name"]

    try:
        telegram_client.download_to_file(msg_id, tmp_file)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    try:
        data = tmp_file.read_bytes()
    finally:
        try:
            tmp_file.unlink(missing_ok=True)
            tmp_dir.rmdir()
        except Exception:
            pass

    # store in cache
    with _preview_lock:
        _preview_cache[msg_id] = (data, now)
        # limit to 20 entries
        if len(_preview_cache) > 20:
            oldest = min(_preview_cache.keys(), key=lambda k: _preview_cache[k][1])
            del _preview_cache[oldest]

    import mimetypes
    mime, _ = mimetypes.guess_type(entry["name"])
    mime = mime or "application/octet-stream"

    resp = send_file(io.BytesIO(data), mimetype=mime)
    resp.headers["X-Cache"] = "MISS"
    return resp


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
    tmp_file = tmp_dir / name

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
    """Serve the finished file to the browser."""
    path = _download_cache.pop(task_id, None)
    if not path:
        return jsonify({"error": "not ready"}), 404

    p = Path(path)
    if not p.exists():
        return jsonify({"error": "file missing"}), 404

    try:
        data = p.read_bytes()
    finally:
        try:
            p.unlink(missing_ok=True)
            p.parent.rmdir()
        except Exception:
            pass

    return send_file(
        io.BytesIO(data),
        as_attachment=True,
        download_name=p.name,
    )


@app.route("/api/download/<int:msg_id>")
def api_download(msg_id):
    """Legacy endpoint — downloads synchronously and returns the file."""
    import tempfile
    entry = index.find(msg_id)
    name = entry["name"] if entry else f"file_{msg_id}.bin"

    tmp_dir = Path(tempfile.mkdtemp(prefix="zzodrive-dl-"))
    tmp_file = tmp_dir / name

    try:
        telegram_client.download_to_file(msg_id, tmp_file)
    except Exception as e:
        try:
            tmp_file.unlink(missing_ok=True)
            tmp_dir.rmdir()
        except Exception:
            pass
        return jsonify({"error": str(e)}), 500

    try:
        data = tmp_file.read_bytes()
    finally:
        try:
            tmp_file.unlink(missing_ok=True)
            tmp_dir.rmdir()
        except Exception:
            pass

    return send_file(
        io.BytesIO(data),
        as_attachment=True,
        download_name=name,
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
            pwd = data["password"]
            if pwd:
                config.set_value("ZZODRIVE_PASSWORD", pwd)
            else:
                config.delete("ZZODRIVE_PASSWORD")
        return jsonify({"ok": True})

    return jsonify({
        "token_set": bool(config.get("ZZODRIVE_BOT_TOKEN")),
        "channel": config.get("ZZODRIVE_CHANNEL_ID") or "",
        "password_set": bool(config.get("ZZODRIVE_PASSWORD")),
    })


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
    return jsonify({"ok": True, "enabled": enabled})


@app.route("/api/proxy/test", methods=["POST"])
def api_proxy_test():
    """Test a proxy URL without saving it."""
    data = request.get_json() or {}
    proxy = (data.get("proxy") or "").strip()

    # temporarily set and test
    old = config.get("ZZODRIVE_PROXY") or ""
    try:
        if proxy:
            config.set_value("ZZODRIVE_PROXY", proxy)
        else:
            config.delete("ZZODRIVE_PROXY")

        from .. import telegram_client
        telegram_client.login(config.get("ZZODRIVE_BOT_TOKEN") or "")
        return jsonify({"ok": True, "message": "Connected"})
    except Exception as e:
        # restore old value on failure
        if old:
            config.set_value("ZZODRIVE_PROXY", old)
        else:
            config.delete("ZZODRIVE_PROXY")
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/reset", methods=["POST"])
def api_reset():
    from .. import index as idx_mod
    idx_mod.save({"files": []})
    return jsonify({"ok": True})
