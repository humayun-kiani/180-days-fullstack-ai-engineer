# backend/tests/conftest.py
# Shared fixtures for all tests

import pytest
import asyncio
from typing import AsyncGenerator

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker
)

# Use SQLite for testing (no PostgreSQL needed in CI)
TEST_DB_URL = "sqlite+aiosqlite:///./test_taskmind.db"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

TestAsyncSession = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def override_get_db():
    async with TestAsyncSession() as session:
        yield session


# ── Application setup ─────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    """Create all tables once per test session."""
    from app.db.database import Base
    # Import models to register them
    from app.models.user import User  # noqa
    from app.models.task import Task  # noqa

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
def app():
    """FastAPI application with test DB override."""
    from app.main import app as _app
    from app.db.database import get_db
    _app.dependency_overrides[get_db] = override_get_db
    return _app


@pytest.fixture(scope="session")
def client(app):
    """Synchronous test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client(app):
    """Async HTTP client for async tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.fixture
async def db_session():
    """Clean database session per test."""
    async with TestAsyncSession() as session:
        yield session
        await session.rollback()


# ── User fixtures ─────────────────────────────────────────────

@pytest.fixture
def user_data():
    return {
        "email": "humayun@test.com",
        "name": "Humayun",
        "password": "securepassword123"
    }


@pytest.fixture
def user_data_2():
    return {
        "email": "ali@test.com",
        "name": "Ali",
        "password": "securepassword456"
    }


@pytest.fixture
def registered_user(client, user_data):
    """Register a user and return their data + token."""
    import uuid
    # Use unique email per test to avoid conflicts
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    data = {**user_data, "email": unique_email}
    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def auth_headers(registered_user):
    """Return Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {registered_user['access_token']}"}


@pytest.fixture
def sample_task_data():
    return {
        "title": "Fix login authentication bug",
        "description": "Users with special characters in passwords cannot log in",
        "priority": "high"
    }


@pytest.fixture
def created_task(client, auth_headers, sample_task_data):
    """Create and return a task."""
    response = client.post("/api/tasks", json=sample_task_data, headers=auth_headers)
    assert response.status_code == 201
    return response.json()