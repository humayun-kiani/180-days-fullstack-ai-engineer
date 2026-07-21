# ============================================================
# tests/test_bank_account.py
# Tests for the BankAccount base class
# ============================================================

import pytest
from unittest.mock import patch, MagicMock
from bank import BankAccount, InvalidAmountError, InsufficientFundsError


# ─────────────────────────────────────────
# INITIALIZATION TESTS
# ─────────────────────────────────────────

class TestBankAccountInit:
    """Tests for BankAccount initialization."""

    def test_creates_with_owner_and_balance(self, basic_account):
        """Account should store owner name and balance."""
        assert basic_account.owner == "Ali Hassan"
        assert basic_account.balance == 10000

    def test_title_cases_owner_name(self):
        """Owner name should be title-cased."""
        account = BankAccount("ALI HASSAN", 1000)
        assert account.owner == "Ali Hassan"

    def test_strips_whitespace_from_name(self):
        """Leading and trailing spaces should be stripped."""
        account = BankAccount("  Ali Hassan  ", 1000)
        assert account.owner == "Ali Hassan"

    def test_default_balance_is_zero(self):
        """Account created without balance should have zero balance."""
        account = BankAccount("Ali Hassan")
        assert account.balance == 0

    def test_account_type_defaults_to_standard(self, basic_account):
        """Default account type should be Standard."""
        assert basic_account.account_type == "Standard"

    def test_generates_unique_account_id(self):
        """Each account should have a unique account ID."""
        acc1 = BankAccount("User One", 1000)
        acc2 = BankAccount("User Two", 1000)
        assert acc1.account_id != acc2.account_id

    def test_account_id_format(self, basic_account):
        """Account ID should follow PNB-XXXX format."""
        assert basic_account.account_id.startswith("PNB-")
        assert len(basic_account.account_id) == 8

    def test_starts_with_empty_transactions(self, empty_account):
        """New account with zero balance should have no transactions."""
        assert len(empty_account.transactions) == 0

    def test_opening_deposit_creates_transaction(self, basic_account):
        """Non-zero initial balance should create an opening transaction."""
        assert len(basic_account.transactions) == 1
        assert basic_account.transactions[0]["description"] == "Opening Deposit"

    def test_negative_initial_balance_raises_error(self):
        """Negative initial balance should raise InvalidAmountError."""
        with pytest.raises(InvalidAmountError):
            BankAccount("Ali Hassan", -1000)

    def test_zero_initial_balance_is_valid(self):
        """Zero initial balance should be allowed."""
        account = BankAccount("Ali Hassan", 0)
        assert account.balance == 0

    def test_float_balance_is_valid(self):
        """Float initial balance should be accepted."""
        account = BankAccount("Ali Hassan", 1000.50)
        assert account.balance == 1000.50


# ─────────────────────────────────────────
# DEPOSIT TESTS
# ─────────────────────────────────────────

class TestDeposit:
    """Tests for the deposit method."""

    def test_basic_deposit_increases_balance(self, basic_account):
        """Deposit should increase the balance by the deposited amount."""
        initial = basic_account.balance
        basic_account.deposit(500)
        assert basic_account.balance == initial + 500

    def test_deposit_returns_new_balance(self, basic_account):
        """Deposit should return the new balance."""
        result = basic_account.deposit(500)
        assert result == 10500

    def test_multiple_deposits_accumulate(self, basic_account):
        """Multiple deposits should all accumulate."""
        basic_account.deposit(1000)
        basic_account.deposit(2000)
        basic_account.deposit(3000)
        assert basic_account.balance == 16000

    def test_deposit_creates_transaction_record(self, basic_account):
        """Each deposit should create a transaction entry."""
        before = len(basic_account.transactions)
        basic_account.deposit(500)
        assert len(basic_account.transactions) == before + 1

    def test_deposit_transaction_has_correct_type(self, basic_account):
        """Deposit transaction should be of type 'credit'."""
        basic_account.deposit(500)
        last = basic_account.transactions[-1]
        assert last["type"] == "credit"

    def test_deposit_transaction_records_amount(self, basic_account):
        """Transaction record should include the deposited amount."""
        basic_account.deposit(750)
        last = basic_account.transactions[-1]
        assert last["amount"] == 750

    def test_deposit_transaction_records_balance_after(self, basic_account):
        """Transaction should record the balance after deposit."""
        basic_account.deposit(500)
        last = basic_account.transactions[-1]
        assert last["balance_after"] == 10500

    def test_deposit_with_custom_description(self, basic_account):
        """Deposit should accept a custom description."""
        basic_account.deposit(5000, "Monthly Salary")
        last = basic_account.transactions[-1]
        assert last["description"] == "Monthly Salary"

    @pytest.mark.parametrize("amount", [0, -1, -100, -0.01])
    def test_deposit_invalid_amounts_raise_error(self, basic_account, amount):
        """Zero and negative amounts should raise InvalidAmountError."""
        with pytest.raises(InvalidAmountError):
            basic_account.deposit(amount)

    @pytest.mark.parametrize("amount", [0.01, 1, 100, 1000, 99999.99])
    def test_deposit_valid_amounts_accepted(self, basic_account, amount):
        """Valid positive amounts should be accepted without error."""
        initial = basic_account.balance
        basic_account.deposit(amount)
        assert basic_account.balance == pytest.approx(initial + amount)

    def test_deposit_string_amount_raises_error(self, basic_account):
        """String amounts should raise InvalidAmountError."""
        with pytest.raises(InvalidAmountError):
            basic_account.deposit("500")

    def test_deposit_none_raises_error(self, basic_account):
        """None amount should raise InvalidAmountError."""
        with pytest.raises(InvalidAmountError):
            basic_account.deposit(None)

    def test_deposit_float_amount(self, basic_account):
        """Float amounts should be accepted."""
        basic_account.deposit(99.99)
        assert basic_account.balance == pytest.approx(10099.99)


