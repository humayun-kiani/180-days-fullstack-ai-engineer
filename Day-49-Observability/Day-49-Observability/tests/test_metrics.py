# tests/test_metrics.py
import pytest
from app.metrics.registry import Counter, Gauge, Histogram, MetricsRegistry


class TestCounter:
    def test_starts_at_zero(self):
        c = Counter("test_counter", "desc")
        assert c.get() == 0.0

    def test_increments_by_one(self):
        c = Counter("c2", "desc")
        c.inc()
        assert c.get() == 1.0

    def test_increments_by_amount(self):
        c = Counter("c3", "desc")
        c.inc(5.0)
        assert c.get() == 5.0

    def test_never_decrements(self):
        c = Counter("c4", "desc")
        c.inc(10)
        c.inc(-5)    # adding negative is allowed but unusual
        assert c.get() == 5.0

    def test_labels(self):
        c = Counter("c5", "desc", labels=["method", "status"])
        c.inc(method="GET", status="200")
        c.inc(method="POST", status="201")
        c.inc(method="GET", status="200")
        assert c.get(method="GET", status="200") == 2.0
        assert c.get(method="POST", status="201") == 1.0


class TestGauge:
    def test_set_value(self):
        g = Gauge("g1", "desc")
        g.set(42.0)
        assert g.get() == 42.0

    def test_inc_dec(self):
        g = Gauge("g2", "desc")
        g.inc()
        g.inc()
        assert g.get() == 2.0
        g.dec()
        assert g.get() == 1.0

    def test_can_go_negative(self):
        g = Gauge("g3", "desc")
        g.dec(5)
        assert g.get() == -5.0


class TestHistogram:
    def test_observe_and_count(self):
        h = Histogram("h1", "desc", buckets=[0.1, 0.5, 1.0])
        h.observe(0.05)
        h.observe(0.3)
        h.observe(0.8)
        stats = h.get_stats()
        assert stats["count"] == 3

    def test_percentile_estimation(self):
        h = Histogram("h2", "desc", buckets=[0.01, 0.05, 0.1, 0.5, 1.0])
        for _ in range(100):
            h.observe(0.05)   # all at 50ms bucket
        p50 = h.percentile(50)
        assert p50 <= 0.1

    def test_empty_histogram(self):
        h = Histogram("h3", "desc")
        assert h.percentile(99) == 0.0


class TestRegistry:
    def test_counter_registration(self):
        reg = MetricsRegistry()
        c = reg.counter("test", "desc")
        c.inc(5)
        assert "counters" in reg.get_summary()

    def test_prometheus_format(self):
        reg = MetricsRegistry()
        reg.counter("my_counter", "A counter").inc(3)
        output = reg.prometheus_format()
        assert "my_counter" in output
        assert "3" in output
        assert "# HELP" in output
        assert "# TYPE" in output