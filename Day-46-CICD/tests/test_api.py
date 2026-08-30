# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import tasks as task_store


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    task_store.clear_all()
    yield
    task_store.clear_all()


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_has_required_fields(self, client):
        r = client.get("/health")
        data = r.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data


class TestCreateTaskAPI:
    def test_creates_task_returns_201(self, client):
        r = client.post("/tasks", json={"title": "API test task"})
        assert r.status_code == 201

    def test_response_has_task_id(self, client):
        r = client.post("/tasks", json={"title": "Has ID"})
        assert "task_id" in r.json()

    def test_requires_title(self, client):
        r = client.post("/tasks", json={})
        assert r.status_code == 422

    def test_validates_priority_enum(self, client):
        r = client.post("/tasks", json={"title": "Test", "priority": "invalid"})
        assert r.status_code == 422

    def test_accepts_all_priorities(self, client):
        for p in ["urgent", "high", "medium", "low"]:
            r = client.post("/tasks", json={"title": f"Task {p}", "priority": p})
            assert r.status_code == 201
            assert r.json()["priority"] == p

    def test_title_too_long_rejected(self, client):
        r = client.post("/tasks", json={"title": "x" * 301})
        assert r.status_code == 422


class TestListTasksAPI:
    def test_returns_empty_list(self, client):
        r = client.get("/tasks")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_all_tasks(self, client):
        client.post("/tasks", json={"title": "T1"})
        client.post("/tasks", json={"title": "T2"})
        r = client.get("/tasks")
        assert len(r.json()) == 2

    def test_filters_by_priority(self, client):
        client.post("/tasks", json={"title": "Urgent", "priority": "urgent"})
        client.post("/tasks", json={"title": "Low", "priority": "low"})
        r = client.get("/tasks?priority=urgent")
        tasks = r.json()
        assert len(tasks) == 1
        assert tasks[0]["priority"] == "urgent"


class TestGetTaskAPI:
    def test_gets_existing_task(self, client):
        created = client.post("/tasks", json={"title": "Get me"}).json()
        r = client.get(f"/tasks/{created['task_id']}")
        assert r.status_code == 200
        assert r.json()["title"] == "Get me"

    def test_returns_404_for_missing(self, client):
        r = client.get("/tasks/task-doesnt-exist")
        assert r.status_code == 404


class TestUpdateTaskAPI:
    def test_updates_task(self, client):
        created = client.post("/tasks", json={"title": "Original"}).json()
        r = client.patch(
            f"/tasks/{created['task_id']}",
            json={"title": "Updated", "status": "in_progress"}
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Updated"
        assert r.json()["status"] == "in_progress"

    def test_returns_404_for_missing(self, client):
        r = client.patch("/tasks/no-exist", json={"title": "X"})
        assert r.status_code == 404


class TestDeleteTaskAPI:
    def test_deletes_task_returns_204(self, client):
        created = client.post("/tasks", json={"title": "Delete me"}).json()
        r = client.delete(f"/tasks/{created['task_id']}")
        assert r.status_code == 204

    def test_deleted_task_not_found(self, client):
        created = client.post("/tasks", json={"title": "Gone"}).json()
        client.delete(f"/tasks/{created['task_id']}")
        r = client.get(f"/tasks/{created['task_id']}")
        assert r.status_code == 404

    def test_returns_404_for_missing(self, client):
        r = client.delete("/tasks/no-exist")
        assert r.status_code == 404