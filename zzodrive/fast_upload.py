"""Custom parallel uploader for zzoDrive.

Features:
  - Parallel parts with configurable workers
  - Retry with exponential backoff
  - FloodWait handling
  - Precise progress
"""
import asyncio
import hashlib
import math
import os
import time
from pathlib import Path

from telethon.errors import FloodWaitError
from telethon.tl.functions.upload import SaveFilePartRequest, SaveBigFilePartRequest
from telethon.tl.types import InputFileBig, InputFile

MAX_CHUNK = 512 * 1024           # 512 KiB per part
BIG_FILE_THRESHOLD = 10 * 1024 * 1024
MAX_PARALLEL = 16
DEFAULT_WORKERS = 8
MAX_RETRIES = 5
BASE_BACKOFF = 1.5               # seconds


async def upload_parallel(client, file_path, progress_cb=None, num_workers=DEFAULT_WORKERS):
    """Upload a file with parallel parts, retry, and FloodWait handling."""
    file_path = Path(file_path)
    file_size = file_path.stat().st_size
    file_id = int.from_bytes(os.urandom(8), "big", signed=True)

    is_big = file_size > BIG_FILE_THRESHOLD
    if is_big:
        upload_file = InputFileBig(id=file_id, parts=0, name=file_path.name)
    else:
        md5 = _md5_of_file(file_path)
        upload_file = InputFile(
            id=file_id, parts=0, name=file_path.name, md5_checksum=md5,
        )

    total_parts = max(1, math.ceil(file_size / MAX_CHUNK))
    uploaded_bytes = 0
    lock = asyncio.Lock()

    sem = asyncio.Semaphore(num_workers)
    errors = []

    async def upload_one_part(part_num):
        nonlocal uploaded_bytes
        async with sem:
            offset = part_num * MAX_CHUNK
            with open(file_path, "rb") as f:
                f.seek(offset)
                chunk = f.read(MAX_CHUNK)

            if not chunk:
                return

            attempt = 0
            while True:
                attempt += 1
                try:
                    if is_big:
                        req = SaveBigFilePartRequest(
                            file_id=file_id,
                            file_part=part_num,
                            file_total_parts=total_parts,
                            bytes=chunk,
                        )
                    else:
                        req = SaveFilePartRequest(
                            file_id=file_id,
                            file_part=part_num,
                            bytes=chunk,
                        )
                    await client(req)

                    async with lock:
                        uploaded_bytes += len(chunk)
                        if progress_cb:
                            try:
                                progress_cb(done=uploaded_bytes, total=file_size)
                            except Exception:
                                pass
                    return

                except FloodWaitError as e:
                    wait = getattr(e, "seconds", 5)
                    print(f"[upload] FloodWait {wait}s on part {part_num}")
                    await asyncio.sleep(wait)

                except Exception as e:
                    if attempt >= MAX_RETRIES:
                        errors.append((part_num, str(e)))
                        return
                    backoff = BASE_BACKOFF * (2 ** (attempt - 1))
                    print(f"[upload] part {part_num} error (try {attempt}): {e} — retry in {backoff:.1f}s")
                    await asyncio.sleep(backoff)

    tasks = [upload_one_part(i) for i in range(total_parts)]
    await asyncio.gather(*tasks)

    if errors:
        first = errors[0]
        raise RuntimeError(
            f"{len(errors)} of {total_parts} parts failed. "
            f"First: part {first[0]}: {first[1]}"
        )

    upload_file.parts = total_parts
    return upload_file


def _md5_of_file(path, chunk=1024 * 1024):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            c = f.read(chunk)
            if not c:
                break
            h.update(c)
    return h.hexdigest()
