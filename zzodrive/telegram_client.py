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
from . import chunker
from . import cache

SESSION_PATH = config.CONFIG_DIR / "bot_session"

# Bots cannot upload files larger than 2 GB (Telegram limit)
MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB
# Override for testing:
import os as _os
_test_size = _os.environ.get("ZZODRIVE_CHUNK_THRESHOLD")
if _test_size:
    MAX_UPLOAD_BYTES = int(_test_size)
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

    # If file too large, use chunked upload
    size = path.stat().st_size
    if size > MAX_UPLOAD_BYTES:
        return await _upload_chunked(path, remote_path, encrypted, task_id)

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


async def _upload_chunked(path, remote_path, encrypted, task_id=None):
    """Upload file > 2GB by splitting into chunks."""
    channel_id = int(config.get("ZZODRIVE_CHANNEL_ID"))
    size = path.stat().st_size

    # Encrypt first if needed (chunks must be encrypted before splitting)
    work_file = path
    tmp_enc = None
    if encrypted:
        pwd = config.get("ZZODRIVE_PASSWORD")
        if not pwd:
            if task_id:
                progress.create(task_id, path.name, size, kind="upload")
                progress.complete(task_id, "error", "Encryption password not set")
            raise ValueError("Encryption password not set")
        tmp_enc = path.parent / (path.name + ".zzed.tmp")
        crypto.encrypt_file(path, tmp_enc, pwd)
        work_file = tmp_enc

    # Split — CHUNK_SIZE = MAX_UPLOAD_BYTES با یه بافر کوچیک
    total_size = work_file.stat().st_size
    chunker.CHUNK_SIZE = MAX_UPLOAD_BYTES
    chunks = chunker.split_file(work_file)
    num_chunks = len(chunks)
    print(f"[chunked] File {total_size} bytes split into {num_chunks} chunks of <= {MAX_UPLOAD_BYTES} bytes")

    if task_id:
        progress.create(task_id, path.name, total_size, kind="upload")

    cb = _make_cb(task_id) if task_id else None

    chunk_msg_ids = []
    uploaded_bytes = 0

    try:
        for i, chunk_path in enumerate(chunks):
            chunk_size = chunk_path.stat().st_size
            uploaded_before = uploaded_bytes

            def chunk_cb(done=0, total=None, _before=uploaded_before, _size=chunk_size):
                if cb:
                    cb(done=_before + done, total=total_size)

            # Retry each chunk up to 3 times
            last_err = None
            msg = None
            for attempt in range(3):
                try:
                    # Get a FRESH client for each chunk (avoid session reuse issues)
                    client = await client_manager._get_client()
                    uploaded_file = await upload_parallel(
                        client=client,
                        file_path=chunk_path,
                        progress_cb=chunk_cb,
                        num_workers=4,
                    )
                    msg = await client.send_file(
                        channel_id,
                        uploaded_file,
                        caption=f"zzodrive:{remote_path}.part{i+1:03d}",
                        force_document=True,
                    )
                    last_err = None
                    break
                except Exception as e:
                    last_err = e
                    print(f"[chunked] chunk {i+1} attempt {attempt+1} failed: {e}")
                    if attempt < 2:
                        # Reset client and wait
                        try:
                            await client_manager._close_client()
                        except Exception:
                            pass
                        await asyncio.sleep(3 * (attempt + 1))

            if last_err is not None:
                raise last_err

            chunk_msg_ids.append(msg.id)
            uploaded_bytes += chunk_size
            print(f"[chunked] chunk {i+1}/{num_chunks} done (msg_id={msg.id})")

            if num_chunks > 1:
                chunk_path.unlink(missing_ok=True)

            if i < num_chunks - 1:
                await asyncio.sleep(2.0)

        if task_id:
            progress.complete(task_id, "done")

        return chunk_msg_ids, total_size
    except Exception as e:
        if task_id:
            progress.complete(task_id, "error", str(e))
        raise
    finally:
        if tmp_enc and tmp_enc.exists():
            tmp_enc.unlink()


