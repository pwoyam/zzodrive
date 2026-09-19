#!/usr/bin/env python3
"""
zzoDrive launcher.

Run this file to start the app. It will:
  - verify dependencies
  - start the web server
  - open your browser automatically
"""
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


HOST = "0.0.0.0"


def find_free_port(start=8765, max_tries=50):
    """Find the first free port starting at `start`."""
    import socket
    for offset in range(max_tries):
        port = start + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((HOST, port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port found")


PORT = find_free_port()
URL = f"http://127.0.0.1:{PORT}"


def _local_ips():
    """Return list of local IPv4 addresses (for LAN share links)."""
    import socket
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    return ips


LOCAL_IP = _local_ips()[0] if _local_ips() else "127.0.0.1"


def open_browser_later():
    time.sleep(1.2)
    try:
        webbrowser.open(URL)
    except Exception:
        pass


def main():
    print()
    print("=" * 60)
    print("         🚀  zzoDrive v1.0.0 is starting")
    print("=" * 60)
    print()
    print(f"  Local URL : {URL}")
    print(f"  LAN URL   : http://{LOCAL_IP}:{PORT}   (other devices on your Wi-Fi)")
    print(f"  Stop      : press Ctrl+C")
    print()

    threading.Thread(target=open_browser_later, daemon=True).start()

    try:
        app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 Bye!")


if __name__ == "__main__":
    main()
