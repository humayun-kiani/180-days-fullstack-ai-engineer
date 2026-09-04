# tests/test_health.py
import pytest
import asyncio
from app.health.checks import HealthChecker, CheckResult, check_memory


def _healthy_check() -> CheckResult:
    return CheckResult("test", "healthy", "All good", 1.0)


def _unhealthy_check() -> CheckResult:
    return CheckResult("bad", "unhealthy", "Failed", 1.0)


def _degraded_check() -> CheckResult:
    return CheckResult("warn", "degraded", "Warning", 1.0)


class TestHealthChecker:
    def test_all_healthy(self):
        checker = HealthChecker()
        checker.add_check(_healthy_check)
        result = asyncio.run(checker.run_all())
        assert result["status"] == "healthy"

    def test_unhealthy_if_critical_fails(self):
        checker = HealthChecker()
        checker.add_check(_unhealthy_check, critical=True)
        result = asyncio.run(checker.run_all())
        assert result["status"] == "unhealthy"

    def test_degraded_if_noncritical_fails(self):
        checker = HealthChecker()
        checker.add_check(_healthy_check, critical=True)
        checker.add_check(_degraded_check, critical=False)
        result = asyncio.run(checker.run_all())
        assert result["status"] == "degraded"

    def test_contains_check_results(self):
        checker = HealthChecker()
        checker.add_check(_healthy_check)
        result = asyncio.run(checker.run_all())
        assert "checks" in result
        assert len(result["checks"]) == 1

    def test_memory_check_returns_result(self):
        result = check_memory()
        assert result.name == "memory"
        assert result.status in ("healthy", "degraded", "unhealthy")
        assert result.duration_ms >= 0