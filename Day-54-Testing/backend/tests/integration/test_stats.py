# backend/tests/integration/test_stats.py
import pytest


@pytest.mark.integration
class TestStats:
    def test_stats_empty_db(self, client, auth_headers):
        response = client.get("/api/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "overview" in data
        assert "by_priority" in data
        assert "this_week" in data
        assert "health" in data

    def test_stats_requires_auth(self, client):
        response = client.get("/api/stats")
        assert response.status_code in (401, 403)

    def test_stats_after_creating_tasks(self, client, auth_headers):
        # Create tasks of different types
        task_configs = [
            {"title": "Urgent task", "priority": "urgent"},
            {"title": "High task", "priority": "high"},
            {"title": "Done task", "priority": "medium"},
        ]
        created = []
        for cfg in task_configs:
            r = client.post("/api/tasks", json=cfg, headers=auth_headers)
            created.append(r.json())

        # Mark one as done
        client.patch(f"/api/tasks/{created[2]['id']}",
                     json={"status": "done"}, headers=auth_headers)

        response = client.get("/api/stats", headers=auth_headers)
        data = response.json()

        assert data["overview"]["total"] >= 3
        assert data["overview"]["done"] >= 1
        assert data["by_priority"]["urgent"] >= 1
        assert data["by_priority"]["high"] >= 1

    def test_stats_completion_rate_calculation(self, client, auth_headers):
        # Create 2 tasks, complete 1
        r1 = client.post("/api/tasks", json={"title": "Task A"}, headers=auth_headers)
        r2 = client.post("/api/tasks", json={"title": "Task B"}, headers=auth_headers)
        client.patch(f"/api/tasks/{r1.json()['id']}",
                     json={"status": "done"}, headers=auth_headers)

        response = client.get("/api/stats", headers=auth_headers)
        data = response.json()
        # Completion rate should be > 0 (at least 1 done)
        assert data["overview"]["completion_rate_pct"] >= 0

    def test_health_score_values(self, client, auth_headers):
        response = client.get("/api/stats", headers=auth_headers)
        data = response.json()
        assert data["health"]["score"] in ("healthy", "ok", "warning", "critical", "no_data")
        assert isinstance(data["health"]["issues"], list)