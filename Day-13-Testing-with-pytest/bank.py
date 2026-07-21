# ============================================================
# BANK ACCOUNT SYSTEM — COMPLETE OOP IMPLEMENTATION
# Day 07 - 180 Days Full Stack AI Engineer Roadmap
# ============================================================

import json
import os
from datetime import datetime
from pathlib import Path


# ─────────────────────────────────────────
# CUSTOM EXCEPTIONS
# ─────────────────────────────────────────

class InsufficientFundsError(Exception):
    """Raised when withdrawal exceeds available balance."""
    pass


class InvalidAmountError(Exception):
    """Raised when an invalid amount is provided."""
    pass


class AccountNotFoundError(Exception):
    """Raised when an account ID does not exist."""
    pass


# ─────────────────────────────────────────
# BASE CLASS
# ─────────────────────────────────────────

class BankAccount:
    """
    Base class representing a standard bank account.

    Attributes:
        bank_name (str): Class variable — name of the bank.
        total_accounts (int): Class variable — total accounts created.
    """

    bank_name = "National Bank"
    total_accounts = 0

    def __init__(self, owner, balance=0, account_type="Standard"):
        """
        Initialize a bank account.

        Args:
            owner (str): Full name of the account owner.
            balance (float): Initial deposit amount.
            account_type (str): Type label for the account.
        """
        # Validate initial balance
        if balance < 0:
            raise InvalidAmountError("Initial balance cannot be negative.")

        # Instance variables
        self.owner = owner.strip().title()
        self._balance = float(balance)
        self.account_type = account_type
        self.transactions = []
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generate account ID
        BankAccount.total_accounts += 1
        self.account_id = f"PNB-{BankAccount.total_accounts:04d}"

        # Record opening transaction if initial balance > 0
        if balance > 0:
            self._record_transaction("Opening Deposit", balance)

    # ─── CORE METHODS ───

    def deposit(self, amount, description="Deposit"):
        """
        Deposit money into the account.

        Args:
            amount (float): Amount to deposit.
            description (str): Transaction description.

        Returns:
            float: New balance after deposit.

        Raises:
            InvalidAmountError: If amount is not positive.
        """
        self._validate_amount(amount)
        self._balance += amount
        self._record_transaction(description, amount, "credit")
        return self._balance

    def withdraw(self, amount, description="Withdrawal"):
        """
        Withdraw money from the account.

        Args:
            amount (float): Amount to withdraw.
            description (str): Transaction description.

        Returns:
            float: New balance after withdrawal.

        Raises:
            InvalidAmountError: If amount is not positive.
            InsufficientFundsError: If balance is insufficient.
        """
        self._validate_amount(amount)

        if amount > self._balance:
            raise InsufficientFundsError(
                f"Insufficient funds. "
                f"Balance: Rs.{self._balance:,.0f} | "
                f"Requested: Rs.{amount:,.0f}"
            )

        self._balance -= amount
        self._record_transaction(description, amount, "debit")
        return self._balance

    def transfer(self, target_account, amount):
        """
        Transfer money to another account.

        Args:
            target_account (BankAccount): Destination account.
            amount (float): Amount to transfer.

        Returns:
            float: New balance after transfer.
        """
        self.withdraw(amount, f"Transfer to {target_account.owner}")
        target_account.deposit(amount, f"Transfer from {self.owner}")
        return self._balance

    # ─── PRIVATE HELPER METHODS ───

    def _validate_amount(self, amount):
        """Validate that amount is a positive number."""
        if not isinstance(amount, (int, float)):
            raise InvalidAmountError(
                f"Amount must be a number, got {type(amount).__name__}."
            )
        if amount <= 0:
            raise InvalidAmountError(
                f"Amount must be positive, got Rs.{amount:,.0f}."
            )

    def _record_transaction(self, description, amount, trans_type="credit"):
        """Record a transaction in the history."""
        transaction = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "description": description,
            "type": trans_type,
            "amount": amount,
            "balance_after": self._balance
        }
        self.transactions.append(transaction)

    # ─── PROPERTY ───

    @property
    def balance(self):
        """Get current balance (read-only)."""
        return self._balance

    # ─── CLASS METHODS ───

    @classmethod
    def get_bank_info(cls):
        """Return bank information."""
        return {
            "name": cls.bank_name,
            "total_accounts": cls.total_accounts
        }

    @classmethod
    def from_dict(cls, data):
        """Create account from a dictionary (for loading from JSON)."""
        account = cls(data["owner"], 0, data.get("account_type", "Standard"))
        account._balance = data["balance"]
        account.account_id = data["account_id"]
        account.created_at = data["created_at"]
        account.transactions = data.get("transactions", [])
        return account

    # ─── STATIC METHODS ───

    @staticmethod
    def validate_amount(amount):
        """Check if an amount is valid without raising an error."""
        return isinstance(amount, (int, float)) and amount > 0

    # ─── DISPLAY METHODS ───

    def get_statement(self, last_n=None):
        """
        Generate account statement.

        Args:
            last_n (int): Show only last N transactions. None shows all.
        """
        transactions = self.transactions
        if last_n:
            transactions = transactions[-last_n:]

        print(f"\n{'=' * 58}")
        print(f"  {self.bank_name}")
        print(f"  ACCOUNT STATEMENT")
        print(f"{'=' * 58}")
        print(f"  Account ID:    {self.account_id}")
        print(f"  Account Type:  {self.account_type}")
        print(f"  Owner:         {self.owner}")
        print(f"  Opened:        {self.created_at}")
        print(f"  Current Balance: Rs. {self._balance:>10,.2f}")
        print(f"{'─' * 58}")
        print(f"  {'Date':<16} {'Description':<22} {'Type':<8} {'Amount':>9}")
        print(f"{'─' * 58}")

        for t in transactions:
            sign = "+" if t["type"] == "credit" else "-"
            print(
                f"  {t['date']:<16} "
                f"{t['description']:<22} "
                f"{t['type'].upper():<8} "
                f"{sign}Rs.{t['amount']:>7,.0f}"
            )

        print(f"{'─' * 58}")
        print(f"  Total Transactions: {len(self.transactions)}")
        print(f"{'=' * 58}\n")

    def to_dict(self):
        """Convert account to dictionary for JSON storage."""
        return {
            "account_id": self.account_id,
            "owner": self.owner,
            "balance": self._balance,
            "account_type": self.account_type,
            "created_at": self.created_at,
            "transactions": self.transactions
        }

    # ─── DUNDER METHODS ───

    def __str__(self):
        return (f"[{self.account_id}] {self.owner} "
                f"({self.account_type}) — Rs. {self._balance:,.0f}")

    def __repr__(self):
        return (f"BankAccount(owner='{self.owner}', "
                f"balance={self._balance}, "
                f"type='{self.account_type}')")

    def __len__(self):
        """Return number of transactions."""
        return len(self.transactions)

    def __eq__(self, other):
        if not isinstance(other, BankAccount):
            return False
        return self.account_id == other.account_id

    def __lt__(self, other):
        """Compare by balance."""
        return self._balance < other._balance

    def __le__(self, other):
        return self._balance <= other._balance

    def __gt__(self, other):
        return self._balance > other._balance

    def __add__(self, other):
        """Merge two accounts — returns a new account."""
        if not isinstance(other, BankAccount):
            raise TypeError("Can only merge two BankAccount objects.")
        merged = BankAccount(
            f"{self.owner} & {other.owner}",
            self._balance + other._balance,
            "Merged"
        )
        return merged

    def __contains__(self, description):
        """Check if a transaction description exists in history."""
        return any(description.lower() in t["description"].lower()
                   for t in self.transactions)


