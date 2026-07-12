# ============================================================
# PERSONAL EXPENSE TRACKER
# Day 05 - 180 Days Full Stack AI Engineer Roadmap
# ============================================================


# ─────────────────────────────────────────
# DATA STORAGE
# ─────────────────────────────────────────

# Global list to store all expenses
# Each expense is a dictionary
expenses = []

# Available categories
CATEGORIES = [
    "Food", "Transport", "Shopping",
    "Health", "Education", "Entertainment",
    "Bills", "Other"
]

# Monthly budget (can be changed by user)
monthly_budget = 50000


# ─────────────────────────────────────────
# CORE FUNCTIONS — Data Operations
# ─────────────────────────────────────────

def add_expense(name, amount, category, note=""):
    """
    Add a new expense to the tracker.

    Args:
        name (str): Name/description of the expense.
        amount (float): Amount spent in rupees.
        category (str): Category of the expense.
        note (str): Optional note about the expense.

    Returns:
        dict: The created expense dictionary.
    """
    expense = {
        "id": len(expenses) + 1,
        "name": name.strip().title(),
        "amount": float(amount),
        "category": category.strip().title(),
        "note": note.strip()
    }
    expenses.append(expense)
    return expense


def delete_expense(expense_id):
    """
    Delete an expense by its ID.

    Args:
        expense_id (int): The ID of the expense to delete.

    Returns:
        bool: True if deleted, False if not found.
    """
    for i, expense in enumerate(expenses):
        if expense["id"] == expense_id:
            removed = expenses.pop(i)
            print(f"  Deleted: {removed['name']} (Rs. {removed['amount']:,.0f})")
            return True
    return False


def get_total(*expense_list):
    """
    Calculate the total amount of expenses.

    Args:
        *expense_list: Optional specific list of expenses.
                       Uses global expenses if not provided.

    Returns:
        float: Total amount of all expenses.
    """
    target = expense_list[0] if expense_list else expenses
    return sum(e["amount"] for e in target)


def get_average(*expense_list):
    """
    Calculate the average expense amount.

    Returns:
        float: Average amount, or 0 if no expenses.
    """
    target = expense_list[0] if expense_list else expenses
    if not target:
        return 0
    return get_total(target) / len(target)


def get_by_category(category):
    """
    Filter expenses by category.

    Args:
        category (str): Category name to filter by.

    Returns:
        list: List of expenses matching the category.
    """
    return [e for e in expenses if e["category"].lower() == category.lower()]


def search_expenses(keyword):
    """
    Search expenses by name or note.

    Args:
        keyword (str): Search term to look for.

    Returns:
        list: List of expenses matching the keyword.
    """
    keyword = keyword.lower()
    return [
        e for e in expenses
        if keyword in e["name"].lower() or keyword in e["note"].lower()
    ]


def get_highest_expense():
    """Return the expense with the highest amount."""
    if not expenses:
        return None
    return max(expenses, key=lambda e: e["amount"])


def get_lowest_expense():
    """Return the expense with the lowest amount."""
    if not expenses:
        return None
    return min(expenses, key=lambda e: e["amount"])


def get_category_summary():
    """
    Build a summary of spending by category.

    Returns:
        dict: Category names mapped to total spent.
    """
    summary = {}
    for expense in expenses:
        category = expense["category"]
        summary[category] = summary.get(category, 0) + expense["amount"]
    return summary


# ─────────────────────────────────────────
# DISPLAY FUNCTIONS — Formatting Output
# ─────────────────────────────────────────

def display_header(title):
    """Display a formatted section header."""
    print("\n" + "=" * 55)
    print(f"  {title}")
    print("=" * 55)


def display_expense_row(expense):
    """Display a single expense as a formatted table row."""
    print(
        f"  {expense['id']:<4} "
        f"{expense['name']:<20} "
        f"Rs.{expense['amount']:>8,.0f}  "
        f"{expense['category']:<14}"
        f"{expense['note'][:15] if expense['note'] else ''}"
    )


def display_all_expenses():
    """Display all expenses in a formatted table."""
    display_header("ALL EXPENSES")

    if not expenses:
        print("  No expenses recorded yet.")
        return

    # Table header
    print(f"  {'ID':<4} {'Name':<20} {'Amount':>12}  {'Category':<14} {'Note'}")
    print("  " + "-" * 53)

    for expense in expenses:
        display_expense_row(expense)

    print("  " + "-" * 53)
    print(f"  {'TOTAL':<25} Rs.{get_total():>8,.0f}")
    print(f"  Total expenses: {len(expenses)}")


