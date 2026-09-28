import logging
import time
from collections import Counter, deque
from threading import Lock

logger = logging.getLogger("civiclens")
_recent = deque(maxlen=100)
_counts = Counter()
_lock = Lock()


def _metric_path(path: str) -> str:
    parts = path.strip("/").split("/")
    if len(parts) >= 5 and parts[:3] == ["api", "v1", "history"] and parts[3] == "state":
        return "/api/v1/history/state/{state_ut}"
    return path or "/"

def record_request(path: str, method: str, status: int, duration_ms: float) -> None:
    metric_path = _metric_path(path)
    with _lock:
        _recent.append({"path": metric_path, "method": method, "status": status, "duration_ms": round(duration_ms, 2)})
        _counts[f"{method} {metric_path}"] += 1
    logger.info("request method=%s path=%s status=%s duration_ms=%.2f", method, path, status, duration_ms)


def metrics() -> dict:
    with _lock:
        return {"requests_total": sum(_counts.values()), "routes": dict(_counts), "recent": list(_recent)}


def timer():
    return time.perf_counter()