# ─────────────────────────────────────────
# WITHDRAWAL TESTS
# ─────────────────────────────────────────

class TestWithdraw:
    """Tests for the withdraw method."""

    def test_basic_withdrawal_decreases_balance(self, basic_account):
        """Withdrawal should decrease balance by the withdrawn amount."""
        basic_account.withdraw(3000)
        assert basic_account.balance == 7000

    def test_withdrawal_returns_new_balance(self, basic_account):
        """Withdraw should return the new balance."""
        result = basic_account.withdraw(3000)
        assert result == 7000

    def test_withdraw_entire_balance(self, basic_account):
        """Should be able to withdraw entire balance."""
        basic_account.withdraw(10000)
        assert basic_account.balance == 0

    def test_withdrawal_creates_transaction(self, basic_account):
        """Each withdrawal should create a transaction record."""
        before = len(basic_account.transactions)
        basic_account.withdraw(500)
        assert len(basic_account.transactions) == before + 1

    def test_withdrawal_transaction_type_is_debit(self, basic_account):
        """Withdrawal transaction should be of type 'debit'."""
        basic_account.withdraw(500)
        last = basic_account.transactions[-1]
        assert last["type"] == "debit"

    def test_withdrawal_exceeds_balance_raises_error(self, basic_account):
        """Withdrawing more than balance should raise InsufficientFundsError."""
        with pytest.raises(InsufficientFundsError):
            basic_account.withdraw(50000)

    def test_insufficient_funds_error_message(self, basic_account):
        """Error message should contain relevant information."""
        with pytest.raises(InsufficientFundsError) as exc_info:
            basic_account.withdraw(50000)
        error_msg = str(exc_info.value).lower()
        assert "insufficient" in error_msg

    @pytest.mark.parametrize("amount", [0, -1, -100])
    def test_withdraw_invalid_amounts_raise_error(self, basic_account, amount):
        """Zero and negative amounts should raise InvalidAmountError."""
        with pytest.raises(InvalidAmountError):
            basic_account.withdraw(amount)

    def test_withdraw_with_custom_description(self, basic_account):
        """Withdrawal should accept a custom description."""
        basic_account.withdraw(1000, "Rent Payment")
        last = basic_account.transactions[-1]
        assert last["description"] == "Rent Payment"

    def test_consecutive_withdrawals(self, basic_account):
        """Multiple withdrawals should each decrease balance."""
        basic_account.withdraw(2000)
        basic_account.withdraw(3000)
        assert basic_account.balance == 5000


# ─────────────────────────────────────────
# TRANSFER TESTS
# ─────────────────────────────────────────