# ─────────────────────────────────────────
# CHILD CLASS 1 — SAVINGS ACCOUNT
# ─────────────────────────────────────────

class SavingsAccount(BankAccount):
    """
    Savings account with interest rate and withdrawal limits.
    Inherits from BankAccount.
    """

    MIN_BALANCE = 5000     # minimum balance requirement
    MAX_WITHDRAWALS = 3    # maximum withdrawals per month

    def __init__(self, owner, balance=0, interest_rate=0.06):
        """
        Initialize savings account.

        Args:
            owner (str): Account owner name.
            balance (float): Initial balance.
            interest_rate (float): Annual interest rate (0.06 = 6%).
        """
        if balance < self.MIN_BALANCE:
            raise InvalidAmountError(
                f"Savings account requires minimum balance of "
                f"Rs. {self.MIN_BALANCE:,}."
            )

        super().__init__(owner, balance, "Savings")
        self.interest_rate = interest_rate
        self.monthly_withdrawals = 0

    def withdraw(self, amount, description="Withdrawal"):
        """
        Override withdrawal — enforces monthly limit.
        """
        if self.monthly_withdrawals >= self.MAX_WITHDRAWALS:
            raise InsufficientFundsError(
                f"Monthly withdrawal limit ({self.MAX_WITHDRAWALS}) reached."
            )

        remaining_after = self._balance - amount
        if remaining_after < self.MIN_BALANCE:
            raise InsufficientFundsError(
                f"Withdrawal would breach minimum balance of "
                f"Rs. {self.MIN_BALANCE:,}."
            )

        self.monthly_withdrawals += 1
        return super().withdraw(amount, description)

    def add_interest(self):
        """
        Add monthly interest to the account.

        Returns:
            float: Interest amount added.
        """
        monthly_rate = self.interest_rate / 12
        interest = self._balance * monthly_rate
        self._balance += interest
        self._record_transaction(
            f"Interest ({self.interest_rate * 100:.1f}% p.a.)",
            interest,
            "credit"
        )
        self.monthly_withdrawals = 0    # reset monthly counter
        return interest

    def reset_monthly_withdrawals(self):
        """Reset withdrawal counter at start of new month."""
        self.monthly_withdrawals = 0

    @property
    def withdrawals_remaining(self):
        """How many withdrawals left this month."""
        return self.MAX_WITHDRAWALS - self.monthly_withdrawals

    def __str__(self):
        return (f"[{self.account_id}] {self.owner} "
                f"(Savings {self.interest_rate * 100:.0f}% p.a.) "
                f"— Rs. {self._balance:,.0f} "
                f"[{self.withdrawals_remaining} withdrawals left]")


