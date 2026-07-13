# ============================================================
# PERSISTENT EXPENSE TRACKER
# Day 06 - 180 Days Full Stack AI Engineer Roadmap
# ============================================================

import json
import csv
import os
from pathlib import Path
from datetime import datetime


# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────

# File paths
BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "expenses.json"
BACKUP_FILE = BASE_DIR / "expenses_backup.json"
CSV_EXPORT_FILE = BASE_DIR / "expenses_export.csv"

# Valid categories
CATEGORIES = [
    "Food", "Transport", "Shopping",
    "Health", "Education", "Entertainment",
    "Bills", "Other"
]

# Default data structure
DEFAULT_DATA = {
    "expenses": [],
    "monthly_budget": 50000,
    "next_id": 1,
    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}


# ─────────────────────────────────────────
# CUSTOM EXCEPTIONS
# ─────────────────────────────────────────

class InvalidCategoryError(Exception):
    """Raised when an invalid expense category is provided."""
    pass


class InvalidAmountError(Exception):
    """Raised when an invalid expense amount is provided."""
    pass


class ExpenseNotFoundError(Exception):
    """Raised when an expense ID does not exist."""
    pass


# ─────────────────────────────────────────
# FILE OPERATIONS — Load and Save
# ─────────────────────────────────────────

def load_data():
    """
    Load expense data from JSON file.

    Returns:
        dict: The loaded data, or default data if file does not exist.
    """
    # If file does not exist, return fresh default data
    if not DATA_FILE.exists():
        print("  No existing data found. Starting fresh.")
        return DEFAULT_DATA.copy()

    try:
        with open(DATA_FILE, "r") as file:
            data = json.load(file)
            expense_count = len(data.get("expenses", []))
            print(f"  Loaded {expense_count} expense(s) from previous session.")
            return data

    except json.JSONDecodeError as e:
        print(f"  Warning: Data file is corrupted ({e}).")
        print("  Attempting to load backup...")
        return load_backup()

    except PermissionError:
        print(f"  Error: Cannot read data file (permission denied).")
        print("  Using in-memory storage for this session.")
        return DEFAULT_DATA.copy()

    except Exception as e:
        print(f"  Unexpected error loading data: {e}")
        return DEFAULT_DATA.copy()


def load_backup():
    """
    Attempt to load data from backup file.

    Returns:
        dict: Backup data or default data if backup also fails.
    """
    if not BACKUP_FILE.exists():
        print("  No backup found. Starting with fresh data.")
        return DEFAULT_DATA.copy()

    try:
        with open(BACKUP_FILE, "r") as file:
            data = json.load(file)
            print(f"  Backup loaded successfully.")
            return data
    except Exception as e:
        print(f"  Backup also corrupted: {e}. Starting fresh.")
        return DEFAULT_DATA.copy()


def save_data(data):
    """
    Save expense data to JSON file with backup.

    Args:
        data (dict): The data to save.

    Returns:
        bool: True if saved successfully, False otherwise.
    """
    try:
        # Create backup of existing data before overwriting
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r") as original:
                    existing_data = original.read()
                with open(BACKUP_FILE, "w") as backup:
                    backup.write(existing_data)
            except Exception:
                pass    # Backup failed — not critical, continue saving

        # Update last modified timestamp
        data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Write main data file
        with open(DATA_FILE, "w") as file:
            json.dump(data, file, indent=4)

        return True

    except PermissionError:
        print("  Error: Cannot write to data file (permission denied).")
        return False

    except OSError as e:
        print(f"  Error saving data (disk issue?): {e}")
        return False

    except Exception as e:
        print(f"  Unexpected error saving data: {e}")
        return False


