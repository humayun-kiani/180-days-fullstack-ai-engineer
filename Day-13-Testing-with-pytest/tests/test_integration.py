# ============================================================
# tests/test_integration.py
# Integration tests — multiple components working together
# ============================================================

import pytest
from bank import (
    BankAccount, SavingsAccount, CheckingAccount, PremiumAccount,
    InsufficientFundsError, InvalidAmountError
)


@pytest.mark.integration
class TestTransferBetweenAccountTypes:
    """Integration tests for transfers between different account types."""

    def test_transfer_basic_to_savings(self):
        """Transfer from standard to savings account should work."""
        sender = BankAccount("Sender", 20000)
        receiver = SavingsAccount("Receiver", 5000)

        sender.transfer(receiver, 5000)

        assert sender.balance == 15000
        assert receiver.balance == 10000

    def test_transfer_checking_overdraft_to_savings(self):
        """Transfer using overdraft should work."""
        sender = CheckingAccount("Sender", 5000, overdraft_limit=10000)
        receiver = BankAccount("Receiver", 0)

        sender.transfer(receiver, 10000)

        assert sender.balance == -5000
        assert receiver.balance == 10000

    def test_chain_of_transfers(self):
        """Money transferred through a chain of accounts should balance."""
        initial_total = 30000

        acc1 = BankAccount("Account 1", 30000)
        acc2 = BankAccount("Account 2", 0)
        acc3 = BankAccount("Account 3", 0)

        acc1.transfer(acc2, 15000)
        acc2.transfer(acc3, 10000)

        total_after = acc1.balance + acc2.balance + acc3.balance
        assert total_after == initial_total    # money is conserved

    def test_premium_deposit_then_redeem_then_transfer(self):
        """Complex multi-operation scenario."""
        premium = PremiumAccount("Premium User", 20000)
        regular = BankAccount("Regular User", 5000)

        # Deposit to earn points
        premium.deposit(10000)    # earns 100 points, balance = 30000
        assert premium.rewards_points == 100

        # Redeem points
        premium.redeem_points(100)    # get Rs. 10 back
        assert premium.rewards_points == 0

        # Transfer to regular account
        premium.transfer(regular, 10000)
        assert regular.balance == 15000

    def test_savings_interest_then_transfer(self):
        """Adding interest then transferring should work correctly."""
        savings = SavingsAccount("Saver", 50000, interest_rate=0.12)
        checking = CheckingAccount("Spender", 0)

        interest = savings.add_interest()
        assert interest > 0

        balance_after_interest = savings.balance
        savings.transfer(checking, 5000)

        assert savings.balance == balance_after_interest - 5000
        assert checking.balance == 5000


@pytest.mark.integration
class TestComplexWorkflows:
    """Tests for realistic workflows."""

    def test_monthly_salary_workflow(self):
        """Simulate receiving salary and distributing to different accounts."""
        salary_account = CheckingAccount("Salary", 0)
        savings = SavingsAccount("Savings", 5000)
        expense_account = BankAccount("Expenses", 0)

        # Receive salary
        salary_account.deposit(100000, "Monthly Salary")

        # Transfer to savings (40%)
        salary_account.transfer(savings, 40000)

        # Transfer to expense account (30%)
        salary_account.transfer(expense_account, 30000)

        # Keep remainder in salary account
        assert salary_account.balance == 30000
        assert savings.balance == 45000
        assert expense_account.balance == 30000

    def test_savings_goal_workflow(self):
        """Simulate saving toward a goal over multiple months."""
        savings = SavingsAccount("Saver", 10000)
        monthly_deposit = 5000
        months = 6

        initial_balance = savings.balance
        total_deposited = 0
        total_interest = 0

        for _ in range(months):
            savings.deposit(monthly_deposit, "Monthly Saving")
            total_deposited += monthly_deposit
            interest = savings.add_interest()
            total_interest += interest

        assert savings.balance > initial_balance + total_deposited
        assert total_interest > 0
        # Balance should be initial + all deposits + all interest
        expected = initial_balance + total_deposited + total_interest
        assert savings.balance == pytest.approx(expected, rel=1e-6)