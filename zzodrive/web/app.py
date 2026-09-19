"""Flask web app for zzoDrive."""
import io
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for,
    jsonify, send_file, flash, session,
)

from .. import config, index, telegram_client, progress, about
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
        "version": "1.0.0",
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

@app.route("/api/files")
def api_files():
    files = index.all_files()
    q = request.args.get("q", "").lower().strip()
    if q:
        files = [f for f in files
                 if q in f["name"].lower()
                 or q in f.get("remote_path", "").lower()]
    files = sorted(files, key=lambda x: x.get("remote_path", x["name"]))
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
    return jsonify({"files": out, "count": len(out)})


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
    rel_path = request.form.get("path") or f.filename
    task_id = uuid.uuid4().hex

    tmp = Path(tempfile.mkdtemp()) / f.filename
    f.save(str(tmp))

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
