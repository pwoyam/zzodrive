"""Telegram client wrapper using Telethon.

Uses a single persistent client managed by `client_manager`.
"""
import asyncio
import hashlib
import threading
from pathlib import Path

from aiofasttelethonhelper import fast_download

from . import config, crypto, index, progress
from . import client_manager
from .fast_upload import upload_parallel

SESSION_PATH = config.CONFIG_DIR / "bot_session"

# Bots cannot upload files larger than 2 GB (Telegram limit)
MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB
WARN_UPLOAD_BYTES = 1900 * 1024 * 1024     # 1.9 GB

# Serialize SQLite-heavy operations to avoid lock contention
_GLOBAL_LOCK = threading.RLock()


def _run(coro):
    with _GLOBAL_LOCK:
        return client_manager.run(coro)


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


def _make_cb(task_id):
    """Progress callback for parallel transfers."""
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


# ---------- async internals ----------

async def _login(token):
    """Verify login and return the user object."""
    client = await client_manager._get_client()
    return await client.get_me()


async def _upload(path: Path, remote_path: str, encrypted: bool, task_id=None):
    channel = int(config.get("ZZODRIVE_CHANNEL_ID"))

    # Size guard: Telegram bots cannot upload > 2 GB
    size = path.stat().st_size
    if size > MAX_UPLOAD_BYTES:
        msg = (
            f"File is too large ({human_size(size)}). "
            f"Telegram bots can only upload up to 2 GB."
        )
        if task_id:
            progress.create(task_id, path.name, size, kind="upload")
            progress.complete(task_id, "error", msg)
        raise ValueError(msg)

    src_path = path
    tmp_enc = None

    if encrypted:
        pwd = config.get("ZZODRIVE_PASSWORD")
        if not pwd:
            if task_id:
                progress.create(task_id, path.name, path.stat().st_size, kind="upload")
                progress.complete(task_id, "error", "Encryption password not set")
            raise ValueError("Encryption password not set")
        try:
            tmp_enc = path.parent / (path.name + ".zzed.tmp")
            crypto.encrypt_file(path, tmp_enc, pwd)
            src_path = tmp_enc
        except Exception as e:
            if task_id:
                progress.create(task_id, path.name, path.stat().st_size, kind="upload")
                progress.complete(task_id, "error", str(e))
            raise

    if task_id:
        progress.create(task_id, src_path.name, src_path.stat().st_size, kind="upload")

    cb = _make_cb(task_id) if task_id else None

    try:
        client = await client_manager._get_client()
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
        # close client on error to allow reconnect
        try:
            await client_manager._close_client()
        except Exception:
            pass
        raise
    finally:
        if tmp_enc and tmp_enc.exists():
            tmp_enc.unlink()


async def _download_to_file(msg_id: int, dest_path: Path, task_id=None):
    channel = int(config.get("ZZODRIVE_CHANNEL_ID"))
    entry = index.find(msg_id)
    encrypted = entry and entry.get("encrypted")

    pwd = None
    if encrypted:
        pwd = config.get("ZZODRIVE_PASSWORD")
        if not pwd:
            raise ValueError("File is encrypted but no password is set")

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    client = await client_manager._get_client()
    try:
        msg = await client.get_messages(channel, ids=msg_id)
        if not msg or not msg.document:
            raise FileNotFoundError(f"Message {msg_id} not found")

        total = msg.document.size
        name = entry["name"] if entry else f"file_{msg_id}"

        if task_id:
            progress.create(task_id, name, total, kind="download")

        cb = _make_cb(task_id) if task_id else None

        if encrypted:
            tmp = dest_path.parent / (dest_path.name + ".zzed.tmp")
            await fast_download(
                client=client,
                message=msg,
                file_path=str(tmp),
                progress_callback=cb,
            )
            crypto.decrypt_file(tmp, dest_path, pwd)
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


async def _download_to_bytes(msg_id: int) -> bytes:
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tmp = Path(tf.name)
    try:
        await _download_to_file(msg_id, tmp)
        return tmp.read_bytes()
    finally:
        tmp.unlink(missing_ok=True)


async def _delete(msg_id: int):
    channel = int(config.get("ZZODRIVE_CHANNEL_ID"))
    client = await client_manager._get_client()
    await client.delete_messages(channel, msg_id)


async def _update_captions(items):
    """items: list of (msg_id, new_path)"""
    if not items:
        return
    channel = int(config.get("ZZODRIVE_CHANNEL_ID"))
    client = await client_manager._get_client()
    for msg_id, new_path in items:
        try:
            await client.edit_message(
                channel, msg_id,
                text=f"zzodrive:{new_path}",
            )
        except Exception as e:
            print(f"[caption update] msg {msg_id}: {e}")


async def _rename_folder_captions(old_prefix, new_prefix):
    idx = index.load()
    affected = [f for f in idx["files"]
                if f.get("remote_path", f["name"]).startswith(old_prefix + "/")]
    if not affected:
        return
    items = []
    for f in affected:
        old_path = f.get("remote_path", f["name"])
        new_path = new_prefix + old_path[len(old_prefix):]
        items.append((f["msg_id"], new_path))
    await _update_captions(items)


# ---------- public sync API ----------

def login(token: str):
    """Login and return user object. Raises on failure."""
    # if token differs from config, reset client to force re-login
    old = config.get("ZZODRIVE_BOT_TOKEN")
    if token and token != old:
        config.set_value("ZZODRIVE_BOT_TOKEN", token)
        client_manager.reset()
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
    _run(_download_to_file(msg_id, output, task_id=task_id))
    return output


def download_to_file(msg_id: int, dest_path, task_id=None):
    dest_path = Path(dest_path)
    _run(_download_to_file(msg_id, dest_path, task_id=task_id))
    return dest_path


def download_to_bytes(msg_id: int) -> bytes:
    return _run(_download_to_bytes(msg_id))


def delete_file(msg_id: int):
    _run(_delete(msg_id))
    index.remove(msg_id)


def update_captions(items):
    return _run(_update_captions(items))


def rename_folder_captions(old_prefix, new_prefix):
    return _run(_rename_folder_captions(old_prefix, new_prefix))
