# backend/tests/integration/test_search.py
import pytest
import uuid


@pytest.mark.integration
class TestSearch:
    @pytest.fixture(autouse=True)
    def seed_tasks(self, client, auth_headers):
        tasks = [
            {"title": "Fix login authentication bug", "priority": "high"},
            {"title": "Add dark mode to dashboard", "priority": "medium"},
            {"title": "URGENT: Database connection failure", "priority": "urgent"},
            {"title": "Write unit tests for payment module", "priority": "medium"},
            {"title": "Update user documentation", "priority": "low"},
        ]
        for t in tasks:
            client.post("/api/tasks", json=t, headers=auth_headers)

    def test_search_by_title_keyword(self, client, auth_headers):
        response = client.get("/api/search?q=login", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("login" in t["title"].lower() for t in data["tasks"])

    def test_search_case_insensitive(self, client, auth_headers):
        response = client.get("/api/search?q=LOGIN", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_search_no_results(self, client, auth_headers):
        response = client.get("/api/search?q=xyznotfound", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_search_empty_query_returns_all(self, client, auth_headers):
        response = client.get("/api/search", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] >= 5

    def test_sort_by_priority(self, client, auth_headers):
        response = client.get("/api/search?sort_by=priority&sort_dir=asc", headers=auth_headers)
        assert response.status_code == 200

    def test_filter_by_priority_in_search(self, client, auth_headers):
        response = client.get("/api/search?priority=urgent", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(t["priority"] == "urgent" for t in data["tasks"])

    def test_pagination_in_search(self, client, auth_headers):
        response = client.get("/api/search?per_page=2&page=1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) <= 2

    def test_invalid_sort_field_returns_422(self, client, auth_headers):
        response = client.get("/api/search?sort_by=invalid_field", headers=auth_headers)
        assert response.status_code == 422

    def test_invalid_sort_dir_returns_422(self, client, auth_headers):
        response = client.get("/api/search?sort_dir=sideways", headers=auth_headers)
        assert response.status_code == 422