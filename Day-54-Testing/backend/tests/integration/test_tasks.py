# backend/tests/integration/test_tasks.py
import pytest
import uuid


@pytest.mark.integration
class TestCreateTask:
    def test_create_task_success(self, client, auth_headers):
        response = client.post("/api/tasks", json={
            "title": "Fix login bug",
            "priority": "high"
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Fix login bug"
        assert data["priority"] == "high"
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data

    def test_create_task_defaults(self, client, auth_headers):
        response = client.post("/api/tasks", json={
            "title": "Minimal task"
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["priority"] == "medium"
        assert data["status"] == "pending"
        assert data["description"] is None

    def test_create_task_with_description(self, client, auth_headers):
        response = client.post("/api/tasks", json={
            "title": "Task with context",
            "description": "This has a detailed description",
            "priority": "low"
        }, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["description"] == "This has a detailed description"

    def test_create_task_empty_title_fails(self, client, auth_headers):
        response = client.post("/api/tasks", json={
            "title": ""
        }, headers=auth_headers)
        assert response.status_code == 422

    def test_create_task_title_too_long_fails(self, client, auth_headers):
        response = client.post("/api/tasks", json={
            "title": "x" * 501
        }, headers=auth_headers)
        assert response.status_code == 422

    @pytest.mark.parametrize("priority", ["urgent", "high", "medium", "low"])
    def test_create_task_all_priorities(self, client, auth_headers, priority):
        response = client.post("/api/tasks", json={
            "title": f"Task with {priority} priority",
            "priority": priority
        }, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["priority"] == priority

    def test_task_belongs_to_creator(self, client, auth_headers, registered_user):
        response = client.post("/api/tasks", json={
            "title": "My personal task"
        }, headers=auth_headers)
        data = response.json()
        assert str(data["owner_id"]) == registered_user["user"]["id"]


@pytest.mark.integration
class TestListTasks:
    @pytest.fixture(autouse=True)
    def create_tasks(self, client, auth_headers):
        """Create a set of tasks for filter/pagination tests."""
        tasks = [
            {"title": "Urgent task", "priority": "urgent"},
            {"title": "High priority task", "priority": "high"},
            {"title": "Medium task 1", "priority": "medium"},
            {"title": "Medium task 2", "priority": "medium"},
            {"title": "Low priority task", "priority": "low"},
        ]
        for t in tasks:
            client.post("/api/tasks", json=t, headers=auth_headers)

    def test_list_tasks_returns_tasks(self, client, auth_headers):
        response = client.get("/api/tasks", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert data["total"] >= 5

    def test_filter_by_priority(self, client, auth_headers):
        response = client.get("/api/tasks?priority=urgent", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(t["priority"] == "urgent" for t in data["tasks"])

    def test_filter_by_status(self, client, auth_headers):
        response = client.get("/api/tasks?status=pending", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(t["status"] == "pending" for t in data["tasks"])

    def test_pagination_returns_correct_page_size(self, client, auth_headers):
        response = client.get("/api/tasks?per_page=2&page=1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["per_page"] == 2
        assert data["page"] == 1

    def test_pagination_page_count(self, client, auth_headers):
        response = client.get("/api/tasks?per_page=2", headers=auth_headers)
        data = response.json()
        assert data["pages"] == (data["total"] + 1) // 2

    def test_tasks_isolated_between_users(self, client, user_data_2):
        """User B cannot see User A's tasks."""
        import uuid
        user2 = {**user_data_2, "email": f"user2_{uuid.uuid4().hex[:8]}@test.com"}
        reg_response = client.post("/api/auth/register", json=user2)
        token2 = reg_response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        response = client.get("/api/tasks", headers=headers2)
        data = response.json()
        # User B should have 0 tasks (none created)
        assert data["total"] == 0


@pytest.mark.integration
class TestUpdateTask:
    def test_update_status(self, client, auth_headers, created_task):
        response = client.patch(
            f"/api/tasks/{created_task['id']}",
            json={"status": "in_progress"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"

    def test_update_priority(self, client, auth_headers, created_task):
        response = client.patch(
            f"/api/tasks/{created_task['id']}",
            json={"priority": "urgent"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["priority"] == "urgent"

    def test_update_title(self, client, auth_headers, created_task):
        new_title = "Updated task title"
        response = client.patch(
            f"/api/tasks/{created_task['id']}",
            json={"title": new_title},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == new_title

    def test_update_nonexistent_task_returns_404(self, client, auth_headers):
        fake_id = str(uuid.uuid4())
        response = client.patch(
            f"/api/tasks/{fake_id}",
            json={"status": "done"},
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_cannot_update_another_users_task(self, client, auth_headers, created_task, user_data_2):
        """Users cannot update tasks they don't own."""
        user2 = {**user_data_2, "email": f"attacker_{uuid.uuid4().hex[:8]}@test.com"}
        reg = client.post("/api/auth/register", json=user2)
        headers2 = {"Authorization": f"Bearer {reg.json()['access_token']}"}

        response = client.patch(
            f"/api/tasks/{created_task['id']}",
            json={"priority": "low"},
            headers=headers2
        )
        assert response.status_code == 404  # Returns 404, not 403 (security: don't reveal existence)


@pytest.mark.integration
class TestDeleteTask:
    def test_delete_task_success(self, client, auth_headers, created_task):
        task_id = created_task["id"]
        response = client.delete(f"/api/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_nonexistent_task_returns_404(self, client, auth_headers):
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/tasks/{fake_id}", headers=auth_headers)
        assert response.status_code == 404