def display_category_summary():
    """Display spending breakdown by category."""
    display_header("SPENDING BY CATEGORY")

    if not expenses:
        print("  No expenses recorded yet.")
        return

    summary = get_category_summary()
    total = get_total()

    # Sort by amount spent (highest first)
    sorted_categories = sorted(summary.items(), key=lambda x: x[1], reverse=True)

    print(f"  {'Category':<16} {'Amount':>10}  {'% of Total':>10}  {'Bar'}")
    print("  " + "-" * 53)

    for category, amount in sorted_categories:
        percentage = (amount / total) * 100
        bar_length = int(percentage / 5)    # each block = 5%
        bar = "█" * bar_length
        print(f"  {category:<16} Rs.{amount:>7,.0f}  {percentage:>9.1f}%  {bar}")

    print("  " + "-" * 53)
    print(f"  {'TOTAL':<16} Rs.{total:>7,.0f}  {'100.0%':>10}")


def display_statistics():
    """Display key statistics about expenses."""
    display_header("EXPENSE STATISTICS")

    if not expenses:
        print("  No expenses recorded yet.")
        return

    total = get_total()
    average = get_average()
    highest = get_highest_expense()
    lowest = get_lowest_expense()
    budget_used = (total / monthly_budget) * 100
    remaining = monthly_budget - total

    print(f"  Total Expenses:    Rs. {total:>10,.0f}")
    print(f"  Average Expense:   Rs. {average:>10,.0f}")
    print(f"  Highest Expense:   Rs. {highest['amount']:>10,.0f}  ({highest['name']})")
    print(f"  Lowest Expense:    Rs. {lowest['amount']:>10,.0f}  ({lowest['name']})")
    print(f"  Number of Items:   {len(expenses)}")
    print()
    print(f"  Monthly Budget:    Rs. {monthly_budget:>10,.0f}")
    print(f"  Amount Used:       Rs. {total:>10,.0f}  ({budget_used:.1f}%)")
    print(f"  Remaining:         Rs. {remaining:>10,.0f}")

    # Budget status bar
    used_blocks = int(budget_used / 5)
    used_blocks = min(used_blocks, 20)    # cap at 20 blocks
    empty_blocks = 20 - used_blocks
    status_bar = "█" * used_blocks + "░" * empty_blocks

    print(f"\n  Budget: [{status_bar}] {budget_used:.1f}%")

    if budget_used >= 100:
        print("WARNING: You have exceeded your budget!")
    elif budget_used >= 80:
        print("CAUTION: You are close to your budget limit.")
    else:
        print("You are within your budget.")


# ─────────────────────────────────────────
# INPUT FUNCTIONS — Getting User Input
# ─────────────────────────────────────────

def get_valid_amount(prompt):
    """
    Get a valid positive number from the user.

    Args:
        prompt (str): Message to display to the user.

    Returns:
        float: A valid positive amount.
    """
    while True:
        try:
            amount = float(input(prompt))
            if amount <= 0:
                print("  Amount must be greater than zero.")
                continue
            return amount
        except ValueError:
            print("  Please enter a valid number.")


def get_valid_category():
    """
    Display category menu and get a valid category choice.

    Returns:
        str: The selected category name.
    """
    print("\n  Categories:")
    for i, cat in enumerate(CATEGORIES, start=1):
        print(f"    {i}. {cat}")

    while True:
        try:
            choice = int(input("  Select category (number): "))
            if 1 <= choice <= len(CATEGORIES):
                return CATEGORIES[choice - 1]
            print(f"  Please enter a number between 1 and {len(CATEGORIES)}.")
        except ValueError:
            print("  Please enter a valid number.")


def handle_add_expense():
    """Handle the add expense user flow."""
    display_header("ADD NEW EXPENSE")

    name = input("  Expense name: ").strip()
    if not name:
        print("  Name cannot be empty.")
        return

    amount = get_valid_amount("  Amount (Rs.): ")
    category = get_valid_category()
    note = input("  Note (optional, press Enter to skip): ").strip()

    expense = add_expense(name, amount, category, note)
    print(f"\n Added: {expense['name']} — Rs. {expense['amount']:,.0f} ({expense['category']})")


