# Day 13 — Testing with pytest: Unit Tests, Fixtures, Mocking & Coverage

> **Phase 1 — Foundations** | Week 2 | Day 13 of 180

---

## 📌 What I Learned Today

- Why testing matters — real cost of bugs in production
- Types of tests: unit, integration, end-to-end
- pytest — why it is better than unittest
- Test naming conventions and auto-discovery
- Writing assertions with plain assert statements
- pytest.raises — testing that exceptions are raised correctly
- pytest.approx — handling floating point comparisons
- Fixtures — @pytest.fixture for reusable test setup
- Fixture scope: function, class, module, session
- Fixtures with yield — setup AND teardown in one function
- conftest.py — shared fixtures across all test files
- Built-in fixtures: tmp_path, capsys, monkeypatch
- @pytest.mark.parametrize — data-driven testing
- Mocking with unittest.mock: Mock, patch, MagicMock
- patch as decorator and context manager
- pytest-mock: mocker fixture for cleaner mocking
- pytest-cov: measuring test coverage with --cov
- Arrange-Act-Assert (AAA) pattern
- Grouping tests in classes for organization
- pytest.ini configuration file

## 🔨 Project Built

**Complete Test Suite for Bank Account System:**

- 65+ test cases across 6 test files
- TestBankAccountInit — 13 tests for initialization
- TestDeposit — 12 tests including parametrize for all amounts
- TestWithdraw — 10 tests including edge cases
- TestTransfer — 6 tests including insufficient funds
- TestProperties — 9 tests for dunder methods
- TestSavingsAccount — 20 tests for savings-specific behavior
- TestCheckingAccount — 12 tests for overdraft behavior
- TestPremiumAccount — 14 tests for points and cashback
- Integration tests — 7 complex workflow scenarios
- 92%+ test coverage achieved
- pytest.ini for clean configuration

## 🚀 How to Run

```bash
cd Day-13-Testing-with-pytest
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run with HTML coverage report
pytest --cov=. --cov-report=html
# Then open htmlcov/index.html in browser
```

## 🧠 Key Concepts

| Concept          | Syntax                                   |
| ---------------- | ---------------------------------------- |
| Assert equality  | `assert result == expected`              |
| Assert exception | `with pytest.raises(Error):`             |
| Float comparison | `assert x == pytest.approx(3.14)`        |
| Fixture          | `@pytest.fixture`                        |
| Parametrize      | `@pytest.mark.parametrize("x,y", [...])` |
| Mock function    | `@patch("module.function")`              |
| Mock return      | `mock.return_value = data`               |
| Mock error       | `mock.side_effect = Exception()`         |
| Run coverage     | `pytest --cov=src`                       |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
