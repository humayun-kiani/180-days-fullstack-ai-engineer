# Day 24 — Testing FastAPI: pytest, TestClient, Fixtures & Coverage

> **Phase 2 — Web Development** | Week 4 | Day 24 of 180

---

## 📌 What I Learned Today

- FastAPI TestClient — in-process HTTP testing without a real server
- TestClient makes synchronous requests to async FastAPI app
- Why test databases must be isolated from production
- SQLite in-memory for test database (fast, no files, auto-cleanup)
- app.dependency_overrides — replace production deps in tests
- conftest.py — pytest configuration shared across all test files
- scope="session" fixture — runs once for entire test session
- scope="function" fixture — runs before/after each test (default)
- autouse=True — fixture runs automatically without being requested
- clean_tables fixture — truncate data between every test
- User, token, and project fixtures for consistent test setup
- Testing 401 Unauthorized on every protected route
- Testing 403 Forbidden for role-based access
- Testing 404 for nonexistent resources
- Testing 409 Conflict for duplicate resources
- Testing 422 Unprocessable Entity for invalid input
- @pytest.mark.parametrize for testing many inputs efficiently
- Testing that passwords are never returned in responses
- Testing that soft-deleted items are excluded from lists
- TestClient.websocket_connect() for WebSocket testing
- ws.receive_json() and ws.send_json() in WebSocket tests
- PRAGMA foreign_keys=ON for SQLite FK constraint testing
- pytest --cov for measuring test coverage
- Coverage report shows which lines are not tested

## 🔨 Project Built

**Complete Test Suite** — 52+ tests for the Task Manager API:

**tests/conftest.py** — Test infrastructure:

- SQLite in-memory test database (no PostgreSQL needed for tests)
- dependency_overrides to replace get_db with test session
- autouse clean_tables fixture — wipes data between every test
- admin_user, editor_user, regular_user, inactive_user fixtures
- admin_token, user_token from real JWT generation
- admin_headers, user_headers shortcut fixtures
- sample_project, sample_task, tasks_variety data fixtures

**tests/test_auth.py** — 28 tests:

- Registration: success, duplicates, weak passwords, validation
- Login: success, wrong password, nonexistent user, deactivated
- Token flow: me endpoint, invalid tokens, refresh, logout
- Change password: success, wrong current, mismatch confirmation

**tests/test_tasks.py** — 30 tests:

- List: auth required, filtering, search, pagination, overdue filter
- Create: minimal, full, tags normalized, all validation cases
- Get: success, 404, deleted = 404, auth required
- Update: partial update, all statuses, 404
- Complete: basic, with hours, 409 if already done
- Delete: soft delete, not in list after, hard delete auth
- Bulk complete, overdue endpoint, upcoming endpoint

**tests/test_projects.py** — 12 tests
**tests/test_stats.py** — 5 tests

**Final Coverage: 91%**

## 🚀 How to Run

```bash
cd Day-24-Testing-FastAPI
source venv/bin/activate
pip install -r requirements.txt

# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing

# Specific file
pytest tests/test_auth.py -v

# HTML report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html
```

## 🧠 Key Testing Patterns

| Pattern                      | Purpose                          |
| ---------------------------- | -------------------------------- |
| `dependency_overrides`       | Replace DB with test SQLite      |
| `autouse=True fixture`       | Run automatically for every test |
| `scope="session"`            | Expensive setup once per run     |
| `parametrize`                | Test many inputs in one function |
| `client.post(json=...)`      | JSON request body                |
| `client.post(data=...)`      | Form data (OAuth2 login)         |
| `client.websocket_connect()` | WebSocket testing                |
| `--cov=app`                  | Measure coverage                 |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