# ─────────────────────────────────────────
# CHILD CLASS 2 — CHECKING ACCOUNT
# ─────────────────────────────────────────

class CheckingAccount(BankAccount):
    """
    Checking account with overdraft protection.
    Inherits from BankAccount.
    """

    def __init__(self, owner, balance=0, overdraft_limit=25000):
        """
        Initialize checking account.

        Args:
            owner (str): Account owner name.
            balance (float): Initial balance.
            overdraft_limit (float): Maximum overdraft allowed.
        """
        super().__init__(owner, balance, "Checking")
        self.overdraft_limit = overdraft_limit

    def withdraw(self, amount, description="Withdrawal"):
        """
        Override withdrawal — allows overdraft up to limit.
        """
        self._validate_amount(amount)

        available = self._balance + self.overdraft_limit
        if amount > available:
            raise InsufficientFundsError(
                f"Exceeds overdraft limit. "
                f"Max available: Rs. {available:,.0f}"
            )

        self._balance -= amount
        self._record_transaction(description, amount, "debit")

        if self._balance < 0:
            print(f"Overdraft: Rs. {abs(self._balance):,.0f} "
                  f"(Limit: Rs. {self.overdraft_limit:,.0f})")

        return self._balance

    @property
    def available_balance(self):
        """Total spendable amount including overdraft."""
        return self._balance + self.overdraft_limit

    def __str__(self):
        return (f"[{self.account_id}] {self.owner} "
                f"(Checking | Overdraft: Rs.{self.overdraft_limit:,.0f}) "
                f"— Rs. {self._balance:,.0f} "
                f"[Available: Rs.{self.available_balance:,.0f}]")


# ─────────────────────────────────────────
# CHILD CLASS 3 — PREMIUM ACCOUNT
# ─────────────────────────────────────────

