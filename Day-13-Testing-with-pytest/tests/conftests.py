# ============================================================
# tests/conftest.py
# Shared fixtures for all test files
# ============================================================

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bank import (
    BankAccount,
    SavingsAccount,
    CheckingAccount,
    PremiumAccount,
    InsufficientFundsError,
    InvalidAmountError,
    AccountNotFoundError
)


# ─────────────────────────────────────────
# ACCOUNT FIXTURES
# ─────────────────────────────────────────

@pytest.fixture
def basic_account():
    """Standard bank account with Rs. 10,000 balance."""
    return BankAccount("Ali Hassan", 10000)


@pytest.fixture
def empty_account():
    """Standard bank account with zero balance."""
    return BankAccount("Omar Farooq", 0)


@pytest.fixture
def rich_account():
    """Standard bank account with large balance."""
    return BankAccount("Sara Ahmed", 500000)


@pytest.fixture
def savings_account():
    """Savings account with minimum required balance."""
    return SavingsAccount("Humayun Kiani", 10000, interest_rate=0.06)


@pytest.fixture
def high_rate_savings():
    """Savings account with high interest rate."""
    return SavingsAccount("Fatima Malik", 50000, interest_rate=0.12)


@pytest.fixture
def checking_account():
    """Checking account with default overdraft."""
    return CheckingAccount("Ahmed Khan", 10000)


@pytest.fixture
def checking_no_overdraft():
    """Checking account with zero overdraft limit."""
    return CheckingAccount("Test User", 5000, overdraft_limit=0)


@pytest.fixture
def premium_account():
    """Premium account with initial balance."""
    return PremiumAccount("Zara Shah", 10000)


@pytest.fixture
def two_accounts():
    """Two basic accounts for transfer testing."""
    sender = BankAccount("Sender User", 20000)
    receiver = BankAccount("Receiver User", 5000)
    return sender, receiver


@pytest.fixture
def account_with_history(basic_account):
    """Account with multiple transactions already recorded."""
    basic_account.deposit(5000, "Salary")
    basic_account.deposit(2000, "Bonus")
    basic_account.withdraw(1000, "Rent")
    basic_account.withdraw(500, "Groceries")
    return basic_account


# ─────────────────────────────────────────
# DATA FIXTURES
# ─────────────────────────────────────────

@pytest.fixture
def sample_owners():
    """List of sample owner names for parametrized tests."""
    return ["Ali Hassan", "Sara Ahmed", "Humayun Kiani", "Fatima Malik"]


@pytest.fixture
def valid_amounts():
    """List of valid amounts for parametrized tests."""
    return [0.01, 1, 100, 1000, 10000, 99999.99]


@pytest.fixture
def invalid_amounts():
    """List of invalid amounts that should raise errors."""
    return [0, -1, -100, -0.01]