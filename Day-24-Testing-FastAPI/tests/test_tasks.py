# ============================================================
# tests/test_tasks.py
# Task CRUD endpoint tests
# ============================================================

import pytest
from fastapi.testclient import TestClient


class TestTaskList:
    """GET /api/v1/tasks"""

    def test_requires_auth(self, client: TestClient):
        assert client.get("/api/v1/tasks").status_code == 401

    def test_returns_paginated_response(
        self, client: TestClient, admin_headers, tasks_variety
    ):
        response = client.get("/api/v1/tasks", headers=admin_headers)
        assert response.status_code == 200
        body = response.json()
        for key in ("items", "total", "page", "per_page", "pages",
                    "has_next", "has_prev"):
            assert key in body

    def test_excludes_soft_deleted_tasks(
        self, client: TestClient, admin_headers, db, sample_task
    ):
        """Soft-deleted tasks don't appear in list."""
        # Soft delete the task
        from app.db.models.task import Task
        task = db.query(Task).filter(Task.id == sample_task.id).first()
        task.is_deleted = True
        db.commit()

        response = client.get("/api/v1/tasks", headers=admin_headers)
        ids = [t["id"] for t in response.json()["items"]]
        assert sample_task.id not in ids

    @pytest.mark.parametrize("status", [
        "pending", "in_progress", "done", "archived"
    ])
    def test_filter_by_status(
        self, client: TestClient, admin_headers, tasks_variety, status: str
    ):
        response = client.get(
            "/api/v1/tasks",
            params={"status": status},
            headers=admin_headers
        )
        assert response.status_code == 200
        items = response.json()["items"]
        assert all(t["status"] == status for t in items)

    @pytest.mark.parametrize("priority", [
        "low", "medium", "high", "urgent"
    ])
    def test_filter_by_priority(
        self, client: TestClient, admin_headers, tasks_variety, priority: str
    ):
        response = client.get(
            "/api/v1/tasks",
            params={"priority": priority},
            headers=admin_headers
        )
        assert response.status_code == 200
        items = response.json()["items"]
        assert all(t["priority"] == priority for t in items)

    def test_search_by_title(
        self, client: TestClient, admin_headers, tasks_variety
    ):
        response = client.get(
            "/api/v1/tasks",
            params={"search": "Urgent"},
            headers=admin_headers
        )
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) >= 1
        assert all("Urgent" in t["title"] or
                   "urgent" in t.get("description", "").lower()
                   for t in items)

    def test_pagination_page_2(
        self, client: TestClient, admin_headers, tasks_variety
    ):
        # Get page 1
        r1 = client.get(
            "/api/v1/tasks",
            params={"page": 1, "per_page": 3},
            headers=admin_headers
        )
        # Get page 2
        r2 = client.get(
            "/api/v1/tasks",
            params={"page": 2, "per_page": 3},
            headers=admin_headers
        )
        ids_p1 = {t["id"] for t in r1.json()["items"]}
        ids_p2 = {t["id"] for t in r2.json()["items"]}
        assert ids_p1.isdisjoint(ids_p2)    # no overlap

    def test_filter_by_project(
        self, client: TestClient, admin_headers,
        tasks_variety, second_project, db, admin_user
    ):
        """Tasks are correctly filtered by project_id."""
        from app.db.models.task import Task
        other_task = Task(
            title="Task in other project",
            status="pending",
            priority="medium",
            project_id=second_project.id,
            owner_id=admin_user.id,
            tags=[],
            is_deleted=False
        )
        db.add(other_task)
        db.commit()

        response = client.get(
            "/api/v1/tasks",
            params={"project_id": second_project.id},
            headers=admin_headers
        )
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["project_id"] == second_project.id

    def test_overdue_filter(
        self, client: TestClient, admin_headers, db, admin_user, sample_project
    ):
        """Overdue filter returns only overdue tasks."""
        from datetime import datetime, timedelta
        from app.db.models.task import Task

        overdue_task = Task(
            title="Overdue Task",
            status="pending",
            priority="high",
            project_id=sample_project.id,
            owner_id=admin_user.id,
            tags=[],
            due_date=datetime.utcnow() - timedelta(days=2),
            is_deleted=False
        )
        db.add(overdue_task)
        db.commit()

        response = client.get(
            "/api/v1/tasks",
            params={"overdue": True},
            headers=admin_headers
        )
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) >= 1
        assert all(t["is_overdue"] for t in items)