class PremiumAccount(SavingsAccount):
    """
    Premium account with rewards points and cashback.
    Inherits from SavingsAccount (which inherits from BankAccount).
    This shows MULTI-LEVEL inheritance.
    """

    CASHBACK_RATE = 0.02       # 2% cashback on withdrawals
    POINTS_PER_1000 = 10       # 10 points per Rs. 1000 deposited

    def __init__(self, owner, balance=0):
        super().__init__(owner, balance, interest_rate=0.08)  # 8% interest
        self.account_type = "Premium"
        self.rewards_points = 0
        self.total_cashback = 0

    def deposit(self, amount, description="Deposit"):
        """Override — earn rewards points on deposit."""
        result = super().deposit(amount, description)
        points_earned = int(amount / 1000) * self.POINTS_PER_1000
        self.rewards_points += points_earned
        if points_earned > 0:
            print(f"{points_earned} reward points earned! "
                  f"Total: {self.rewards_points}")
        return result

    def withdraw(self, amount, description="Withdrawal"):
        """Override — earn cashback on withdrawals."""
        result = super().withdraw(amount, description)
        cashback = amount * self.CASHBACK_RATE
        self._balance += cashback
        self.total_cashback += cashback
        self._record_transaction(
            f"Cashback ({self.CASHBACK_RATE * 100:.0f}%)",
            cashback,
            "credit"
        )
        print(f"Cashback: Rs. {cashback:,.0f} credited! "
              f"Total cashback: Rs. {self.total_cashback:,.0f}")
        return result

    def redeem_points(self, points):
        """Redeem reward points for cash (100 points = Rs. 10)."""
        if points > self.rewards_points:
            raise ValueError(
                f"Insufficient points. "
                f"Available: {self.rewards_points}"
            )
        cash_value = points / 10
        self.rewards_points -= points
        self._balance += cash_value
        self._record_transaction(
            f"Points Redemption ({points} pts)",
            cash_value,
            "credit"
        )
        return cash_value

    def __str__(self):
        return (f"[{self.account_id}] {self.owner} "
                f"(Premium | {self.rewards_points} pts) "
                f"— Rs. {self._balance:,.0f}")


# ─────────────────────────────────────────
# BANK SYSTEM — Manages All Accounts
# ─────────────────────────────────────────

