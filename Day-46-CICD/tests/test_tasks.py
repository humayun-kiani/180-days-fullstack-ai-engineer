# tests/test_tasks.py
import pytest
from app.models import TaskCreate, TaskUpdate, Priority, Status
from app import tasks as task_store


@pytest.fixture(autouse=True)
def clean_db():
    """Clear tasks before each test."""
    task_store.clear_all()
    yield
    task_store.clear_all()


class TestCreateTask:
    def test_creates_task_with_required_fields(self):
        data = TaskCreate(title="Fix the login bug")
        task = task_store.create_task(data)

        assert task.task_id.startswith("task-")
        assert task.title == "Fix the login bug"
        assert task.priority == Priority.MEDIUM
        assert task.status == Status.PENDING
        assert task.tags == []

    def test_creates_task_with_all_fields(self):
        data = TaskCreate(
            title="URGENT: Production down",
            description="All users affected",
            priority=Priority.URGENT,
            tags=["production", "incident"]
        )
        task = task_store.create_task(data)
        assert task.priority == Priority.URGENT
        assert "production" in task.tags

    def test_assigns_unique_ids(self):
        t1 = task_store.create_task(TaskCreate(title="Task 1"))
        t2 = task_store.create_task(TaskCreate(title="Task 2"))
        assert t1.task_id != t2.task_id

    def test_sets_timestamps(self):
        task = task_store.create_task(TaskCreate(title="Has timestamps"))
        assert task.created_at
        assert task.updated_at
        assert task.created_at == task.updated_at


class TestGetTask:
    def test_returns_existing_task(self):
        created = task_store.create_task(TaskCreate(title="Findable task"))
        found = task_store.get_task(created.task_id)
        assert found is not None
        assert found.task_id == created.task_id

    def test_returns_none_for_missing(self):
        result = task_store.get_task("task-doesnt-exist")
        assert result is None


class TestListTasks:
    def test_returns_all_tasks(self):
        task_store.create_task(TaskCreate(title="Task A"))
        task_store.create_task(TaskCreate(title="Task B"))
        task_store.create_task(TaskCreate(title="Task C"))
        assert len(task_store.list_tasks()) == 3

    def test_filters_by_status(self):
        t = task_store.create_task(TaskCreate(title="Filter me"))
        task_store.update_task(t.task_id, TaskUpdate(status=Status.DONE))
        task_store.create_task(TaskCreate(title="Still pending"))

        done = task_store.list_tasks(status="done")
        pending = task_store.list_tasks(status="pending")
        assert len(done) == 1
        assert len(pending) == 1

    def test_filters_by_priority(self):
        task_store.create_task(TaskCreate(title="Urgent!", priority=Priority.URGENT))
        task_store.create_task(TaskCreate(title="Meh", priority=Priority.LOW))

        urgent = task_store.list_tasks(priority="urgent")
        assert len(urgent) == 1
        assert urgent[0].priority == Priority.URGENT

    def test_empty_when_no_tasks(self):
        assert task_store.list_tasks() == []


class TestUpdateTask:
    def test_updates_title(self):
        task = task_store.create_task(TaskCreate(title="Original"))
        updated = task_store.update_task(task.task_id, TaskUpdate(title="Updated"))
        assert updated.title == "Updated"

    def test_updates_status(self):
        task = task_store.create_task(TaskCreate(title="Will be done"))
        updated = task_store.update_task(task.task_id, TaskUpdate(status=Status.DONE))
        assert updated.status == Status.DONE

    def test_updates_multiple_fields(self):
        task = task_store.create_task(TaskCreate(title="Multi"))
        updated = task_store.update_task(
            task.task_id,
            TaskUpdate(title="New title", priority=Priority.HIGH, status=Status.IN_PROGRESS)
        )
        assert updated.title == "New title"
        assert updated.priority == Priority.HIGH
        assert updated.status == Status.IN_PROGRESS

    def test_returns_none_for_missing(self):
        result = task_store.update_task("no-exist", TaskUpdate(title="X"))
        assert result is None

    def test_updates_timestamp(self):
        import time
        task = task_store.create_task(TaskCreate(title="Time test"))
        original_updated_at = task.updated_at
        time.sleep(0.01)
        updated = task_store.update_task(task.task_id, TaskUpdate(title="New"))
        assert updated.updated_at >= original_updated_at


class TestDeleteTask:
    def test_deletes_existing_task(self):
        task = task_store.create_task(TaskCreate(title="Delete me"))
        assert task_store.delete_task(task.task_id) is True
        assert task_store.get_task(task.task_id) is None

    def test_returns_false_for_missing(self):
        assert task_store.delete_task("no-exist") is False

    def test_reduces_count(self):
        task = task_store.create_task(TaskCreate(title="Count test"))
        assert task_store.task_count() == 1
        task_store.delete_task(task.task_id)
        assert task_store.task_count() == 0