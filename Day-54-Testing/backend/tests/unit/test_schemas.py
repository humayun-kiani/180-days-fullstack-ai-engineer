# backend/tests/unit/test_schemas.py
import pytest
from pydantic import ValidationError
from app.schemas.task import TaskCreate, TaskUpdate
from app.schemas.user import UserCreate


@pytest.mark.unit
class TestTaskCreate:
    def test_valid_task_creation(self):
        task = TaskCreate(title="Fix login bug", priority="high")
        assert task.title == "Fix login bug"
        assert task.priority == "high"

    def test_default_priority_is_medium(self):
        task = TaskCreate(title="Some task")
        assert task.priority == "medium"

    def test_empty_title_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title="")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_title_too_long_raises(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="x" * 501)

    def test_title_at_max_length_ok(self):
        task = TaskCreate(title="x" * 500)
        assert len(task.title) == 500

    @pytest.mark.parametrize("priority", ["urgent", "high", "medium", "low"])
    def test_valid_priorities(self, priority):
        task = TaskCreate(title="Test", priority=priority)
        assert task.priority == priority

    def test_invalid_priority_raises(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="Test", priority="critical")

    def test_optional_description_defaults_none(self):
        task = TaskCreate(title="Test")
        assert task.description is None

    def test_description_accepted(self):
        task = TaskCreate(title="Test", description="Detailed description here")
        assert task.description == "Detailed description here"


@pytest.mark.unit
class TestTaskUpdate:
    def test_all_optional(self):
        update = TaskUpdate()
        assert update.title is None
        assert update.status is None
        assert update.priority is None

    @pytest.mark.parametrize("status", ["pending", "in_progress", "done"])
    def test_valid_statuses(self, status):
        update = TaskUpdate(status=status)
        assert update.status == status

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            TaskUpdate(status="cancelled")

    def test_partial_update_allowed(self):
        update = TaskUpdate(priority="low")
        assert update.priority == "low"
        assert update.status is None
        assert update.title is None


@pytest.mark.unit
class TestUserCreate:
    def test_valid_user(self):
        user = UserCreate(email="test@example.com", name="Test", password="password123")
        assert user.email == "test@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(email="not-an-email", name="Test", password="password123")

    def test_short_password_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com", name="Test", password="short")

    def test_password_exactly_8_chars_ok(self):
        user = UserCreate(email="test@example.com", name="Test", password="12345678")
        assert len(user.password) == 8