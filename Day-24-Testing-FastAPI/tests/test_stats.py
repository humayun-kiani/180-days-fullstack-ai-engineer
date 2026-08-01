# ============================================================
# tests/test_stats.py
# Stats and health endpoint tests
# ============================================================

from fastapi.testclient import TestClient


class TestStats:
    def test_health_check(self, client: TestClient):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert "timestamp" in body
        assert "version" in body

    def test_stats_unauthenticated(self, client: TestClient):
        response = client.get("/api/v1/stats")
        assert response.status_code == 401

    def test_stats_authenticated(
        self, client: TestClient, admin_headers, tasks_variety
    ):
        response = client.get("/api/v1/stats", headers=admin_headers)
        assert response.status_code == 200
        body = response.json()
        assert "total_tasks" in body
        assert "tasks_by_status" in body
        assert "tasks_by_priority" in body
        assert "completion_rate_pct" in body
        assert "overdue_tasks" in body

    def test_stats_reflect_task_count(
        self, client: TestClient, admin_headers, tasks_variety
    ):
        response = client.get("/api/v1/stats", headers=admin_headers)
        body = response.json()
        # tasks_variety creates 7 tasks (including 1 archived that counts)
        assert body["total_tasks"] >= 7

    def test_completion_rate_calculation(
        self, client: TestClient, admin_headers, tasks_variety
    ):
        response = client.get("/api/v1/stats", headers=admin_headers)
        body = response.json()
        # 2 done out of 7 = ~28.5%
        assert 0 <= body["completion_rate_pct"] <= 100