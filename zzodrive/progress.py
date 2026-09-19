"""Thread-safe progress tracker for uploads and downloads."""
import threading
import time

_tasks = {}
_lock = threading.Lock()


def create(task_id, name, total_bytes, kind="upload"):
    """Create a new task entry."""
    with _lock:
        _tasks[task_id] = {
            "task_id": task_id,
            "name": name,
            "total": total_bytes,
            "current": 0,
            "kind": kind,
            "started_at": time.time(),
            "finished_at": None,
            "speed": 0.0,
            "percent": 0.0,
            "status": "running",
            "error": None,
        }


def update(task_id, current, total=None):
    """Update progress. Called frequently from the upload/download loop."""
    with _lock:
        t = _tasks.get(task_id)
        if not t:
            return
        t["current"] = int(current)
        if total:
            t["total"] = int(total)
        elapsed = time.time() - t["started_at"]
        if elapsed > 0.05:
            t["speed"] = t["current"] / elapsed
        if t["total"] > 0:
            t["percent"] = min(100.0, (t["current"] / t["total"]) * 100)


def complete(task_id, status="done", error=None):
    with _lock:
        t = _tasks.get(task_id)
        if not t:
            return
        t["status"] = status
        t["error"] = error
        t["finished_at"] = time.time()
        if status == "done":
            t["percent"] = 100.0


def get(task_id):
    with _lock:
        t = _tasks.get(task_id)
        return dict(t) if t else None


def cleanup_old(max_age=3600):
    now = time.time()
    with _lock:
        dead = [k for k, v in _tasks.items()
                if v.get("finished_at") and (now - v["finished_at"]) > max_age]
        for k in dead:
            del _tasks[k]
