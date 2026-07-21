# ============================================================
# tests/test_premium_account.py
# Tests for PremiumAccount
# ============================================================

import pytest
from bank import PremiumAccount, InvalidAmountError


class TestPremiumDeposit:
    """Tests for PremiumAccount deposit with rewards."""

    def test_deposit_earns_points(self, premium_account):
        """Deposit of Rs. 1000+ should earn reward points."""
        premium_account.deposit(5000)
        assert premium_account.rewards_points > 0

    def test_points_calculation(self, premium_account):
        """Points earned should be 10 per Rs. 1000 deposited."""
        premium_account.deposit(5000)
        expected_points = 5 * PremiumAccount.POINTS_PER_1000
        assert premium_account.rewards_points == expected_points

    def test_small_deposit_no_points(self, premium_account):
        """Deposit under Rs. 1000 should earn no points."""
        premium_account.deposit(500)
        assert premium_account.rewards_points == 0

    def test_multiple_deposits_accumulate_points(self, premium_account):
        """Multiple deposits should accumulate points."""
        premium_account.deposit(2000)
        premium_account.deposit(3000)
        assert premium_account.rewards_points == 50    # 20 + 30

    def test_deposit_updates_balance(self, premium_account):
        """Deposit should still update balance normally."""
        premium_account.deposit(5000)
        assert premium_account.balance == 15000


class TestPremiumWithdraw:
    """Tests for PremiumAccount cashback feature."""

    def test_withdrawal_earns_cashback(self, premium_account):
        """Withdrawal should trigger cashback credit."""
        before = premium_account.total_cashback
        premium_account.withdraw(2000)
        assert premium_account.total_cashback > before

    def test_cashback_amount_correct(self, premium_account):
        """Cashback should be 2% of withdrawn amount."""
        premium_account.withdraw(5000)
        expected_cashback = 5000 * PremiumAccount.CASHBACK_RATE
        assert premium_account.total_cashback == pytest.approx(expected_cashback)

    def test_cashback_credited_to_balance(self, premium_account):
        """Cashback should be added back to balance."""
        initial = premium_account.balance
        withdraw_amount = 5000
        premium_account.withdraw(withdraw_amount)
        cashback = withdraw_amount * PremiumAccount.CASHBACK_RATE
        expected = initial - withdraw_amount + cashback
        assert premium_account.balance == pytest.approx(expected)


class TestPremiumRedemption:
    """Tests for reward point redemption."""

    def test_redeem_points_for_cash(self, premium_account):
        """Redeeming points should add cash to balance."""
        premium_account.deposit(10000)    # earn 100 points
        before_balance = premium_account.balance
        premium_account.redeem_points(100)
        assert premium_account.balance > before_balance

    def test_redeem_reduces_points(self, premium_account):
        """Redemption should deduct points from total."""
        premium_account.deposit(10000)    # earn 100 points
        premium_account.redeem_points(50)
        assert premium_account.rewards_points == 50

    def test_redeem_more_than_available_raises_error(self, premium_account):
        """Redeeming more points than available should raise error."""
        with pytest.raises(ValueError, match="Insufficient points"):
            premium_account.redeem_points(1000)    # more than zero initial points

    def test_cash_value_per_point(self, premium_account):
        """100 points should be worth Rs. 10."""
        premium_account.deposit(10000)    # earn 100 points
        initial_balance = premium_account.balance
        premium_account.redeem_points(100)
        assert premium_account.balance == pytest.approx(initial_balance + 10.0)