class BankSystem:
    """
    Manages all bank accounts and handles persistence.
    """

    DATA_FILE = Path(__file__).parent / "bank_data.json"

    def __init__(self):
        self.accounts = {}    # account_id → account object
        self.load_accounts()

    def create_account(self, account_type, owner, balance,
                       **kwargs):
        """
        Create a new account of the specified type.

        Args:
            account_type (str): 'standard', 'savings', 'checking', 'premium'
            owner (str): Account owner name.
            balance (float): Initial balance.
            **kwargs: Additional arguments for specific account types.

        Returns:
            BankAccount: The created account.
        """
        account_type = account_type.lower()

        if account_type == "standard":
            account = BankAccount(owner, balance)
        elif account_type == "savings":
            rate = kwargs.get("interest_rate", 0.06)
            account = SavingsAccount(owner, balance, rate)
        elif account_type == "checking":
            overdraft = kwargs.get("overdraft_limit", 25000)
            account = CheckingAccount(owner, balance, overdraft)
        elif account_type == "premium":
            account = PremiumAccount(owner, balance)
        else:
            raise ValueError(f"Unknown account type: '{account_type}'")

        self.accounts[account.account_id] = account
        self.save_accounts()
        return account

    def get_account(self, account_id):
        """
        Retrieve account by ID.

        Raises:
            AccountNotFoundError: If account does not exist.
        """
        account = self.accounts.get(account_id.upper())
        if not account:
            raise AccountNotFoundError(
                f"No account found with ID '{account_id}'."
            )
        return account

    def list_accounts(self):
        """Display all accounts."""
        if not self.accounts:
            print("  No accounts found.")
            return

        print(f"\n{'=' * 58}")
        print(f"  ALL ACCOUNTS — {BankAccount.bank_name}")
        print(f"{'=' * 58}")

        # Sort by balance (highest first) using polymorphism
        sorted_accounts = sorted(
            self.accounts.values(),
            reverse=True    # uses __gt__ dunder method
        )

        for account in sorted_accounts:
            print(f"  {account}")    # uses __str__ dunder method

        print(f"{'─' * 58}")
        total = sum(a.balance for a in self.accounts.values())
        print(f"  Total Accounts: {len(self.accounts)}")
        print(f"  Total Deposits: Rs. {total:,.0f}")
        print(f"{'=' * 58}")

    def save_accounts(self):
        """Save all accounts to JSON file."""
        try:
            data = {
                "bank_name": BankAccount.bank_name,
                "total_accounts_ever": BankAccount.total_accounts,
                "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "accounts": {
                    acc_id: acc.to_dict()
                    for acc_id, acc in self.accounts.items()
                }
            }
            with open(self.DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Could not save: {e}")

    def load_accounts(self):
        """Load accounts from JSON file."""
        if not self.DATA_FILE.exists():
            return

        try:
            with open(self.DATA_FILE, "r") as f:
                data = json.load(f)

            BankAccount.total_accounts = data.get(
                "total_accounts_ever", 0
            )

            for acc_id, acc_data in data.get("accounts", {}).items():
                acc_type = acc_data.get("account_type", "Standard")

                if acc_type == "Savings":
                    account = SavingsAccount.__new__(SavingsAccount)
                    account.__dict__.update({
                        "interest_rate": 0.06,
                        "monthly_withdrawals": 0
                    })
                elif acc_type == "Checking":
                    account = CheckingAccount.__new__(CheckingAccount)
                    account.__dict__.update({"overdraft_limit": 25000})
                elif acc_type == "Premium":
                    account = PremiumAccount.__new__(PremiumAccount)
                    account.__dict__.update({
                        "interest_rate": 0.08,
                        "monthly_withdrawals": 0,
                        "rewards_points": 0,
                        "total_cashback": 0
                    })
                else:
                    account = BankAccount.__new__(BankAccount)

                account.owner = acc_data["owner"]
                account._balance = acc_data["balance"]
                account.account_type = acc_data.get("account_type", "Standard")
                account.account_id = acc_data["account_id"]
                account.created_at = acc_data["created_at"]
                account.transactions = acc_data.get("transactions", [])

                self.accounts[acc_id] = account

            print(f"  Loaded {len(self.accounts)} account(s).")

        except Exception as e:
            print(f"  Could not load saved data: {e}")


# ─────────────────────────────────────────
# MENU SYSTEM
# ─────────────────────────────────────────

def display_header(title):
    """Display a formatted section header."""
    print(f"\n{'=' * 58}")
    print(f"  {title}")
    print(f"{'=' * 58}")


def get_account_id(bank):
    """Helper to select an account from the list."""
    bank.list_accounts()
    return input("\n  Enter Account ID (e.g. PNB-0001): ").strip().upper()


def handle_create_account(bank):
    """Handle account creation flow."""
    display_header("CREATE NEW ACCOUNT")

    print("  Account Types:")
    print("  1. Standard  — Basic account, no frills")
    print("  2. Savings   — Earns interest (6% p.a.), min balance Rs.5,000")
    print("  3. Checking  — Overdraft protection up to Rs.25,000")
    print("  4. Premium   — 8% interest + cashback + reward points")

    type_map = {"1": "standard", "2": "savings",
                "3": "checking", "4": "premium"}
    choice = input("\n  Select type (1-4): ").strip()

    if choice not in type_map:
        print("Invalid choice.")
        return

    account_type = type_map[choice]
    owner = input("  Account owner name: ").strip()
    if not owner:
        print("Name cannot be empty.")
        return

    try:
        balance = float(input("  Initial deposit (Rs.): ").replace(",", ""))
    except ValueError:
        print("Invalid amount.")
        return

    try:
        account = bank.create_account(account_type, owner, balance)
        print(f"\nAccount created!")
        print(f"  {account}")
    except (InvalidAmountError, ValueError) as e:
        print(f"\n{e}")
    except Exception as e:
        print(f"\nError: {e}")


def handle_deposit(bank):
    """Handle deposit flow."""
    display_header("DEPOSIT FUNDS")

    try:
        acc_id = get_account_id(bank)
        account = bank.get_account(acc_id)
        amount = float(input("  Deposit amount (Rs.): ").replace(",", ""))
        desc = input("  Description (optional): ").strip() or "Deposit"

        new_balance = account.deposit(amount, desc)
        bank.save_accounts()
        print(f"\nDeposited Rs. {amount:,.0f}")
        print(f"  New Balance: Rs. {new_balance:,.0f}")

    except (AccountNotFoundError, InvalidAmountError) as e:
        print(f"\n  ❌ {e}")
    except ValueError:
        print("\n Invalid amount entered.")


def handle_withdraw(bank):
    """Handle withdrawal flow."""
    display_header("WITHDRAW FUNDS")

    try:
        acc_id = get_account_id(bank)
        account = bank.get_account(acc_id)
        amount = float(input("  Withdrawal amount (Rs.): ").replace(",", ""))
        desc = input("  Description (optional): ").strip() or "Withdrawal"

        new_balance = account.withdraw(amount, desc)
        bank.save_accounts()
        print(f"\nWithdrawn Rs. {amount:,.0f}")
        print(f"  New Balance: Rs. {new_balance:,.0f}")

    except (AccountNotFoundError, InsufficientFundsError,
            InvalidAmountError) as e:
        print(f"\n  ❌ {e}")
    except ValueError:
        print("\nInvalid amount entered.")


def handle_transfer(bank):
    """Handle transfer flow."""
    display_header("TRANSFER FUNDS")

    try:
        print("  FROM account:")
        from_id = get_account_id(bank)
        from_account = bank.get_account(from_id)

        print("\n  TO account:")
        to_id = get_account_id(bank)
        to_account = bank.get_account(to_id)

        if from_id == to_id:
            print("\nCannot transfer to the same account.")
            return

        amount = float(input("  Transfer amount (Rs.): ").replace(",", ""))
        from_account.transfer(to_account, amount)
        bank.save_accounts()
        print(f"\nTransferred Rs. {amount:,.0f} "
              f"from {from_account.owner} to {to_account.owner}")

    except (AccountNotFoundError, InsufficientFundsError,
            InvalidAmountError) as e:
        print(f"\n{e}")
    except ValueError:
        print("\nInvalid amount entered.")


def handle_statement(bank):
    """Handle statement flow."""
    display_header("ACCOUNT STATEMENT")

    try:
        acc_id = get_account_id(bank)
        account = bank.get_account(acc_id)

        choice = input("  Show last N transactions? (Enter number or press Enter for all): ").strip()
        last_n = int(choice) if choice.isdigit() else None

        account.get_statement(last_n)

    except AccountNotFoundError as e:
        print(f"\n{e}")


def handle_interest(bank):
    """Add interest to savings accounts."""
    display_header("ADD MONTHLY INTEREST")

    savings_accounts = [
        acc for acc in bank.accounts.values()
        if isinstance(acc, SavingsAccount)
    ]

    if not savings_accounts:
        print("  No savings accounts found.")
        return

    print(f"  Found {len(savings_accounts)} savings account(s).")
    confirm = input("  Add interest to all savings accounts? (yes/no): ")

    if confirm.lower() not in ["yes", "y"]:
        print("  Cancelled.")
        return

    for account in savings_accounts:
        interest = account.add_interest()
        print(f"{account.owner}: +Rs. {interest:,.2f} interest added")

    bank.save_accounts()


def main():
    """Main function — Bank Account System."""

    print("\n" + "=" * 58)
    print("       NATIONAL BANK")
    print("       Complete Banking System — Day 07")
    print("=" * 58)

    bank = BankSystem()

    # Create demo accounts if none exist
    if not bank.accounts:
        print("\n  Creating demo accounts...")
        try:
            bank.create_account("premium", "Humayun Kiani", 100000)
            bank.create_account("savings", "Ali Hassan", 50000)
            bank.create_account("checking", "Sara Ahmed", 30000)
            print("  3 demo accounts created.")
        except Exception as e:
            print(f"  Demo setup error: {e}")

    while True:
        print("\n" + "─" * 58)
        print("  MAIN MENU")
        print("─" * 58)
        print("  1.  View all accounts")
        print("  2.  Create new account")
        print("  3.  Deposit funds")
        print("  4.  Withdraw funds")
        print("  5.  Transfer funds")
        print("  6.  View account statement")
        print("  7.  Add monthly interest (savings)")
        print("  8.  Exit")
        print("─" * 58)

        choice = input("  Choose option (1-8): ").strip()

        if choice == "1":
            bank.list_accounts()
        elif choice == "2":
            handle_create_account(bank)
        elif choice == "3":
            handle_deposit(bank)
        elif choice == "4":
            handle_withdraw(bank)
        elif choice == "5":
            handle_transfer(bank)
        elif choice == "6":
            handle_statement(bank)
        elif choice == "7":
            handle_interest(bank)
        elif choice == "8":
            print("\n  Thank you for banking with Python National Bank!")
            print("  See you on Day 8!")
            print("=" * 58 + "\n")
            break
        else:
            print("Invalid option. Choose between 1 and 8.")


if __name__ == "__main__":
    main()