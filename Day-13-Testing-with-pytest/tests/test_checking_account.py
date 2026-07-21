# ============================================================
# tests/test_checking_account.py
# Tests for CheckingAccount
# ============================================================

import pytest
from bank import CheckingAccount, InsufficientFundsError, InvalidAmountError


class TestCheckingAccountInit:
    """Tests for CheckingAccount initialization."""

    def test_creates_successfully(self, checking_account):
        """Checking account should create with correct balance."""
        assert checking_account.balance == 10000

    def test_default_overdraft_limit(self, checking_account):
        """Default overdraft limit should be 25000."""
        assert checking_account.overdraft_limit == 25000

    def test_custom_overdraft_limit(self):
        """Custom overdraft limit should be stored."""
        account = CheckingAccount("Ali", 5000, overdraft_limit=50000)
        assert account.overdraft_limit == 50000

    def test_account_type_is_checking(self, checking_account):
        """Account type should be 'Checking'."""
        assert checking_account.account_type == "Checking"

    def test_available_balance_property(self, checking_account):
        """Available balance should include overdraft limit."""
        expected = checking_account.balance + checking_account.overdraft_limit
        assert checking_account.available_balance == expected


class TestCheckingWithdraw:
    """Tests for CheckingAccount overdraft withdrawals."""

    def test_withdrawal_within_balance(self, checking_account):
        """Normal withdrawal within balance should work."""
        checking_account.withdraw(5000)
        assert checking_account.balance == 5000

    def test_withdrawal_into_overdraft(self, checking_account):
        """Withdrawal into overdraft should be allowed."""
        checking_account.withdraw(20000)    # 10000 balance + 10000 overdraft
        assert checking_account.balance == -10000

    def test_withdrawal_to_overdraft_limit(self, checking_account):
        """Withdrawal to exact overdraft limit should work."""
        max_withdrawal = checking_account.available_balance
        checking_account.withdraw(max_withdrawal)
        assert checking_account.balance == -checking_account.overdraft_limit

    def test_withdrawal_exceeds_overdraft_raises_error(self, checking_account):
        """Withdrawal beyond overdraft limit should raise error."""
        with pytest.raises(InsufficientFundsError):
            checking_account.withdraw(100000)    # way more than available

    def test_zero_overdraft_limit(self, checking_no_overdraft):
        """Account with zero overdraft should block overdraft withdrawal."""
        with pytest.raises(InsufficientFundsError):
            checking_no_overdraft.withdraw(checking_no_overdraft.balance + 1)

    def test_available_balance_updates_after_withdrawal(self, checking_account):
        """Available balance should update after withdrawal."""
        before = checking_account.available_balance
        checking_account.withdraw(5000)
        assert checking_account.available_balance == before - 5000