"""Custom parallel uploader for zzoDrive."""
import asyncio
import hashlib
import math
import os
from pathlib import Path

from telethon.tl.functions.upload import SaveFilePartRequest, SaveBigFilePartRequest
from telethon.tl.types import InputFileBig, InputFile

MAX_CHUNK = 512 * 1024
BIG_FILE_THRESHOLD = 10 * 1024 * 1024


async def upload_parallel(client, file_path, progress_cb=None, num_workers=8):
    """Upload a file using parallel SaveFilePart requests."""
    file_path = Path(file_path)
    file_size = file_path.stat().st_size
    file_id = int.from_bytes(os.urandom(8), "big", signed=True)

    is_big = file_size > BIG_FILE_THRESHOLD
    if is_big:
        upload_file = InputFileBig(id=file_id, parts=0, name=file_path.name)
    else:
        md5 = _md5_of_file(file_path)
        upload_file = InputFile(id=file_id, parts=0, name=file_path.name, md5_checksum=md5)

    total_parts = math.ceil(file_size / MAX_CHUNK)
    uploaded = 0
    lock = asyncio.Lock()

    if total_parts == 0:
        return upload_file

    sem = asyncio.Semaphore(num_workers)
    errors = []

    async def upload_part(part_num):
        nonlocal uploaded
        async with sem:
            try:
                with open(file_path, "rb") as f:
                    f.seek(part_num * MAX_CHUNK)
                    chunk = f.read(MAX_CHUNK)

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
                    uploaded += len(chunk)
                    if progress_cb:
                        try:
                            progress_cb(done=uploaded, total=file_size)
                        except Exception:
                            pass
            except Exception as e:
                errors.append((part_num, str(e)))

    tasks = [upload_part(i) for i in range(total_parts)]
    await asyncio.gather(*tasks)

    if errors:
        raise RuntimeError(f"{len(errors)} parts failed. First error: {errors[0][1]}")

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