def handle_delete_expense():
    """Handle the delete expense user flow."""
    display_header("DELETE EXPENSE")

    if not expenses:
        print("  No expenses to delete.")
        return

    display_all_expenses()

    try:
        expense_id = int(input("\n  Enter expense ID to delete: "))
        found = delete_expense(expense_id)
        if not found:
            print(f"  No expense found with ID {expense_id}.")
    except ValueError:
        print("  Please enter a valid ID number.")


def handle_search():
    """Handle the search expense user flow."""
    display_header("SEARCH EXPENSES")

    keyword = input("  Enter search term: ").strip()
    if not keyword:
        print("  Search term cannot be empty.")
        return

    results = search_expenses(keyword)

    if results:
        print(f"\n  Found {len(results)} result(s) for '{keyword}':")
        print(f"  {'ID':<4} {'Name':<20} {'Amount':>12}  {'Category':<14}")
        print("  " + "-" * 53)
        for expense in results:
            display_expense_row(expense)
    else:
        print(f"  No expenses found matching '{keyword}'.")


def handle_category_filter():
    """Handle filtering by category."""
    display_header("FILTER BY CATEGORY")

    category = get_valid_category()
    results = get_by_category(category)

    if results:
        category_total = get_total(results)
        print(f"\n  {category} expenses ({len(results)} items):")
        print(f"  {'ID':<4} {'Name':<20} {'Amount':>12}")
        print("  " + "-" * 38)
        for expense in results:
            print(f"  {expense['id']:<4} {expense['name']:<20} Rs.{expense['amount']:>7,.0f}")
        print("  " + "-" * 38)
        print(f"  {'Category Total':<24} Rs.{category_total:>7,.0f}")
    else:
        print(f"  No expenses found in '{category}' category.")


def handle_set_budget():
    """Handle updating the monthly budget."""
    global monthly_budget
    display_header("SET MONTHLY BUDGET")

    print(f"  Current budget: Rs. {monthly_budget:,.0f}")
    new_budget = get_valid_amount("  Enter new monthly budget (Rs.): ")
    monthly_budget = new_budget
    print(f" Budget updated to Rs. {monthly_budget:,.0f}")


def load_sample_data():
    """Load sample expenses so the tracker has data to show."""
    sample_expenses = [
        ("Morning Chai", 50, "Food", "Daily chai at office"),
        ("Uber to Office", 350, "Transport", "Monday"),
        ("Grocery Shopping", 2800, "Food", "Weekly groceries"),
        ("Internet Bill", 2500, "Bills", "Monthly DSL"),
        ("Python Course", 5000, "Education", "Udemy course"),
        ("Dinner with Family", 3500, "Food", "Weekend dinner"),
        ("Mobile Top-up", 500, "Bills", ""),
        ("Gym Membership", 2000, "Health", "Monthly fee"),
        ("Petrol", 4000, "Transport", "Full tank"),
        ("Books", 1200, "Education", "Programming books"),
    ]
    for name, amount, category, note in sample_expenses:
        add_expense(name, amount, category, note)


# ─────────────────────────────────────────
# MAIN FUNCTION — Program Entry Point
# ─────────────────────────────────────────

def main():
    """Main function — runs the expense tracker application."""

    # Load sample data so there is something to see immediately
    load_sample_data()

    print("\n" + "=" * 55)
    print("       PERSONAL EXPENSE TRACKER")
    print("       180 Days Full Stack AI — Day 05")
    print("=" * 55)
    print("  Sample data loaded. 10 expenses ready to explore.")

    while True:
        print("\n" + "─" * 55)
        print("  MENU")
        print("─" * 55)
        print("  1. View all expenses")
        print("  2. Add new expense")
        print("  3. Delete expense")
        print("  4. View by category")
        print("  5. Search expenses")
        print("  6. Category summary")
        print("  7. Statistics & budget")
        print("  8. Set monthly budget")
        print("  9. Exit")
        print("─" * 55)

        choice = input("  Choose option (1-9): ").strip()

        if choice == "1":
            display_all_expenses()
        elif choice == "2":
            handle_add_expense()
        elif choice == "3":
            handle_delete_expense()
        elif choice == "4":
            handle_category_filter()
        elif choice == "5":
            handle_search()
        elif choice == "6":
            display_category_summary()
        elif choice == "7":
            display_statistics()
        elif choice == "8":
            handle_set_budget()
        elif choice == "9":
            print("\n  Thank you for using Expense Tracker!")
            print("=" * 55 + "\n")
            break
        else:
            print("  Invalid option. Please choose between 1 and 9.")


if __name__ == "__main__":
    main()