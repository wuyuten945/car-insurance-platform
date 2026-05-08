"""
Rate-limit 觀測模組:每次 slowapi 擋下請求都記一筆,可從 admin endpoint 查最近撞牆者。

設計:
  - In-memory rolling buffer(最多 500 筆,夠看最近 1-2 天)
  - 同時維護 hourly aggregate (key → count) 方便看誰常被擋
  - 不持久化到 DB(避免每次撞都寫 DB),足夠日常觀察
"""
from __future__ import annotations

import logging
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# 最多記 500 筆原始事件(最舊的會被擠出去)
_MAX_EVENTS = 500

_lock = threading.Lock()
_events: list[dict] = []
_hourly_counts: dict[str, int] = defaultdict(int)   # f"{key}|{hour_bucket}" → count


def record_hit(*, key: str, path: str, method: str, ip: str, limit: str) -> None:
    """記錄一次 rate-limit 撞牆事件。"""
    now = datetime.now(timezone.utc)
    hour_bucket = now.strftime("%Y-%m-%d %H:00")
    event = {
        "ts": now.isoformat(),
        "key": key,
        "path": path,
        "method": method,
        "ip": ip,
        "limit": limit,
    }
    with _lock:
        _events.append(event)
        if len(_events) > _MAX_EVENTS:
            del _events[: len(_events) - _MAX_EVENTS]
        _hourly_counts[f"{key}|{hour_bucket}"] += 1
        # hourly buckets 太多時清掉超過 24 小時前的
        if len(_hourly_counts) > 5000:
            _gc_old_buckets(now)
    # 結構化 log:方便用 Render log 搜尋
    logger.warning(
        "[rate-limit-hit] key=%s path=%s method=%s ip=%s limit=%s",
        key, path, method, ip, limit,
    )


def _gc_old_buckets(now: datetime) -> None:
    cutoff = now.strftime("%Y-%m-%d %H:00")
    yesterday = (now.timestamp() - 86400)
    keep = {}
    for k, v in _hourly_counts.items():
        try:
            bucket = k.rsplit("|", 1)[1]
            ts = datetime.strptime(bucket, "%Y-%m-%d %H:00").replace(tzinfo=timezone.utc).timestamp()
            if ts > yesterday:
                keep[k] = v
        except Exception:
            pass
    _hourly_counts.clear()
    _hourly_counts.update(keep)


def get_stats(limit: int = 100) -> dict[str, Any]:
    """給 admin endpoint 用:回傳最近 N 筆原始事件 + top offenders。"""
    with _lock:
        events = list(_events[-limit:])
        # 以 key 加總(不分 hour)前 20 名
        per_key: dict[str, int] = defaultdict(int)
        for k, v in _hourly_counts.items():
            key = k.rsplit("|", 1)[0]
            per_key[key] += v
        top = sorted(per_key.items(), key=lambda x: -x[1])[:20]
    return {
        "recent_events": list(reversed(events)),  # 新→舊
        "top_offenders": [{"key": k, "hits": v} for k, v in top],
        "total_events_buffered": len(events),
        "now": datetime.now(timezone.utc).isoformat(),
    }


def clear_stats() -> None:
    """清空(super_admin debug 用)"""
    with _lock:
        _events.clear()
        _hourly_counts.clear()
