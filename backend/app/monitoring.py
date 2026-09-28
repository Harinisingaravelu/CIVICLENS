import logging
import time
from collections import Counter, deque
from threading import Lock

logger = logging.getLogger("civiclens")
_recent = deque(maxlen=100)
_counts = Counter()
_lock = Lock()


def record_request(path: str, method: str, status: int, duration_ms: float) -> None:
    with _lock:
        _recent.append({"path": path, "method": method, "status": status, "duration_ms": round(duration_ms, 2)})
        _counts[f"{method} {path}"] += 1
    logger.info("request method=%s path=%s status=%s duration_ms=%.2f", method, path, status, duration_ms)


def metrics() -> dict:
    with _lock:
        return {"requests_total": sum(_counts.values()), "routes": dict(_counts), "recent": list(_recent)}


def timer():
    return time.perf_counter()
