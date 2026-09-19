"""Telegram client wrapper using Telethon."""
import asyncio
import hashlib
import threading
import tempfile
from pathlib import Path

from telethon import TelegramClient
from aiofasttelethonhelper import fast_upload, fast_download

from . import config, crypto, index, progress
from .fast_upload import upload_parallel
from . import proxy as proxy_mod

SESSION_PATH = config.CONFIG_DIR / "bot_session"

# Serialize all Telegram operations to avoid SQLite lock
_GLOBAL_LOCK = threading.RLock()

# Persistent client cache (started once, reused)
_LOOP = None
_CLIENT = None
_CLIENT_LOCK = threading.Lock()


def _client():
    # proxy is used only if:
    #  - a proxy URL is set, AND
    #  - the proxy is enabled (default: enabled if URL set)
    proxy_enabled = config.get("ZZODRIVE_PROXY_ENABLED")
    # if not set at all, default to True (backwards compat)
    if proxy_enabled is None:
        proxy_enabled = "1"
    proxy_url = config.get("ZZODRIVE_PROXY")

    conn_class = None
    proxy_tuple = None

    if proxy_enabled in ("1", "true", "True", "yes") and proxy_url:
        try:
            conn_class, proxy_tuple = proxy_mod.make_connection(proxy_url)
        except Exception as e:
            print(f"[zzoDrive] proxy config error: {e}")

    kwargs = {}
    if conn_class is not None:
        kwargs["connection"] = conn_class
    if proxy_tuple is not None:
        kwargs["proxy"] = proxy_tuple

    return TelegramClient(
        str(SESSION_PATH),
        config.DEFAULT_API_ID,
        config.DEFAULT_API_HASH,
        **kwargs,
    )


