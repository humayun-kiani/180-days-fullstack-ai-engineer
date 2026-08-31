# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import tasks as task_store


@pytest.fixture(autouse=True)
def clean_db():
    task_store.clear_all()
    yield
    task_store.clear_all()


@pytest.fixture
def client():
    return TestClient(app)


class TestHealth:
    def test_health_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_structure(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "task_count" in data

    def test_readiness_returns_200(self, client):
        r = client.get("/ready")
        assert r.status_code == 200
        assert r.json()["ready"] is True


class TestTaskCRUD:
    def test_create_task(self, client):
        r = client.post("/tasks", json={"title": "Test task"})
        assert r.status_code == 201
        assert r.json()["title"] == "Test task"
        assert r.json()["status"] == "pending"

    def test_list_tasks(self, client):
        client.post("/tasks", json={"title": "T1"})
        client.post("/tasks", json={"title": "T2"})
        r = client.get("/tasks")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_task(self, client):
        created = client.post("/tasks", json={"title": "Get me"}).json()
        r = client.get(f"/tasks/{created['task_id']}")
        assert r.status_code == 200

    def test_update_task(self, client):
        created = client.post("/tasks", json={"title": "Update me"}).json()
        r = client.patch(f"/tasks/{created['task_id']}",
                        json={"status": "done"})
        assert r.status_code == 200
        assert r.json()["status"] == "done"

    def test_delete_task(self, client):
        created = client.post("/tasks", json={"title": "Delete me"}).json()
        r = client.delete(f"/tasks/{created['task_id']}")
        assert r.status_code == 204

    def test_get_missing_task_returns_404(self, client):
        r = client.get("/tasks/task-doesnt-exist")
        assert r.status_code == 404

    def test_filter_by_priority(self, client):
        client.post("/tasks", json={"title": "Urgent", "priority": "urgent"})
        client.post("/tasks", json={"title": "Low", "priority": "low"})
        r = client.get("/tasks?priority=urgent")
        assert len(r.json()) == 1
        assert r.json()[0]["priority"] == "urgent"

    def test_cluster_info_endpoint(self, client):
        r = client.get("/info")
        assert r.status_code == 200
        data = r.json()
        assert "pod_name" in data
        assert "environment" in data