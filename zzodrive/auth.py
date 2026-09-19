"""Simple token-based auth for zzoDrive LAN mode."""
import secrets

from flask import request, Response, jsonify

from . import config


def is_lan_mode():
    """LAN mode is on if access token is set."""
    return bool(config.get("ZZODRIVE_ACCESS_TOKEN"))


def get_or_create_token():
    """Get or generate an access token."""
    token = config.get("ZZODRIVE_ACCESS_TOKEN")
    if not token:
        token = secrets.token_urlsafe(16)
        config.set_value("ZZODRIVE_ACCESS_TOKEN", token)
    return token


def regenerate_token():
    token = secrets.token_urlsafe(16)
    config.set_value("ZZODRIVE_ACCESS_TOKEN", token)
    return token


def check_auth():
    """Return None if OK, or a Response to send back (401)."""
    if not is_lan_mode():
        return None

    token = config.get("ZZODRIVE_ACCESS_TOKEN")

    # 1) check cookie
    if request.cookies.get("zzodrive_token") == token:
        return None

    # 2) check query param (?token=xxx)
    if request.args.get("token") == token:
        # don't redirect, just allow; set cookie in response is complex here
        return None

    # 3) check Authorization: Bearer
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ") and auth[7:] == token:
        return None

    # 4) check Basic auth (username = zzodrive, password = token)
    basic = request.authorization
    if basic and basic.password == token:
        return None

    # Not authorized — return 401 with instructions
    if request.path.startswith("/api/"):
        return jsonify({"error": "Unauthorized. Provide ?token=... or set the cookie."}), 401

    # HTML page for browser
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>zzoDrive — Access</title>
<style>
body {{ font-family: -apple-system, sans-serif; background:#f7f8fa; display:flex; align-items:center; justify-content:center; min-height:100vh; margin:0; }}
.box {{ background:#fff; border-radius:12px; padding:32px; max-width:420px; width:100%; box-shadow:0 10px 30px rgba(0,0,0,.1); }}
h1 {{ margin:0 0 12px; font-size:1.4rem; }}
p {{ color:#6b7280; font-size:0.95rem; }}
input {{ width:100%; padding:12px; border:1px solid #e5e7eb; border-radius:8px; font-size:1rem; margin-top:8px; box-sizing:border-box; }}
button {{ width:100%; padding:12px; background:#4f7cff; color:#fff; border:none; border-radius:8px; font-size:1rem; font-weight:600; cursor:pointer; margin-top:12px; }}
button:hover {{ background:#3a66e0; }}
code {{ background:#f3f4f6; padding:2px 6px; border-radius:4px; font-size:0.85rem; word-break:break-all; }}
</style></head><body>
<div class="box">
  <h1>🔐 zzoDrive</h1>
  <p>Enter your access token to continue. Your token is in <code>~/.zzodrive/config.env</code>.</p>
  <form method="get" action="{request.path}">
    <input type="password" name="token" placeholder="Access token" autofocus required>
    <button type="submit">Unlock</button>
  </form>
</div>
</body></html>"""
    return Response(html, status=401, mimetype="text/html")


def install_middleware(app):
    """Register the auth check as a before_request handler."""

    @app.before_request
    def _auth_gate():
        # skip static files
        if request.path.startswith("/static/"):
            return None
        return check_auth()


def cookie_from_token(token):
    """Helper for setting the cookie after a successful ?token= login."""
    return token
