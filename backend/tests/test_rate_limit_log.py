"""
Rate-limit 觀測模組:確保 record_hit 真的累積、get_stats 回傳新→舊順序、clear 能清乾淨。
"""
from app.core.rate_limit_log import record_hit, get_stats, clear_stats


class TestRateLimitLog:
    def setup_method(self):
        clear_stats()

    def test_record_and_retrieve(self):
        record_hit(key="tok:abc", path="/foo", method="POST", ip="1.2.3.4", limit="5/hour")
        stats = get_stats()
        assert stats["total_events_buffered"] == 1
        ev = stats["recent_events"][0]
        assert ev["key"] == "tok:abc"
        assert ev["path"] == "/foo"
        assert ev["limit"] == "5/hour"

    def test_top_offenders_aggregates(self):
        for _ in range(3):
            record_hit(key="ip:5.5.5.5", path="/x", method="GET", ip="5.5.5.5", limit="10/min")
        record_hit(key="tok:abc", path="/y", method="POST", ip="1.2.3.4", limit="5/min")
        top = get_stats()["top_offenders"]
        # ip:5.5.5.5 應該排第一(3 hits)
        assert top[0]["key"] == "ip:5.5.5.5"
        assert top[0]["hits"] == 3
        assert top[1]["key"] == "tok:abc"
        assert top[1]["hits"] == 1

    def test_recent_events_newest_first(self):
        record_hit(key="a", path="/1", method="GET", ip="x", limit="x")
        record_hit(key="b", path="/2", method="GET", ip="x", limit="x")
        events = get_stats()["recent_events"]
        assert events[0]["key"] == "b"
        assert events[1]["key"] == "a"

    def test_clear(self):
        record_hit(key="x", path="/p", method="GET", ip="x", limit="x")
        clear_stats()
        stats = get_stats()
        assert stats["total_events_buffered"] == 0
        assert stats["top_offenders"] == []
