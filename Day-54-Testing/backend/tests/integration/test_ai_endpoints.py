# backend/tests/integration/test_ai_endpoints.py
import pytest
from unittest.mock import patch, AsyncMock
from app.schemas.ai import AnalyzeResponse, ExpandResponse, BreakdownResponse, SubTask


@pytest.fixture
def mock_analyze():
    """Mock the AI analyze_task function."""
    mock_response = AnalyzeResponse(
        suggested_priority="high",
        confidence="high",
        reasoning="Contains 'fix' keyword",
        suggested_tags=["bug", "auth"],
        summary="Fix authentication issue",
        estimated_hours=3.0
    )
    with patch("app.api.ai.ai_service.analyze_task", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response
        yield mock


@pytest.fixture
def mock_expand():
    mock_response = ExpandResponse(
        description="Implement dark mode across all UI components",
        suggested_priority="medium",
        suggested_tags=["ui", "design"]
    )
    with patch("app.api.ai.ai_service.expand_task", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response
        yield mock


@pytest.mark.integration
class TestAIEndpoints:
    def test_analyze_endpoint_success(self, client, auth_headers, mock_analyze):
        response = client.post("/api/ai/analyze", json={
            "title": "Fix auth bug",
            "description": "Users can't log in"
        }, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["suggested_priority"] == "high"
        assert data["confidence"] == "high"
        assert "reasoning" in data
        assert "suggested_tags" in data
        assert "estimated_hours" in data

    def test_analyze_requires_title(self, client, auth_headers):
        response = client.post("/api/ai/analyze", json={
            "description": "No title provided"
        }, headers=auth_headers)
        assert response.status_code == 422

    def test_analyze_title_only_ok(self, client, auth_headers, mock_analyze):
        response = client.post("/api/ai/analyze", json={
            "title": "Fix something"
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_expand_endpoint_success(self, client, auth_headers, mock_expand):
        response = client.post("/api/ai/expand", json={
            "title": "Add dark mode"
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "description" in data
        assert len(data["description"]) > 0
        assert "suggested_priority" in data
        assert "suggested_tags" in data

    def test_ai_endpoints_require_auth(self, client):
        response = client.post("/api/ai/analyze", json={"title": "Test"})
        assert response.status_code in (401, 403)

    def test_breakdown_endpoint_returns_subtasks(self, client, auth_headers):
        """Test breakdown with mock (uses internal mock when no API key)."""
        with patch("app.api.ai.ai_service.breakdown_task", new_callable=AsyncMock) as mock:
            mock.return_value = BreakdownResponse(
                subtasks=[
                    SubTask(title="Research", estimated_hours=1.0, priority="medium"),
                    SubTask(title="Implement", estimated_hours=4.0, priority="high"),
                    SubTask(title="Test", estimated_hours=2.0, priority="medium"),
                ],
                total_estimated_hours=7.0
            )
            response = client.post("/api/ai/breakdown", json={
                "title": "Build checkout page"
            }, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "subtasks" in data
        assert len(data["subtasks"]) == 3
        assert data["total_estimated_hours"] == 7.0

    def test_weekly_summary_endpoint(self, client, auth_headers):
        """Weekly summary should work even with 0 tasks."""
        with patch("app.api.ai.ai_service.weekly_summary", new_callable=AsyncMock) as mock:
            from app.schemas.ai import WeeklySummaryResponse
            mock.return_value = WeeklySummaryResponse(
                summary="No tasks this week",
                stats={"total_tasks": 0},
                highlights=[],
                recommendations=["Create your first task"]
            )
            response = client.get("/api/ai/weekly-summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "stats" in data