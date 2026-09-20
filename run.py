#!/usr/bin/env python3
"""
zzoDrive launcher.

Run this file to start the app. It will:
  - verify dependencies
  - start the web server
  - open your browser automatically
"""
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

# ---------- friendly dependency check ----------
missing = []
try:
    import telethon  # noqa
except ImportError:
    missing.append("telethon")
try:
    import cryptography  # noqa
except ImportError:
    missing.append("cryptography")
try:
    import flask  # noqa
except ImportError:
    missing.append("flask")

if missing:
    print()
    print("=" * 60)
    print("  Missing dependencies:", ", ".join(missing))
    print("=" * 60)
    print()
    print("  Please install them first:")
    print()
    print(f"    {sys.executable} -m pip install -r requirements.txt")
    print()
    print("  Or run the installer:")
    print("    macOS / Linux :  bash install.sh")
    print("    Windows       :  install.bat")
    print()
    sys.exit(1)


# ---------- start app ----------
from zzodrive.web.app import app  # noqa: E402


# Default: bind to localhost only (secure).
# Set ZZODRIVE_LAN=1 to allow LAN access (a token will be required).
LAN_MODE = os.environ.get("ZZODRIVE_LAN", "").lower() in ("1", "true", "yes")
HOST = "0.0.0.0" if LAN_MODE else "127.0.0.1"


def _local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def find_free_port(start=8765, max_tries=50):
    for offset in range(max_tries):
        port = start + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((HOST if HOST != "0.0.0.0" else "0.0.0.0", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port found")


PORT = find_free_port()
LOCAL_IP = _local_ip()


def open_browser_later():
    time.sleep(1.2)
    try:
        webbrowser.open(f"http://127.0.0.1:{PORT}")
    except Exception:
        pass


def main():
    print()
    print("=" * 60)
    print("         🚀  zzoDrive v2.0.0 is starting")
    print("=" * 60)
    print()

    if LAN_MODE:
        # in LAN mode, show the access token
        from zzodrive import auth
        token = auth.get_or_create_token()
        print(f"  Local URL : http://127.0.0.1:{PORT}")
        print(f"  LAN URL   : http://{LOCAL_IP}:{PORT}")
        print()
        print(f"  🔒 Access token: {token}")
        print(f"     Share this URL with your phone:")
        print(f"     http://{LOCAL_IP}:{PORT}/?token={token}")
        print()
    else:
        print(f"  URL  : http://127.0.0.1:{PORT}")
        print(f"  Note : LAN access disabled (local only)")
        print(f"         To enable: set ZZODRIVE_LAN=1")
        print()

    print(f"  Stop : press Ctrl+C  (or close this window)")
    print()
    print(f"  💡 Keep this window open while using zzoDrive.")

    # Start event-based sync (in a thread so client is ready first)
    def _start_sync():
        import time as _t
        _t.sleep(2)
        try:
            from zzodrive import sync_watcher
            sync_watcher.start()
        except Exception as e:
            print(f"  Sync     : Failed to start ({e})")

    threading.Thread(target=_start_sync, daemon=True).start()

    threading.Thread(target=open_browser_later, daemon=True).start()

    try:
        try:
            from waitress import serve
            serve(app, host=HOST, port=PORT, threads=4)
        except ImportError:
            app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 Bye!")


if __name__ == "__main__":
    main()
