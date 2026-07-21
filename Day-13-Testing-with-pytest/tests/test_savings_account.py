# ============================================================
# tests/test_savings_account.py
# Tests for SavingsAccount
# ============================================================

import pytest
from bank import SavingsAccount, InvalidAmountError, InsufficientFundsError


class TestSavingsAccountInit:
    """Tests for SavingsAccount initialization."""

    def test_creates_with_valid_balance(self, savings_account):
        """Savings account should create with valid balance."""
        assert savings_account.balance == 10000

    def test_minimum_balance_required(self):
        """Balance below minimum should raise InvalidAmountError."""
        with pytest.raises(InvalidAmountError, match="minimum balance"):
            SavingsAccount("Ali", 1000)    # below 5000 minimum

    def test_exact_minimum_balance_allowed(self):
        """Exact minimum balance should be allowed."""
        account = SavingsAccount("Ali", 5000)
        assert account.balance == 5000

    def test_default_interest_rate(self, savings_account):
        """Default interest rate should be 6%."""
        assert savings_account.interest_rate == 0.06

    def test_custom_interest_rate(self, high_rate_savings):
        """Custom interest rate should be stored correctly."""
        assert high_rate_savings.interest_rate == 0.12

    def test_starts_with_zero_withdrawals(self, savings_account):
        """Monthly withdrawal counter should start at zero."""
        assert savings_account.monthly_withdrawals == 0

    def test_account_type_is_savings(self, savings_account):
        """Account type should be 'Savings'."""
        assert savings_account.account_type == "Savings"


class TestSavingsWithdraw:
    """Tests for SavingsAccount withdrawal restrictions."""

    def test_basic_withdrawal_works(self, savings_account):
        """Normal withdrawal should work."""
        savings_account.withdraw(2000)
        assert savings_account.balance == 8000

    def test_withdrawal_below_minimum_balance_blocked(self, savings_account):
        """Withdrawal that would breach minimum balance should be blocked."""
        with pytest.raises(InsufficientFundsError, match="minimum balance"):
            savings_account.withdraw(6000)    # would leave 4000 < 5000 min

    def test_monthly_limit_enforced(self, savings_account):
        """Should block withdrawal after monthly limit reached."""
        for _ in range(SavingsAccount.MAX_WITHDRAWALS):
            savings_account.withdraw(1000)

        with pytest.raises(InsufficientFundsError, match="Monthly withdrawal limit"):
            savings_account.withdraw(1000)

    def test_withdrawal_counter_increments(self, savings_account):
        """Monthly withdrawal counter should increment."""
        savings_account.withdraw(1000)
        assert savings_account.monthly_withdrawals == 1

    def test_withdrawals_remaining_property(self, savings_account):
        """withdrawals_remaining should reflect remaining allowed."""
        savings_account.withdraw(1000)
        assert savings_account.withdrawals_remaining == SavingsAccount.MAX_WITHDRAWALS - 1

    def test_withdrawal_to_exact_minimum(self, savings_account):
        """Withdrawal leaving exactly minimum balance should be allowed."""
        withdraw_amount = savings_account.balance - SavingsAccount.MIN_BALANCE
        savings_account.withdraw(withdraw_amount)
        assert savings_account.balance == SavingsAccount.MIN_BALANCE


class TestSavingsInterest:
    """Tests for interest calculation."""

    def test_add_interest_increases_balance(self, savings_account):
        """Adding interest should increase balance."""
        before = savings_account.balance
        savings_account.add_interest()
        assert savings_account.balance > before

    def test_interest_amount_correct(self, savings_account):
        """Interest should be calculated as (rate/12) * balance."""
        expected_interest = savings_account.balance * (savings_account.interest_rate / 12)
        interest = savings_account.add_interest()
        assert interest == pytest.approx(expected_interest)

    def test_add_interest_creates_transaction(self, savings_account):
        """Adding interest should create a transaction record."""
        before = len(savings_account.transactions)
        savings_account.add_interest()
        assert len(savings_account.transactions) == before + 1

    def test_add_interest_resets_monthly_withdrawals(self, savings_account):
        """Adding interest should reset the monthly withdrawal counter."""
        savings_account.withdraw(1000)
        assert savings_account.monthly_withdrawals == 1
        savings_account.add_interest()
        assert savings_account.monthly_withdrawals == 0

    @pytest.mark.parametrize("rate, balance, expected_monthly", [
        (0.06, 10000, 50.0),    # 6% annual / 12 months
        (0.12, 10000, 100.0),   # 12% annual / 12 months
        (0.06, 20000, 100.0),   # double balance = double interest
    ])
    def test_interest_calculation_various_rates(self, rate, balance, expected_monthly):
        """Interest calculation should be correct for various rates."""
        account = SavingsAccount("Test", balance, interest_rate=rate)
        interest = account.add_interest()
        assert interest == pytest.approx(expected_monthly, rel=1e-3)