"""Persistent Telegram client manager.

Runs a single background asyncio loop and keeps one TelegramClient
alive for all operations. This avoids the cost of creating a new
client + event loop for every request, and prevents resource leaks.
"""
import asyncio
import atexit
import threading

from telethon import TelegramClient

from . import config
from . import proxy as proxy_mod

SESSION_PATH = config.CONFIG_DIR / "bot_session"

_LOOP = None
_THREAD = None
_CLIENT = None
_INIT_LOCK = threading.RLock()


def _run_loop():
    global _LOOP
    _LOOP = asyncio.new_event_loop()
    asyncio.set_event_loop(_LOOP)
    try:
        _LOOP.run_forever()
    finally:
        try:
            _LOOP.close()
        except Exception:
            pass


def _ensure_loop():
    global _THREAD
    with _INIT_LOCK:
        if _THREAD is None or not _THREAD.is_alive():
            _THREAD = threading.Thread(
                target=_run_loop, daemon=True, name="zzoDrive-loop"
            )
            _THREAD.start()
            # give the loop a moment to start
            import time
            for _ in range(50):
                if _LOOP is not None:
                    break
                time.sleep(0.02)


def run(coro):
    """Block until the given coroutine completes on the shared loop."""
    _ensure_loop()
    fut = asyncio.run_coroutine_threadsafe(coro, _LOOP)
    return fut.result()


def _make_kwargs():
    """Build TelegramClient kwargs from config (proxy etc)."""
    kwargs = {}
    proxy_url = config.get("ZZODRIVE_PROXY")
    enabled = config.get("ZZODRIVE_PROXY_ENABLED")
    if enabled is None:
        enabled = "1"
    if enabled in ("1", "true", "True", "yes") and proxy_url:
        try:
            conn, pt = proxy_mod.make_connection(proxy_url)
            if conn is not None:
                kwargs["connection"] = conn
            if pt is not None:
                kwargs["proxy"] = pt
        except Exception as e:
            print(f"[zzoDrive] proxy config error: {e}")
    return kwargs


async def _get_client():
    global _CLIENT
    if _CLIENT is not None:
        try:
            if _CLIENT.is_connected():
                return _CLIENT
        except Exception:
            pass
        # was connected but died — drop it
        try:
            await _CLIENT.disconnect()
        except Exception:
            pass
        _CLIENT = None

    token = config.get("ZZODRIVE_BOT_TOKEN")
    if not token:
        raise RuntimeError("Bot token not set")

    kwargs = _make_kwargs()
    client = TelegramClient(
        str(SESSION_PATH),
        config.DEFAULT_API_ID,
        config.DEFAULT_API_HASH,
        **kwargs,
    )
    await client.start(bot_token=token)
    _CLIENT = client

    # Register bot command handlers (only once per client)
    try:
        from . import bot_commands
        bot_commands.register(client)
    except Exception as e:
        print(f"[client_manager] bot_commands register failed: {e}")

    return _CLIENT


async def _close_client():
    global _CLIENT
    if _CLIENT is not None:
        try:
            await _CLIENT.disconnect()
        except Exception:
            pass
        _CLIENT = None


def get_client():
    """Sync: return the persistent client (connecting if needed)."""
    return run(_get_client())


def close():
    """Sync: disconnect and forget the client."""
    try:
        run(_close_client())
    except Exception:
        pass


def reset():
    """Force a fresh connection on next use."""
    close()


@atexit.register
def _cleanup():
    try:
        close()
    except Exception:
        pass