def export_to_csv(expenses):
    """
    Export all expenses to a CSV file.

    Args:
        expenses (list): List of expense dictionaries.

    Returns:
        bool: True if exported successfully.
    """
    if not expenses:
        print("  No expenses to export.")
        return False

    try:
        with open(CSV_EXPORT_FILE, "w", newline="", encoding="utf-8") as file:
            fieldnames = ["id", "name", "amount", "category", "note", "date"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            for expense in expenses:
                writer.writerow({
                    "id": expense.get("id", ""),
                    "name": expense.get("name", ""),
                    "amount": expense.get("amount", 0),
                    "category": expense.get("category", ""),
                    "note": expense.get("note", ""),
                    "date": expense.get("date", "")
                })

        print(f"  Exported {len(expenses)} expenses to: {CSV_EXPORT_FILE.name}")
        return True

    except PermissionError:
        print("  Error: Cannot write CSV file (is it open in Excel?)")
        return False

    except Exception as e:
        print(f"  Export error: {e}")
        return False


# ─────────────────────────────────────────
# VALIDATION FUNCTIONS
# ─────────────────────────────────────────

def validate_name(name):
    """
    Validate expense name.

    Args:
        name (str): The expense name to validate.

    Returns:
        str: Cleaned and validated name.

    Raises:
        ValueError: If name is empty or too long.
    """
    name = name.strip()
    if not name:
        raise ValueError("Expense name cannot be empty.")
    if len(name) > 50:
        raise ValueError(f"Name too long ({len(name)} chars). Max 50 characters.")
    return name.title()


def validate_amount(amount_str):
    """
    Validate and convert amount string to float.

    Args:
        amount_str (str): The amount as a string.

    Returns:
        float: Validated positive amount.

    Raises:
        InvalidAmountError: If amount is invalid or not positive.
    """
    try:
        amount = float(amount_str.replace(",", ""))    # allow "1,500" format
        if amount <= 0:
            raise InvalidAmountError("Amount must be greater than zero.")
        if amount > 10_000_000:    # 1 crore limit
            raise InvalidAmountError("Amount exceeds maximum limit (1 crore).")
        return round(amount, 2)
    except ValueError:
        raise InvalidAmountError(f"'{amount_str}' is not a valid number.")


def validate_category(category):
    """
    Validate that category is in the allowed list.

    Args:
        category (str): Category to validate.

    Returns:
        str: Validated category name.

    Raises:
        InvalidCategoryError: If category is not in CATEGORIES list.
    """
    category = category.strip().title()
    if category not in CATEGORIES:
        raise InvalidCategoryError(
            f"'{category}' is not valid. Choose from: {', '.join(CATEGORIES)}"
        )
    return category


# ─────────────────────────────────────────
# CORE EXPENSE OPERATIONS
# ─────────────────────────────────────────

def add_expense(data, name, amount, category, note=""):
    """
    Add a validated expense and auto-save.

    Args:
        data (dict): The main data dictionary.
        name (str): Expense name.
        amount (float): Expense amount.
        category (str): Expense category.
        note (str): Optional note.

    Returns:
        dict: The created expense.

    Raises:
        ValueError, InvalidAmountError, InvalidCategoryError
    """
    # Validate all fields
    clean_name = validate_name(name)
    clean_amount = validate_amount(str(amount))
    clean_category = validate_category(category)

    # Create expense object
    expense = {
        "id": data["next_id"],
        "name": clean_name,
        "amount": clean_amount,
        "category": clean_category,
        "note": note.strip()[:100],    # limit note to 100 chars
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    # Add to data and increment ID counter
    data["expenses"].append(expense)
    data["next_id"] += 1

    # Auto-save
    save_data(data)

    return expense


def delete_expense(data, expense_id):
    """
    Delete an expense by ID and auto-save.

    Args:
        data (dict): The main data dictionary.
        expense_id (int): ID of expense to delete.

    Returns:
        dict: The deleted expense.

    Raises:
        ExpenseNotFoundError: If no expense has the given ID.
        ValueError: If expense_id is not a valid integer.
    """
    try:
        expense_id = int(expense_id)
    except (ValueError, TypeError):
        raise ValueError(f"'{expense_id}' is not a valid expense ID.")

    # Find the expense
    for i, expense in enumerate(data["expenses"]):
        if expense["id"] == expense_id:
            removed = data["expenses"].pop(i)
            save_data(data)
            return removed

    raise ExpenseNotFoundError(f"No expense found with ID {expense_id}.")


def get_statistics(expenses):
    """
    Calculate statistics from a list of expenses.

    Args:
        expenses (list): List of expense dictionaries.

    Returns:
        dict: Statistics dictionary or None if no expenses.
    """
    if not expenses:
        return None

    amounts = [e["amount"] for e in expenses]

    return {
        "count": len(expenses),
        "total": sum(amounts),
        "average": sum(amounts) / len(amounts),
        "highest": max(amounts),
        "lowest": min(amounts),
        "highest_expense": max(expenses, key=lambda e: e["amount"]),
        "lowest_expense": min(expenses, key=lambda e: e["amount"])
    }


def get_category_summary(expenses):
    """
    Build category-wise spending summary.

    Args:
        expenses (list): List of expense dictionaries.

    Returns:
        dict: Category names mapped to total spent.
    """
    summary = {}
    for expense in expenses:
        cat = expense["category"]
        summary[cat] = summary.get(cat, 0) + expense["amount"]
    return dict(sorted(summary.items(), key=lambda x: x[1], reverse=True))


def search_expenses(expenses, keyword):
    """Search expenses by name, category, or note."""
    keyword = keyword.lower().strip()
    if not keyword:
        return []
    return [
        e for e in expenses
        if keyword in e["name"].lower()
        or keyword in e["category"].lower()
        or keyword in e.get("note", "").lower()
    ]


# ─────────────────────────────────────────
# DISPLAY FUNCTIONS
# ─────────────────────────────────────────

def display_header(title):
    """Display a formatted section header."""
    print("\n" + "=" * 58)
    print(f"  {title}")
    print("=" * 58)


def display_all_expenses(expenses):
    """Display all expenses in a formatted table."""
    display_header("ALL EXPENSES")

    if not expenses:
        print("  No expenses recorded yet.")
        print("  Use option 2 to add your first expense.")
        return

    print(f"  {'ID':<4} {'Name':<20} {'Amount':>10}  {'Category':<13} {'Date'}")
    print("  " + "─" * 56)

    for expense in expenses:
        print(
            f"  {expense['id']:<4} "
            f"{expense['name']:<20} "
            f"Rs.{expense['amount']:>7,.0f}  "
            f"{expense['category']:<13} "
            f"{expense.get('date', 'N/A')[:10]}"
        )

    stats = get_statistics(expenses)
    print("  " + "─" * 56)
    print(f"  {'Total (' + str(stats['count']) + ' items)':<28} Rs.{stats['total']:>7,.0f}")


def display_statistics(expenses, monthly_budget):
    """Display statistics and budget status."""
    display_header("STATISTICS & BUDGET")

    stats = get_statistics(expenses)

    if not stats:
        print("  No expenses recorded yet.")
        return

    total = stats["total"]
    budget_used_pct = (total / monthly_budget) * 100 if monthly_budget > 0 else 0
    remaining = monthly_budget - total

    print(f"  Total Expenses:     Rs. {total:>10,.0f}")
    print(f"  Average Expense:    Rs. {stats['average']:>10,.0f}")
    print(f"  Highest:            Rs. {stats['highest']:>10,.0f}  "
          f"({stats['highest_expense']['name']})")
    print(f"  Lowest:             Rs. {stats['lowest']:>10,.0f}  "
          f"({stats['lowest_expense']['name']})")
    print(f"  Number of Items:    {stats['count']}")
    print()
    print(f"  Monthly Budget:     Rs. {monthly_budget:>10,.0f}")
    print(f"  Amount Used:        Rs. {total:>10,.0f}  ({budget_used_pct:.1f}%)")
    print(f"  Remaining:          Rs. {remaining:>10,.0f}")

    # Visual budget bar
    filled = min(int(budget_used_pct / 5), 20)
    empty = 20 - filled
    bar = "█" * filled + "░" * empty
    print(f"\n  Budget: [{bar}] {budget_used_pct:.1f}%")

    if budget_used_pct >= 100:
        print("OVER BUDGET!")
    elif budget_used_pct >= 80:
        print("Caution: 80% of budget used.")
    else:
        print("Within budget.")


def display_category_summary(expenses):
    """Display spending by category."""
    display_header("CATEGORY BREAKDOWN")

    if not expenses:
        print("  No expenses recorded yet.")
        return

    summary = get_category_summary(expenses)
    total = sum(summary.values())

    print(f"  {'Category':<15} {'Total':>10}  {'%':>6}  Visual")
    print("  " + "─" * 50)

    for category, amount in summary.items():
        pct = (amount / total) * 100
        bar = "█" * int(pct / 5)
        print(f"  {category:<15} Rs.{amount:>7,.0f}  {pct:>5.1f}%  {bar}")

    print("  " + "─" * 50)
    print(f"  {'TOTAL':<15} Rs.{total:>7,.0f}")


# ─────────────────────────────────────────
# USER INPUT HANDLERS
# ─────────────────────────────────────────

def handle_add_expense(data):
    """Interactive flow for adding a new expense."""
    display_header("ADD NEW EXPENSE")

    # Get and validate name
    while True:
        try:
            name = validate_name(input("  Expense name: "))
            break
        except ValueError as e:
            print(f"  ❌ {e}")

    # Get and validate amount
    while True:
        try:
            amount = validate_amount(input("  Amount (Rs.): "))
            break
        except InvalidAmountError as e:
            print(f"  ❌ {e}")

    # Get and validate category
    print("\n  Categories:")
    for i, cat in enumerate(CATEGORIES, 1):
        print(f"    {i}. {cat}")

    while True:
        try:
            choice = int(input("  Select category number: "))
            if 1 <= choice <= len(CATEGORIES):
                category = CATEGORIES[choice - 1]
                break
            print(f"  ❌ Enter a number between 1 and {len(CATEGORIES)}.")
        except ValueError:
            print("  ❌ Please enter a valid number.")

    # Optional note
    note = input("  Note (optional): ").strip()

    # Add the expense
    try:
        expense = add_expense(data, name, amount, category, note)
        print(f"\n Saved: {expense['name']} — "
              f"Rs. {expense['amount']:,.0f} ({expense['category']})")
    except Exception as e:
        print(f"\n Failed to add expense: {e}")


def handle_delete_expense(data):
    """Interactive flow for deleting an expense."""
    display_header("DELETE EXPENSE")

    if not data["expenses"]:
        print("  No expenses to delete.")
        return

    display_all_expenses(data["expenses"])

    try:
        expense_id = input("\n  Enter expense ID to delete (or 'cancel'): ").strip()

        if expense_id.lower() == "cancel":
            print("  Cancelled.")
            return

        removed = delete_expense(data, expense_id)
        print(f"\n Deleted: {removed['name']} — Rs. {removed['amount']:,.0f}")

    except ExpenseNotFoundError as e:
        print(f"\n  {e}")
    except ValueError as e:
        print(f"\n  {e}")
    except Exception as e:
        print(f"\n  Unexpected error: {e}")


def handle_search(expenses):
    """Interactive flow for searching expenses."""
    display_header("SEARCH EXPENSES")

    keyword = input("  Enter search keyword: ").strip()

    if not keyword:
        print("Search term cannot be empty.")
        return

    results = search_expenses(expenses, keyword)

    if results:
        print(f"\n  Found {len(results)} result(s) for '{keyword}':")
        print(f"  {'ID':<4} {'Name':<20} {'Amount':>10}  {'Category'}")
        print("  " + "─" * 50)
        for e in results:
            print(f"  {e['id']:<4} {e['name']:<20} "
                  f"Rs.{e['amount']:>7,.0f}  {e['category']}")
    else:
        print(f"\n  No expenses found matching '{keyword}'.")


def handle_set_budget(data):
    """Interactive flow for updating the monthly budget."""
    display_header("SET MONTHLY BUDGET")
    print(f"  Current budget: Rs. {data['monthly_budget']:,.0f}")

    while True:
        try:
            new_budget = validate_amount(input("  New monthly budget (Rs.): "))
            data["monthly_budget"] = new_budget
            save_data(data)
            print(f"Budget updated to Rs. {new_budget:,.0f}")
            break
        except InvalidAmountError as e:
            print(f"{e}")


def handle_export(expenses):
    """Handle CSV export."""
    display_header("EXPORT TO CSV")
    export_to_csv(expenses)


# ─────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────

def main():
    """Main function — runs the persistent expense tracker."""

    print("\n" + "=" * 58)
    print("       PERSISTENT EXPENSE TRACKER")
    print("       180 Days Full Stack AI — Day 06")
    print("=" * 58)

    # Load data from file (or create fresh)
    data = load_data()

    while True:
        expenses = data["expenses"]
        budget = data["monthly_budget"]

        # Quick summary in menu
        total_spent = sum(e["amount"] for e in expenses) if expenses else 0
        remaining = budget - total_spent

        print("\n" + "─" * 58)
        print(f"  Budget: Rs.{budget:,.0f}  |  "
              f"Spent: Rs.{total_spent:,.0f}  |  "
              f"Left: Rs.{remaining:,.0f}")
        print("─" * 58)
        print("  1. View all expenses")
        print("  2. Add new expense")
        print("  3. Delete expense")
        print("  4. Search expenses")
        print("  5. Category breakdown")
        print("  6. Statistics & budget")
        print("  7. Export to CSV")
        print("  8. Set monthly budget")
        print("  9. Exit")
        print("─" * 58)

        choice = input("  Choose option (1-9): ").strip()

        if choice == "1":
            display_all_expenses(expenses)

        elif choice == "2":
            handle_add_expense(data)

        elif choice == "3":
            handle_delete_expense(data)

        elif choice == "4":
            handle_search(expenses)

        elif choice == "5":
            display_category_summary(expenses)

        elif choice == "6":
            display_statistics(expenses, budget)

        elif choice == "7":
            handle_export(expenses)

        elif choice == "8":
            handle_set_budget(data)

        elif choice == "9":
            print("\n  Data saved. See you next time!")
            print("  Keep building, keep learning!")
            print("=" * 58 + "\n")
            break

        else:
            print("Invalid option. Please choose between 1 and 9.")


if __name__ == "__main__":
    main()