class TestTransfer:
    """Tests for the transfer method."""

    def test_transfer_decreases_sender_balance(self, two_accounts):
        """Transfer should decrease the sender's balance."""
        sender, receiver = two_accounts
        sender.transfer(receiver, 5000)
        assert sender.balance == 15000

    def test_transfer_increases_receiver_balance(self, two_accounts):
        """Transfer should increase the receiver's balance."""
        sender, receiver = two_accounts
        sender.transfer(receiver, 5000)
        assert receiver.balance == 10000

    def test_transfer_creates_transactions_in_both(self, two_accounts):
        """Transfer should create transaction records in both accounts."""
        sender, receiver = two_accounts
        sender_before = len(sender.transactions)
        receiver_before = len(receiver.transactions)

        sender.transfer(receiver, 5000)

        assert len(sender.transactions) == sender_before + 1
        assert len(receiver.transactions) == receiver_before + 1

    def test_transfer_insufficient_funds(self, two_accounts):
        """Transfer of more than balance should raise error."""
        sender, receiver = two_accounts
        with pytest.raises(InsufficientFundsError):
            sender.transfer(receiver, 100000)

    def test_transfer_returns_sender_new_balance(self, two_accounts):
        """Transfer should return the sender's new balance."""
        sender, receiver = two_accounts
        result = sender.transfer(receiver, 5000)
        assert result == 15000

    def test_transfer_amount_zero_raises_error(self, two_accounts):
        """Transferring zero amount should raise error."""
        sender, receiver = two_accounts
        with pytest.raises(InvalidAmountError):
            sender.transfer(receiver, 0)


# ─────────────────────────────────────────
# PROPERTY TESTS
# ─────────────────────────────────────────

class TestProperties:
    """Tests for properties and special methods."""

    def test_balance_property_is_read_only(self, basic_account):
        """Balance should not be directly settable."""
        with pytest.raises(AttributeError):
            basic_account.balance = 99999

    def test_len_returns_transaction_count(self, account_with_history):
        """len() should return the number of transactions."""
        assert len(account_with_history) == 5    # 1 opening + 4 operations

    def test_str_contains_owner(self, basic_account):
        """str() should include the owner's name."""
        assert "Ali Hassan" in str(basic_account)

    def test_str_contains_balance(self, basic_account):
        """str() should include the balance."""
        result = str(basic_account)
        assert "10" in result    # balance is 10,000

    def test_eq_same_account(self, basic_account):
        """Account should equal itself."""
        assert basic_account == basic_account

    def test_eq_different_accounts(self, basic_account, empty_account):
        """Different accounts should not be equal."""
        assert basic_account != empty_account

    def test_lt_compares_balances(self, basic_account, rich_account):
        """< operator should compare balances."""
        assert basic_account < rich_account

    def test_gt_compares_balances(self, rich_account, basic_account):
        """> operator should compare balances."""
        assert rich_account > basic_account

    def test_add_merges_accounts(self, basic_account, empty_account):
        """+ operator should create merged account with combined balance."""
        empty_account.deposit(5000)
        merged = basic_account + empty_account
        assert merged.balance == 15000

    def test_add_invalid_type_raises_error(self, basic_account):
        """Adding non-account should raise TypeError."""
        with pytest.raises(TypeError):
            _ = basic_account + 5000


# ─────────────────────────────────────────
# CLASS AND STATIC METHOD TESTS
# ─────────────────────────────────────────

class TestClassAndStaticMethods:
    """Tests for @classmethod and @staticmethod."""

    def test_get_bank_info_returns_dict(self):
        """get_bank_info should return a dictionary."""
        info = BankAccount.get_bank_info()
        assert isinstance(info, dict)
        assert "name" in info
        assert "total_accounts" in info

    def test_get_bank_info_name(self):
        """Bank name should match the class variable."""
        info = BankAccount.get_bank_info()
        assert info["name"] == BankAccount.bank_name

    @pytest.mark.parametrize("amount, expected", [
        (100, True),
        (0.01, True),
        (0, False),
        (-1, False),
        ("100", False),
        (None, False),
    ])
    def test_validate_amount_static(self, amount, expected):
        """validate_amount should return True only for positive numbers."""
        assert BankAccount.validate_amount(amount) == expected

    def test_to_dict_returns_correct_structure(self, basic_account):
        """to_dict should return a properly structured dictionary."""
        data = basic_account.to_dict()
        required_keys = ["account_id", "owner", "balance",
                         "account_type", "created_at", "transactions"]
        for key in required_keys:
            assert key in data

    def test_to_dict_values_match_account(self, basic_account):
        """to_dict values should match account attributes."""
        data = basic_account.to_dict()
        assert data["owner"] == basic_account.owner
        assert data["balance"] == basic_account.balance
        assert data["account_id"] == basic_account.account_id