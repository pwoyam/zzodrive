"""Split/merge large files for Telegram's 2GB limit."""
import math
import tempfile
from pathlib import Path

CHUNK_SIZE = 1900000000  # ~1.9 GB


def split_file(file_path, output_dir=None):
    """Split file if > CHUNK_SIZE. Returns list of chunk paths."""
    file_path = Path(file_path)
    size = file_path.stat().st_size
    if size <= CHUNK_SIZE:
        return [file_path]
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="zzodrive-chunks-"))
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    chunks = []
    n = math.ceil(size / CHUNK_SIZE)
    for i in range(n):
        start = i * CHUNK_SIZE
        end = min(start + CHUNK_SIZE, size)
        name = file_path.name + ".part" + str(i + 1).zfill(3)
        chunk_path = output_dir / name
        with open(file_path, "rb") as src, open(chunk_path, "wb") as dst:
            src.seek(start)
            remaining = end - start
            while remaining > 0:
                buf = src.read(min(8 * 1024 * 1024, remaining))
                if not buf:
                    break
                dst.write(buf)
                remaining -= len(buf)
        chunks.append(chunk_path)
    return chunks


def merge_files(chunk_paths, output_path):
    """Merge chunk files back into a single file."""
    output_path = Path(output_path)
    with open(output_path, "wb") as dst:
        for p in chunk_paths:
            with open(p, "rb") as src:
                while True:
                    buf = src.read(8 * 1024 * 1024)
                    if not buf:
                        break
                    dst.write(buf)
    return output_path


def is_chunk_name(name):
    """Check if a filename looks like a chunk part."""
    if ".part" not in name:
        return False
    tail = name.rsplit(".part", 1)[-1]
    head = tail.split(".")[0]
    return head.isdigit()


def original_name(chunk_name):
    """Get original filename from a chunk name."""
    return chunk_name.rsplit(".part", 1)[0]