class TestCreateTask:
    """POST /api/v1/tasks"""

    def test_create_minimal_task(self, client: TestClient, admin_headers):
        response = client.post(
            "/api/v1/tasks",
            json={"title": "Minimal Task"},
            headers=admin_headers
        )
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Minimal Task"
        assert body["status"] == "pending"
        assert body["priority"] == "medium"

    def test_create_full_task(
        self, client: TestClient, admin_headers, sample_project
    ):
        response = client.post(
            "/api/v1/tasks",
            json={
                "title": "Full Featured Task",
                "description": "With all fields",
                "priority": "urgent",
                "status": "in_progress",
                "project_id": sample_project.id,
                "tags": ["backend", "testing"],
                "estimated_hours": 3.5
            },
            headers=admin_headers
        )
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Full Featured Task"
        assert body["priority"] == "urgent"
        assert body["estimated_hours"] == 3.5
        assert "testing" in body["tags"]

    def test_tags_deduplicated(self, client: TestClient, admin_headers):
        response = client.post(
            "/api/v1/tasks",
            json={"title": "Dedup Tags", "tags": ["test", "TEST", "Test"]},
            headers=admin_headers
        )
        assert response.status_code == 201
        assert len(response.json()["tags"]) == 1    # deduplicated

    def test_tags_lowercased(self, client: TestClient, admin_headers):
        response = client.post(
            "/api/v1/tasks",
            json={"title": "Case Tags", "tags": ["BACKEND", "Frontend"]},
            headers=admin_headers
        )
        assert response.status_code == 201
        tags = response.json()["tags"]
        assert "backend" in tags
        assert "frontend" in tags

    @pytest.mark.parametrize("bad_payload,expected_status", [
        ({}, 422),                                       # missing title
        ({"title": ""}, 422),                            # empty title
        ({"title": "x" * 201}, 422),                    # title too long
        ({"title": "OK", "priority": "super"}, 422),    # invalid priority
        ({"title": "OK", "status": "flying"}, 422),     # invalid status
        ({"title": "OK", "project_id": 99999}, 404),    # project not found
    ])
    def test_create_task_validation(
        self, client: TestClient, admin_headers,
        bad_payload: dict, expected_status: int
    ):
        response = client.post(
            "/api/v1/tasks",
            json=bad_payload,
            headers=admin_headers
        )
        assert response.status_code == expected_status