def _run(coro):
    with _GLOBAL_LOCK:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def file_md5(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            c = f.read(chunk)
            if not c:
                break
            h.update(c)
    return h.hexdigest()


def human_size(n):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"


# ---------- async internals ----------

async def _login(token: str):
    client = _client()
    await client.start(bot_token=token)
    me = await client.get_me()
    await client.disconnect()
    return me




def _make_cb(task_id):
    """Build a progress_callback that updates our tracker.

    aiofasttelethonhelper calls the callback with keyword arguments:
        done, total
    """
    def cb(**kwargs):
        try:
            done = kwargs.get("done", 0)
            total = kwargs.get("total")
            if total is not None:
                progress.update(task_id, done, total)
            else:
                progress.update(task_id, done)
        except Exception:
            pass
    return cb


async def _upload(path: Path, remote_path: str, encrypted: bool, task_id=None):
    token = config.get("ZZODRIVE_BOT_TOKEN")
    channel = int(config.get("ZZODRIVE_CHANNEL_ID"))

    src_path = path
    tmp_enc = None

    if encrypted:
        pwd = config.get("ZZODRIVE_PASSWORD")
        if not pwd:
            raise ValueError("Encryption password not set")
        key = crypto.derive_key(pwd)
        tmp_enc = path.parent / (path.name + ".zzed.tmp")
        crypto.encrypt_file(path, tmp_enc, key)
        src_path = tmp_enc

    if task_id:
        progress.create(task_id, src_path.name, src_path.stat().st_size, kind="upload")

    cb = _make_cb(task_id) if task_id else None

    client = _client()
    await client.start(bot_token=token)
    try:
        # custom parallel uploader (8 workers)
        uploaded_file = await upload_parallel(
            client=client,
            file_path=src_path,
            progress_cb=cb,
            num_workers=8,
        )
        msg = await client.send_file(
            channel,
            uploaded_file,
            caption=f"zzodrive:{remote_path}",
            force_document=True,
        )
        up_size = src_path.stat().st_size
        if task_id:
            progress.complete(task_id, "done")
        return msg.id, up_size
    except Exception as e:
        if task_id:
            progress.complete(task_id, "error", str(e))
        raise
    finally:
        await client.disconnect()
        if tmp_enc and tmp_enc.exists():
            tmp_enc.unlink()


async def _download(msg_id: int, output: Path, task_id=None):
    token = config.get("ZZODRIVE_BOT_TOKEN")
    channel = int(config.get("ZZODRIVE_CHANNEL_ID"))

    entry = index.find(msg_id)
    encrypted = entry and entry.get("encrypted")
    key = None
    if encrypted:
        pwd = config.get("ZZODRIVE_PASSWORD")
        if not pwd:
            raise ValueError("File is encrypted but no password is set")
        key = crypto.derive_key(pwd)

    client = _client()
    await client.start(bot_token=token)
    try:
        msg = await client.get_messages(channel, ids=msg_id)
        if not msg or not msg.document:
            raise FileNotFoundError(f"Message {msg_id} not found")

        output.parent.mkdir(parents=True, exist_ok=True)

        total = msg.document.size
        if task_id:
            name = entry["name"] if entry else f"file_{msg_id}"
            progress.create(task_id, name, total, kind="download")

        cb = _make_cb(task_id) if task_id else None

        if encrypted:
            tmp = output.parent / (output.name + ".zzed.tmp")
            await fast_download(
                client=client,
                message=msg,
                file_path=str(tmp),
                progress_callback=cb,
            )
            crypto.decrypt_file(tmp, output, key)
            tmp.unlink(missing_ok=True)
        else:
            await fast_download(
                client=client,
                message=msg,
                file_path=str(output),
                progress_callback=cb,
            )
        if task_id:
            progress.complete(task_id, "done")
    except Exception as e:
        if task_id:
            progress.complete(task_id, "error", str(e))
        raise
    finally:
        await client.disconnect()


async def _download_to_file(msg_id: int, dest_path: Path, task_id=None):
    """Download to a file on disk using fast_download (parallel)."""
    token = config.get("ZZODRIVE_BOT_TOKEN")
    channel = int(config.get("ZZODRIVE_CHANNEL_ID"))

    entry = index.find(msg_id)
    encrypted = entry and entry.get("encrypted")
    key = None
    if encrypted:
        pwd = config.get("ZZODRIVE_PASSWORD")
        if not pwd:
            raise ValueError("Encrypted file — no password set")
        key = crypto.derive_key(pwd)

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    client = _client()
    await client.start(bot_token=token)
    try:
        msg = await client.get_messages(channel, ids=msg_id)
        if not msg or not msg.document:
            raise FileNotFoundError("Message not found in channel")

        total = msg.document.size
        name = entry["name"] if entry else f"file_{msg_id}"

        if task_id:
            progress.create(task_id, name, total, kind="download")

        cb = _make_cb(task_id) if task_id else None

        try:
            if encrypted:
                tmp = dest_path.parent / (dest_path.name + ".zzed.tmp")
                await fast_download(
                    client=client,
                    message=msg,
                    file_path=str(tmp),
                    progress_callback=cb,
                )
                crypto.decrypt_file(tmp, dest_path, key)
                tmp.unlink(missing_ok=True)
            else:
                await fast_download(
                    client=client,
                    message=msg,
                    file_path=str(dest_path),
                    progress_callback=cb,
                )
            if task_id:
                progress.complete(task_id, "done")
        except Exception as e:
            if task_id:
                progress.complete(task_id, "error", str(e))
            raise
    finally:
        await client.disconnect()


async def _download_to_bytes(msg_id: int) -> bytes:
    """Kept for backward compat; prefer _download_to_file."""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tmp = Path(tf.name)
    try:
        await _download_to_file(msg_id, tmp)
        return tmp.read_bytes()
    finally:
        tmp.unlink(missing_ok=True)


async def _delete(msg_id: int):
    token = config.get("ZZODRIVE_BOT_TOKEN")
    channel = int(config.get("ZZODRIVE_CHANNEL_ID"))
    client = _client()
    await client.start(bot_token=token)
    try:
        await client.delete_messages(channel, msg_id)
    finally:
        await client.disconnect()


# ---------- public sync API ----------

def login(token: str):
    return _run(_login(token))


def upload_file(path: Path, remote_path: str = None, encrypted: bool = False, task_id=None):
    remote_path = remote_path or path.name
    md5 = file_md5(path)
    orig = path.stat().st_size
    msg_id, up_size = _run(_upload(path, remote_path, encrypted, task_id=task_id))
    index.add(msg_id, path.name, up_size, remote_path=remote_path,
              md5=md5, encrypted=encrypted, original_size=orig)
    return msg_id


def download_file(msg_id: int, output: Path, task_id=None):
    _run(_download(msg_id, output, task_id=task_id))
    return output


def download_to_bytes(msg_id: int) -> bytes:
    return _run(_download_to_bytes(msg_id))


def download_to_file(msg_id: int, dest_path, task_id=None):
    """Download a file to a local path. Returns the path."""
    dest_path = Path(dest_path)
    _run(_download_to_file(msg_id, dest_path, task_id=task_id))
    return dest_path


def delete_file(msg_id: int):
    _run(_delete(msg_id))
    index.remove(msg_id)
