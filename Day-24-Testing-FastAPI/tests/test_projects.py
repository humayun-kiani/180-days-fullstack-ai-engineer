# ============================================================
# tests/test_projects.py
# Project CRUD endpoint tests
# ============================================================

import pytest
from fastapi.testclient import TestClient


class TestProjectCRUD:
    """Full CRUD for projects."""

    def test_list_projects_authenticated(
        self, client: TestClient, admin_headers, sample_project
    ):
        response = client.get("/api/v1/projects", headers=admin_headers)
        assert response.status_code == 200
        body = response.json()
        assert "items" in body
        assert body["total"] >= 1

    def test_create_project(self, client: TestClient, admin_headers):
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "Brand New Project",
                "description": "Created in a test",
                "color": "#EF4444"
            },
            headers=admin_headers
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Brand New Project"
        assert body["color"] == "#EF4444"
        assert body["status"] == "active"

    def test_create_project_invalid_color(
        self, client: TestClient, admin_headers
    ):
        response = client.post(
            "/api/v1/projects",
            json={"name": "Bad Color", "color": "red"},    # not hex
            headers=admin_headers
        )
        assert response.status_code == 422

    def test_get_project_with_task_counts(
        self, client: TestClient, admin_headers,
        sample_project, sample_task
    ):
        response = client.get(
            f"/api/v1/projects/{sample_project.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        body = response.json()
        assert body["task_count"] >= 1

    def test_update_project_status(
        self, client: TestClient, admin_headers, sample_project
    ):
        response = client.put(
            f"/api/v1/projects/{sample_project.id}",
            json={"status": "completed"},
            headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_delete_project_requires_admin(
        self, client: TestClient, user_headers, sample_project
    ):
        response = client.delete(
            f"/api/v1/projects/{sample_project.id}",
            headers=user_headers
        )
        assert response.status_code == 403

    def test_delete_project_as_admin(
        self, client: TestClient, admin_headers, sample_project
    ):
        response = client.delete(
            f"/api/v1/projects/{sample_project.id}",
            headers=admin_headers
        )
        assert response.status_code == 204

    def test_get_project_tasks(
        self, client: TestClient, admin_headers,
        sample_project, sample_task
    ):
        response = client.get(
            f"/api/v1/projects/{sample_project.id}/tasks",
            headers=admin_headers
        )
        assert response.status_code == 200
        tasks = response.json()
        assert isinstance(tasks, list)
        assert len(tasks) >= 1

    def test_get_nonexistent_project(
        self, client: TestClient, admin_headers
    ):
        response = client.get(
            "/api/v1/projects/999999",
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_get_project_stats(
        self, client: TestClient, admin_headers,
        sample_project, tasks_variety
    ):
        response = client.get(
            f"/api/v1/projects/{sample_project.id}/stats",
            headers=admin_headers
        )
        assert response.status_code == 200
        body = response.json()
        assert "total_tasks" in body
        assert "completion_pct" in body