class TestGetTask:
    """GET /api/v1/tasks/{task_id}"""

    def test_get_existing_task(
        self, client: TestClient, admin_headers, sample_task
    ):
        response = client.get(
            f"/api/v1/tasks/{sample_task.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == sample_task.id
        assert body["title"] == sample_task.title
        assert isinstance(body["tags"], list)

    def test_get_nonexistent_task(self, client: TestClient, admin_headers):
        response = client.get(
            "/api/v1/tasks/999999",
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_get_deleted_task_returns_404(
        self, client: TestClient, admin_headers, db, sample_task
    ):
        """Soft-deleted tasks appear as 404."""
        from app.db.models.task import Task
        task = db.query(Task).filter(Task.id == sample_task.id).first()
        task.is_deleted = True
        db.commit()

        response = client.get(
            f"/api/v1/tasks/{sample_task.id}",
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_get_task_requires_auth(self, client: TestClient, sample_task):
        assert client.get(
            f"/api/v1/tasks/{sample_task.id}"
        ).status_code == 401


class TestUpdateTask:
    """PUT /api/v1/tasks/{task_id}"""

    def test_update_title_only(
        self, client: TestClient, admin_headers, sample_task
    ):
        """Updating title preserves other fields."""
        old_priority = sample_task.priority
        response = client.put(
            f"/api/v1/tasks/{sample_task.id}",
            json={"title": "Brand New Title"},
            headers=admin_headers
        )
        assert response.status_code == 200
        body = response.json()
        assert body["title"] == "Brand New Title"
        assert body["priority"] == old_priority    # unchanged

    @pytest.mark.parametrize("new_status", [
        "pending", "in_progress", "done", "archived"
    ])
    def test_update_status_all_values(
        self, client: TestClient, admin_headers, sample_task, new_status: str
    ):
        response = client.put(
            f"/api/v1/tasks/{sample_task.id}",
            json={"status": new_status},
            headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == new_status

    def test_update_nonexistent_returns_404(
        self, client: TestClient, admin_headers
    ):
        response = client.put(
            "/api/v1/tasks/999999",
            json={"title": "Ghost"},
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_update_tags_replaces_all(
        self, client: TestClient, admin_headers, sample_task
    ):
        response = client.put(
            f"/api/v1/tasks/{sample_task.id}",
            json={"tags": ["new-tag-one", "new-tag-two"]},
            headers=admin_headers
        )
        assert response.status_code == 200
        tags = response.json()["tags"]
        assert set(tags) == {"new-tag-one", "new-tag-two"}


class TestCompleteTask:
    """PATCH /api/v1/tasks/{task_id}/complete"""

    def test_complete_pending_task(
        self, client: TestClient, admin_headers, sample_task
    ):
        response = client.patch(
            f"/api/v1/tasks/{sample_task.id}/complete",
            headers=admin_headers
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "done"

    def test_complete_with_actual_hours(
        self, client: TestClient, admin_headers, sample_task
    ):
        response = client.patch(
            f"/api/v1/tasks/{sample_task.id}/complete",
            params={"actual_hours": 4.5},
            headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["actual_hours"] == 4.5

    def test_cannot_complete_already_done(
        self, client: TestClient, admin_headers, done_task
    ):
        response = client.patch(
            f"/api/v1/tasks/{done_task.id}/complete",
            headers=admin_headers
        )
        assert response.status_code == 409


class TestDeleteTask:
    """DELETE /api/v1/tasks/{task_id}"""

    def test_soft_delete_default(
        self, client: TestClient, admin_headers, sample_task
    ):
        response = client.delete(
            f"/api/v1/tasks/{sample_task.id}",
            headers=admin_headers
        )
        assert response.status_code == 204
        assert not response.content

    def test_task_not_in_list_after_soft_delete(
        self, client: TestClient, admin_headers, sample_task
    ):
        client.delete(f"/api/v1/tasks/{sample_task.id}", headers=admin_headers)
        list_r = client.get("/api/v1/tasks", headers=admin_headers)
        ids = [t["id"] for t in list_r.json()["items"]]
        assert sample_task.id not in ids

    def test_hard_delete_requires_admin(
        self, client: TestClient, user_headers, sample_task
    ):
        response = client.delete(
            f"/api/v1/tasks/{sample_task.id}",
            params={"hard": True},
            headers=user_headers
        )
        assert response.status_code == 403

    def test_hard_delete_admin_success(
        self, client: TestClient, admin_headers, sample_task
    ):
        response = client.delete(
            f"/api/v1/tasks/{sample_task.id}",
            params={"hard": True},
            headers=admin_headers
        )
        assert response.status_code == 204


class TestSpecialEndpoints:
    """Overdue, upcoming, and bulk operations."""

    def test_overdue_endpoint(
        self, client: TestClient, admin_headers, db, admin_user, sample_project
    ):
        from datetime import datetime, timedelta
        from app.db.models.task import Task
        overdue = Task(
            title="I am overdue",
            status="pending",
            priority="high",
            project_id=sample_project.id,
            owner_id=admin_user.id,
            tags=[],
            due_date=datetime.utcnow() - timedelta(days=5),
            is_deleted=False
        )
        db.add(overdue)
        db.commit()

        response = client.get(
            "/api/v1/tasks/overdue",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_upcoming_endpoint(
        self, client: TestClient, admin_headers, db, admin_user, sample_project
    ):
        from datetime import datetime, timedelta
        from app.db.models.task import Task
        upcoming = Task(
            title="Coming soon",
            status="pending",
            priority="medium",
            project_id=sample_project.id,
            owner_id=admin_user.id,
            tags=[],
            due_date=datetime.utcnow() + timedelta(days=3),
            is_deleted=False
        )
        db.add(upcoming)
        db.commit()

        response = client.get(
            "/api/v1/tasks/upcoming",
            params={"days": 7},
            headers=admin_headers
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_bulk_complete(
        self, client: TestClient, admin_headers, tasks_variety
    ):
        pending_ids = [
            t.id for t in tasks_variety
            if t.status == "pending"
        ][:3]

        response = client.post(
            "/api/v1/tasks/bulk/complete",
            json=pending_ids,
            headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["updated"] >= 1

    def test_bulk_complete_empty_list(
        self, client: TestClient, admin_headers
    ):
        response = client.post(
            "/api/v1/tasks/bulk/complete",
            json=[],
            headers=admin_headers
        )
        assert response.status_code == 400

    def test_bulk_complete_too_many(
        self, client: TestClient, admin_headers
    ):
        response = client.post(
            "/api/v1/tasks/bulk/complete",
            json=list(range(1, 52)),    # 51 items
            headers=admin_headers
        )
        assert response.status_code == 400