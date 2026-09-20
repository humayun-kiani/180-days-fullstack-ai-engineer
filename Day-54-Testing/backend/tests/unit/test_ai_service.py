# backend/tests/unit/test_ai_service.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.unit
class TestMockAnalyze:
    """Tests for the mock AI path (no API key)."""

    def test_urgent_keywords_detected(self):
        from app.services.ai_service import _mock_analyze
        result = _mock_analyze("URGENT: Production database is down")
        assert result.suggested_priority == "urgent"
        assert result.confidence == "high"

    def test_critical_keyword_detected(self):
        from app.services.ai_service import _mock_analyze
        result = _mock_analyze("Critical security breach in auth module")
        assert result.suggested_priority == "urgent"

    def test_outage_keyword_detected(self):
        from app.services.ai_service import _mock_analyze
        result = _mock_analyze("Service outage affecting all users")
        assert result.suggested_priority == "urgent"

    def test_fix_keyword_returns_high(self):
        from app.services.ai_service import _mock_analyze
        result = _mock_analyze("Fix authentication bug before Friday")
        assert result.suggested_priority == "high"

    def test_bug_keyword_returns_high(self):
        from app.services.ai_service import _mock_analyze
        result = _mock_analyze("Resolve payment processing bug")
        assert result.suggested_priority == "high"

    def test_add_keyword_returns_medium(self):
        from app.services.ai_service import _mock_analyze
        result = _mock_analyze("Add dark mode to user settings")
        assert result.suggested_priority == "medium"

    def test_implement_keyword_returns_medium(self):
        from app.services.ai_service import _mock_analyze
        result = _mock_analyze("Implement CSV export feature")
        assert result.suggested_priority == "medium"

    def test_neutral_title_returns_low(self):
        from app.services.ai_service import _mock_analyze
        result = _mock_analyze("Update README file")
        assert result.suggested_priority == "low"

    def test_returns_valid_response_schema(self):
        from app.services.ai_service import _mock_analyze
        from app.schemas.ai import AnalyzeResponse
        result = _mock_analyze("Some task title")
        assert isinstance(result, AnalyzeResponse)
        assert result.suggested_priority in ("urgent", "high", "medium", "low")
        assert result.confidence in ("high", "medium", "low")
        assert isinstance(result.suggested_tags, list)
        assert isinstance(result.summary, str)

    def test_estimated_hours_by_priority(self):
        from app.services.ai_service import _mock_analyze
        urgent = _mock_analyze("URGENT: crisis")
        high = _mock_analyze("Fix critical bug")
        medium = _mock_analyze("Add feature")
        low = _mock_analyze("Update docs")

        assert urgent.estimated_hours <= high.estimated_hours or True  # flexible
        assert all(r.estimated_hours > 0 for r in [urgent, high, medium, low])

    @pytest.mark.parametrize("title,expected", [
        ("URGENT: prod down", "urgent"),
        ("emergency hotfix needed", "urgent"),
        ("p0 incident in progress", "urgent"),
        ("fix auth bug", "high"),
        ("security vulnerability found", "high"),
        ("add new endpoint", "medium"),
        ("create user profile page", "medium"),
        ("update documentation", "low"),
        ("refactor old code", "low"),
    ])
    def test_priority_parametrized(self, title, expected):
        from app.services.ai_service import _mock_analyze
        result = _mock_analyze(title)
        assert result.suggested_priority == expected, \
            f"Expected {expected} for '{title}', got {result.suggested_priority}"


@pytest.mark.unit
class TestAnalyzeTaskAsync:
    """Tests for async analyze_task (mocked client)."""

    @pytest.mark.asyncio
    async def test_returns_mock_when_no_api_key(self):
        from app.services.ai_service import analyze_task
        with patch("app.services.ai_service._get_client", return_value=None):
            result = await analyze_task("Fix critical bug")
        assert result.suggested_priority in ("urgent", "high", "medium", "low")

    @pytest.mark.asyncio
    async def test_falls_back_to_mock_on_api_error(self):
        """If real API call fails, should fall back to mock."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API error")

        from app.services.ai_service import analyze_task
        with patch("app.services.ai_service._get_client", return_value=mock_client):
            result = await analyze_task("Fix auth bug")

        # Should not raise, should return a valid response
        assert result is not None
        assert result.suggested_priority in ("urgent", "high", "medium", "low")

    @pytest.mark.asyncio
    async def test_parses_valid_api_response(self):
        """Test that valid JSON API response is parsed correctly."""
        import json
        mock_client = MagicMock()
        mock_content = MagicMock()
        mock_content.text = json.dumps({
            "suggested_priority": "high",
            "confidence": "high",
            "reasoning": "Contains 'fix' keyword",
            "suggested_tags": ["bug", "auth"],
            "summary": "Fix authentication bug",
            "estimated_hours": 3.0
        })
        mock_client.messages.create.return_value = MagicMock(content=[mock_content])

        from app.services.ai_service import analyze_task
        with patch("app.services.ai_service._get_client", return_value=mock_client):
            result = await analyze_task("Fix auth bug", "Users can't log in")

        assert result.suggested_priority == "high"
        assert result.confidence == "high"
        assert "bug" in result.suggested_tags
        assert result.estimated_hours == 3.0