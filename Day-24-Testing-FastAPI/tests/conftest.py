# ============================================================
# tests/conftest.py
# Global test configuration and fixtures
# ============================================================

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event as sa_event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import hash_password, create_access_token
from app.db.models.user import User
from app.db.models.project import Project
from app.db.models.task import Task


# ─── Test Database (SQLite in-memory) ───────────────────────

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False    # set True to debug SQL
)

# Enable foreign key support in SQLite
@sa_event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


def override_get_db():
    """Override production DB with test SQLite DB."""
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Apply the override globally
app.dependency_overrides[get_db] = override_get_db


# ─── Schema Management ───────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create schema once for the entire test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    """
    Truncate all tables before each test.
    This ensures complete isolation between tests.
    """
    # Let test run
    yield

    # Clean up after test
    db = TestingSessionLocal()
    try:
        # Delete in reverse dependency order
        db.query(Task).delete()
        db.query(Project).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


# ─── Core Fixtures ───────────────────────────────────────────

@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture
def db():
    """Direct database session for test setup/teardown."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ─── User Fixtures ───────────────────────────────────────────

@pytest.fixture
def admin_user(db) -> User:
    """Admin user in test database."""
    user = User(
        username="admin",
        email="admin@test.com",
        hashed_password=hash_password("AdminPass123"),
        full_name="Test Admin",
        role="admin",
        is_active=True,
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def editor_user(db) -> User:
    """Editor user in test database."""
    user = User(
        username="editor",
        email="editor@test.com",
        hashed_password=hash_password("EditorPass123"),
        full_name="Test Editor",
        role="editor",
        is_active=True,
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def regular_user(db) -> User:
    """Regular user in test database."""
    user = User(
        username="testuser",
        email="user@test.com",
        hashed_password=hash_password("UserPass123"),
        full_name="Test User",
        role="user",
        is_active=True,
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def inactive_user(db) -> User:
    """Inactive (deactivated) user."""
    user = User(
        username="inactive",
        email="inactive@test.com",
        hashed_password=hash_password("InactivePass123"),
        full_name="Inactive User",
        role="user",
        is_active=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ─── Token Fixtures ──────────────────────────────────────────

@pytest.fixture
def admin_token(admin_user) -> str:
    return create_access_token(
        subject=admin_user.id,
        extra_data={
            "username": admin_user.username,
            "role": admin_user.role,
            "email": admin_user.email
        }
    )


@pytest.fixture
def editor_token(editor_user) -> str:
    return create_access_token(
        subject=editor_user.id,
        extra_data={
            "username": editor_user.username,
            "role": editor_user.role,
            "email": editor_user.email
        }
    )


@pytest.fixture
def user_token(regular_user) -> str:
    return create_access_token(
        subject=regular_user.id,
        extra_data={
            "username": regular_user.username,
            "role": regular_user.role,
            "email": regular_user.email
        }
    )


@pytest.fixture
def admin_headers(admin_token) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def editor_headers(editor_token) -> dict:
    return {"Authorization": f"Bearer {editor_token}"}


@pytest.fixture
def user_headers(user_token) -> dict:
    return {"Authorization": f"Bearer {user_token}"}


# ─── Project Fixtures ────────────────────────────────────────

@pytest.fixture
def sample_project(db, admin_user) -> Project:
    project = Project(
        name="Test Project Alpha",
        description="First test project",
        status="active",
        color="#3B82F6",
        is_active=True
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def second_project(db, admin_user) -> Project:
    project = Project(
        name="Test Project Beta",
        description="Second test project",
        status="active",
        color="#10B981",
        is_active=True
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


# ─── Task Fixtures ───────────────────────────────────────────

@pytest.fixture
def sample_task(db, admin_user, sample_project) -> Task:
    task = Task(
        title="Sample Test Task",
        description="A task created for testing",
        status="pending",
        priority="medium",
        project_id=sample_project.id,
        owner_id=admin_user.id,
        tags=["test", "sample"],
        estimated_hours=2.0,
        is_deleted=False
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@pytest.fixture
def done_task(db, admin_user, sample_project) -> Task:
    """A task that is already completed."""
    task = Task(
        title="Completed Task",
        status="done",
        priority="low",
        project_id=sample_project.id,
        owner_id=admin_user.id,
        tags=[],
        is_deleted=False
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@pytest.fixture
def tasks_variety(db, admin_user, sample_project) -> list[Task]:
    """Multiple tasks with different statuses and priorities."""
    task_defs = [
        ("Pending High Task", "pending", "high"),
        ("Pending Low Task", "pending", "low"),
        ("In Progress Task", "in_progress", "medium"),
        ("Done Task One", "done", "medium"),
        ("Done Task Two", "done", "low"),
        ("Urgent Pending", "pending", "urgent"),
        ("Archived Task", "archived", "medium"),
    ]
    tasks = []
    for title, status, priority in task_defs:
        t = Task(
            title=title,
            status=status,
            priority=priority,
            project_id=sample_project.id,
            owner_id=admin_user.id,
            tags=[priority, status],
            is_deleted=False
        )
        db.add(t)
        tasks.append(t)
    db.commit()
    for t in tasks:
        db.refresh(t)
    return tasks