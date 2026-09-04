# app/metrics/registry.py
# Prometheus-compatible metrics registry

import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


# ── Counter ───────────────────────────────────────────────────

class Counter:
    """Always-increasing metric. Use for: requests, errors, bytes."""

    def __init__(self, name: str, description: str, labels: list[str] = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0, **labels) -> None:
        key = tuple(labels.get(l, "") for l in self.label_names)
        with self._lock:
            self._values[key] += amount

    def get(self, **labels) -> float:
        key = tuple(labels.get(l, "") for l in self.label_names)
        return self._values.get(key, 0.0)

    def get_all(self) -> dict:
        return dict(self._values)


# ── Gauge ─────────────────────────────────────────────────────

class Gauge:
    """Can go up or down. Use for: connections, memory, queue depth."""

    def __init__(self, name: str, description: str, labels: list[str] = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()

    def set(self, value: float, **labels) -> None:
        key = tuple(labels.get(l, "") for l in self.label_names)
        with self._lock:
            self._values[key] = value

    def inc(self, amount: float = 1.0, **labels) -> None:
        key = tuple(labels.get(l, "") for l in self.label_names)
        with self._lock:
            self._values[key] += amount

    def dec(self, amount: float = 1.0, **labels) -> None:
        key = tuple(labels.get(l, "") for l in self.label_names)
        with self._lock:
            self._values[key] -= amount

    def get(self, **labels) -> float:
        key = tuple(labels.get(l, "") for l in self.label_names)
        return self._values.get(key, 0.0)

    def get_all(self) -> dict:
        return dict(self._values)


# ── Histogram ─────────────────────────────────────────────────

class Histogram:
    """
    Distribution of values. Use for: latency, request size.

    Stores counts per bucket for percentile estimation.
    """

    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def __init__(self, name: str, description: str,
                 buckets: list[float] = None,
                 labels: list[str] = None):
        self.name = name
        self.description = description
        self.buckets = sorted(buckets or self.DEFAULT_BUCKETS)
        self.label_names = labels or []
        self._lock = threading.Lock()

        # Per-label-combo tracking
        self._counts: dict[tuple, int] = defaultdict(int)
        self._sums: dict[tuple, float] = defaultdict(float)
        self._bucket_counts: dict[tuple, list[int]] = {}

    def observe(self, value: float, **labels) -> None:
        key = tuple(labels.get(l, "") for l in self.label_names)
        with self._lock:
            self._counts[key] += 1
            self._sums[key] += value
            if key not in self._bucket_counts:
                self._bucket_counts[key] = [0] * len(self.buckets)
            for i, bucket in enumerate(self.buckets):
                if value <= bucket:
                    self._bucket_counts[key][i] += 1

    def percentile(self, p: float, **labels) -> float:
        """Estimate a percentile from bucket data."""
        key = tuple(labels.get(l, "") for l in self.label_names)
        count = self._counts.get(key, 0)
        if count == 0:
            return 0.0
        target = count * (p / 100.0)
        bucket_counts = self._bucket_counts.get(key, [])
        cumulative = 0
        for i, bc in enumerate(bucket_counts):
            cumulative += bc
            if cumulative >= target:
                return self.buckets[i]
        return self.buckets[-1]

    def get_stats(self, **labels) -> dict:
        key = tuple(labels.get(l, "") for l in self.label_names)
        count = self._counts.get(key, 0)
        total = self._sums.get(key, 0.0)
        return {
            "count": count,
            "sum": round(total, 6),
            "avg": round(total / count, 6) if count > 0 else 0,
            "p50": self.percentile(50, **labels),
            "p95": self.percentile(95, **labels),
            "p99": self.percentile(99, **labels),
        }

    def get_all_stats(self) -> dict:
        results = {}
        for key in self._counts:
            label_dict = dict(zip(self.label_names, key))
            results[str(label_dict) if label_dict else "default"] = self.get_stats(**label_dict)
        return results


# ── Registry ──────────────────────────────────────────────────

class MetricsRegistry:
    """
    Central registry for all metrics.
    Handles Prometheus text format export.
    """

    def __init__(self):
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}
        self._start_time = time.time()

    def counter(self, name: str, description: str,
                labels: list[str] = None) -> Counter:
        if name not in self._counters:
            self._counters[name] = Counter(name, description, labels)
        return self._counters[name]

    def gauge(self, name: str, description: str,
              labels: list[str] = None) -> Gauge:
        if name not in self._gauges:
            self._gauges[name] = Gauge(name, description, labels)
        return self._gauges[name]

    def histogram(self, name: str, description: str,
                  buckets: list[float] = None,
                  labels: list[str] = None) -> Histogram:
        if name not in self._histograms:
            self._histograms[name] = Histogram(name, description, buckets, labels)
        return self._histograms[name]

    def prometheus_format(self) -> str:
        """Export all metrics in Prometheus text format."""
        lines = []

        # Process time (uptime)
        lines.append(f"# HELP process_uptime_seconds Time since service start")
        lines.append(f"# TYPE process_uptime_seconds gauge")
        lines.append(f"process_uptime_seconds {time.time() - self._start_time:.1f}")

        for name, c in self._counters.items():
            lines.append(f"\n# HELP {name} {c.description}")
            lines.append(f"# TYPE {name} counter")
            for key, value in c.get_all().items():
                if c.label_names and key:
                    label_str = ",".join(
                        f'{ln}="{lv}"'
                        for ln, lv in zip(c.label_names, key)
                        if lv
                    )
                    lines.append(f'{name}{{{label_str}}} {value}')
                else:
                    lines.append(f'{name} {value}')

        for name, g in self._gauges.items():
            lines.append(f"\n# HELP {name} {g.description}")
            lines.append(f"# TYPE {name} gauge")
            for key, value in g.get_all().items():
                if g.label_names and key:
                    label_str = ",".join(
                        f'{ln}="{lv}"'
                        for ln, lv in zip(g.label_names, key)
                        if lv
                    )
                    lines.append(f'{name}{{{label_str}}} {value}')
                else:
                    lines.append(f'{name} {value}')

        for name, h in self._histograms.items():
            lines.append(f"\n# HELP {name} {h.description}")
            lines.append(f"# TYPE {name} histogram")
            for key in h._counts:
                label_dict = dict(zip(h.label_names, key)) if h.label_names else {}
                label_str = ",".join(f'{k}="{v}"' for k, v in label_dict.items())
                prefix = f'{name}{{{label_str}}}' if label_str else name

                bucket_counts = h._bucket_counts.get(key, [])
                for i, bucket in enumerate(h.buckets):
                    bc = bucket_counts[i] if i < len(bucket_counts) else 0
                    if label_str:
                        lines.append(f'{name}_bucket{{{label_str},le="{bucket}"}} {bc}')
                    else:
                        lines.append(f'{name}_bucket{{le="{bucket}"}} {bc}')
                lines.append(f'{prefix}_sum {h._sums.get(key, 0):.6f}')
                lines.append(f'{prefix}_count {h._counts.get(key, 0)}')

        return "\n".join(lines) + "\n"

    def get_summary(self) -> dict:
        """Return a JSON-friendly summary of all metrics."""
        summary = {
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "counters": {},
            "gauges": {},
            "histograms": {}
        }

        for name, c in self._counters.items():
            all_vals = c.get_all()
            if len(all_vals) == 1 and not c.label_names:
                summary["counters"][name] = list(all_vals.values())[0]
            else:
                summary["counters"][name] = {
                    str(dict(zip(c.label_names, k))): v
                    for k, v in all_vals.items()
                }

        for name, g in self._gauges.items():
            all_vals = g.get_all()
            if len(all_vals) <= 1 and not g.label_names:
                summary["gauges"][name] = list(all_vals.values())[0] if all_vals else 0
            else:
                summary["gauges"][name] = {
                    str(dict(zip(g.label_names, k))): v
                    for k, v in all_vals.items()
                }

        for name, h in self._histograms.items():
            summary["histograms"][name] = h.get_all_stats()

        return summary


# Global registry instance
registry = MetricsRegistry()