async def _download_chunked(entry, dest_path, task_id=None):
    """Download a chunked file and merge it (with retry per chunk)."""
    import tempfile
    import shutil

    channel_id = int(config.get("ZZODRIVE_CHANNEL_ID"))
    chunks = entry.get("chunks") or []
    if not chunks:
        raise ValueError("No chunks info")

    total_size = entry.get("size", 0)
    name = entry.get("name", "file")

    if task_id:
        progress.create(task_id, name, total_size, kind="download")
    cb = _make_cb(task_id) if task_id else None

    tmp_dir = Path(tempfile.mkdtemp(prefix="zzodrive-chunks-dl-"))
    chunk_paths = []
    downloaded = 0

    try:
        for i, chunk_msg_id in enumerate(chunks):
            chunk_path = tmp_dir / f"part{i+1:03d}"

            # Retry each chunk up to 5 times
            last_err = None
            success = False
            for attempt in range(5):
                try:
                    # Fresh client for each retry
                    client = await client_manager._get_client()
                    msg = await client.get_messages(channel_id, ids=chunk_msg_id)
                    if not msg or not msg.document:
                        raise FileNotFoundError(f"Chunk {i+1} not found")

                    # Use Telethon's native download (more reliable)
                    # Check if chunk_path is a directory (bug from prev attempt)
                    if chunk_path.exists() and chunk_path.is_dir():
                        import shutil
                        shutil.rmtree(chunk_path, ignore_errors=True)
                    await client.download_media(msg, file=str(chunk_path))
                    last_err = None
                    success = True
                    break
                except Exception as e:
                    last_err = e
                    print(f"[chunked-dl] chunk {i+1} attempt {attempt+1} failed: {e}")
                    # Partial file from failed attempt — remove it
                    try:
                        chunk_path.unlink(missing_ok=True)
                    except Exception:
                        pass
                    # Reset client connection
                    try:
                        await client_manager._close_client()
                    except Exception:
                        pass
                    if attempt < 4:
                        await asyncio.sleep(3 * (attempt + 1))

            if not success:
                raise last_err or RuntimeError(f"chunk {i+1} failed")

            csize = chunk_path.stat().st_size
            downloaded += csize
            print(f"[chunked-dl] chunk {i+1}/{len(chunks)} done ({csize} bytes)")
            if cb:
                cb(done=downloaded, total=total_size)
            chunk_paths.append(chunk_path)

            # Pause between chunks
            if i < len(chunks) - 1:
                await asyncio.sleep(1.5)

        # Merge
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if entry.get("encrypted"):
            merged_enc = tmp_dir / "merged.enc"
            chunker.merge_files(chunk_paths, merged_enc)
            pwd = config.get("ZZODRIVE_PASSWORD")
            if not pwd:
                raise ValueError("Encrypted file but no password")
            crypto.decrypt_file(merged_enc, dest_path, pwd)
        else:
            chunker.merge_files(chunk_paths, dest_path)

        print(f"[chunked-dl] merged -> {dest_path}")
        if task_id:
            progress.complete(task_id, "done")
    except Exception as e:
        if task_id:
            progress.complete(task_id, "error", str(e))
        raise
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


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
            # Save to cache (non-encrypted only)
            try:
                if entry and not entry.get("chunks"):
                    cache.cache.put(f"file_{msg_id}", dest_path)
            except Exception as _ce:
                print(f"[cache] put failed: {_ce}")

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
    size = path.stat().st_size

    if size > MAX_UPLOAD_BYTES:
        # Chunked
        chunk_ids, up_size = _run(
            _upload_chunked(path, remote_path, encrypted, task_id)
        )
        index.add(chunk_ids[0], path.name, up_size, remote_path=remote_path,
                  md5=md5, encrypted=encrypted, original_size=orig,
                  chunks=chunk_ids)
        return chunk_ids[0]
    else:
        msg_id, up_size = _run(_upload(path, remote_path, encrypted, task_id=task_id))
        index.add(msg_id, path.name, up_size, remote_path=remote_path,
                  md5=md5, encrypted=encrypted, original_size=orig)
        return msg_id


def download_file(msg_id: int, output: Path, task_id=None):
    _run(_download_to_file(msg_id, output, task_id=task_id))
    return output


def download_to_file(msg_id: int, dest_path, task_id=None):
    dest_path = Path(dest_path)
    entry = index.find(msg_id)
    if entry and entry.get("chunks"):
        _run(_download_chunked(entry, dest_path, task_id=task_id))
    else:
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
