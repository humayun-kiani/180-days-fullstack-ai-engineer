# Day 54 — Testing & Quality Assurance

> **Phase 7 — Full Stack Integration** | Day 54 of 180

---

## 📌 What I Learned Today

- Testing pyramid: many unit (fast) → some integration → few E2E (slow)
- pytest fixtures: @pytest.fixture provides reusable setup/teardown
- fixture scope: function (default), class, module, session
- conftest.py: shared fixtures auto-discovered by pytest
- pytest.mark.asyncio: enables async test functions
- asyncio_mode = auto in pytest.ini: no need to mark each test
- SQLite + aiosqlite: in-memory test database for integration tests
- app.dependency_overrides: replace FastAPI dependencies in tests
- TestClient: synchronous HTTPX client over async FastAPI app
- AsyncClient + ASGITransport: async version for async tests
- @pytest.mark.parametrize: run same test with multiple inputs
- pytest -m unit: run only tests marked with @pytest.mark.unit
- --cov-fail-under=80: fail CI if coverage drops below 80%
- from unittest.mock import patch: replace functions during a test
- AsyncMock: mock for async functions (return_value works correctly)
- MagicMock: synchronous mock with attribute access
- mock.assert_called_once(): verify mock was called exactly once
- render() + screen queries: RTL philosophy — test what users see
- getByRole: preferred query — matches ARIA semantics
- getByLabelText: for form inputs with labels
- userEvent: simulates real user interaction (focus, type, click)
- waitFor: wait for async state changes after actions
- vi.mock: replace entire module with mock in Vitest
- vi.fn().mockResolvedValue: async mock returning a value
- beforeEach/vi.clearAllMocks: reset mocks between tests
- renderHook + act: test custom hooks in isolation
- Playwright: automates real browser (Chromium, Firefox, WebKit)
- page.fill/click/keyboard.press: user action API
- expect(page.locator(...)).toBeVisible(): wait + assert combined
- await expect(page).toHaveURL(/pattern/): URL assertion with regex
- webServer config: automatically start dev server before tests
- Coverage: lines, functions, branches — target 80%+ for CI gate

## 🔨 Project Built

**Complete Test Suite for TaskMind — 116+ tests:**

**Backend (pytest) — 94 tests:**
- Unit (55 tests): security, AI service mock, Pydantic schemas
- Integration (39 tests): auth, CRUD, search, AI endpoints, stats
- Test database: SQLite + aiosqlite (no PostgreSQL needed)
- Mocking: Claude API, Redis, internal services
- Coverage: 82% line coverage with HTML report

**Frontend (Vitest + RTL) — 42 tests:**
- Unit: pure function analysis (15 tests)
- Components: TaskCard rendering + UX (12 tests), TaskForm (8 tests)
- Hooks: useSwipe touch gesture logic (7 tests)

**E2E (Playwright) — 15 tests across 2 browsers:**
- auth.spec: register → login → redirect flows
- tasks.spec: board layout, create task, keyboard shortcuts
- ai.spec: AI expand, AI prioritize, weekly summary

## 🚀 How to Run

```bash
# Backend tests
cd backend
pip install -r requirements-test.txt
pytest              # all tests + coverage
pytest -m unit      # unit only
pytest -m integration  # integration only

# Frontend tests
cd frontend
npm run test -- --run --coverage

# E2E (ensure backend + frontend running first)
cd e2e
npx playwright install chromium
npx playwright test
npx playwright show-report
```

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)