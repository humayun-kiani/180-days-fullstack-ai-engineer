# ============================================================
# src/utils/date_tools.py
# Date and time utility functions
# ============================================================

from datetime import datetime, date, timedelta


def get_current_datetime(fmt="%Y-%m-%d %H:%M:%S"):
    """Return current datetime as formatted string."""
    return datetime.now().strftime(fmt)


def get_current_date(fmt="%Y-%m-%d"):
    """Return current date as formatted string."""
    return date.today().strftime(fmt)


def days_between(date1_str, date2_str, fmt="%Y-%m-%d"):
    """
    Calculate days between two date strings.

    Args:
        date1_str (str): First date string.
        date2_str (str): Second date string.
        fmt (str): Date format string.

    Returns:
        int: Number of days between the dates.
    """
    d1 = datetime.strptime(date1_str, fmt).date()
    d2 = datetime.strptime(date2_str, fmt).date()
    return abs((d2 - d1).days)


def add_days(date_str, days, fmt="%Y-%m-%d"):
    """Add a number of days to a date string."""
    d = datetime.strptime(date_str, fmt).date()
    result = d + timedelta(days=days)
    return result.strftime(fmt)


def get_age(birth_date_str, fmt="%Y-%m-%d"):
    """
    Calculate age in years from birth date string.

    Returns:
        int: Age in years.
    """
    birth = datetime.strptime(birth_date_str, fmt).date()
    today = date.today()
    age = today.year - birth.year
    # Adjust if birthday has not occurred yet this year
    if (today.month, today.day) < (birth.month, birth.day):
        age -= 1
    return age


def is_weekend(date_str=None, fmt="%Y-%m-%d"):
    """Check if a date falls on a weekend."""
    if date_str:
        d = datetime.strptime(date_str, fmt).date()
    else:
        d = date.today()
    return d.weekday() >= 5    # 5=Saturday, 6=Sunday


def get_day_of_week(date_str=None, fmt="%Y-%m-%d"):
    """Get the day name of a date."""
    if date_str:
        d = datetime.strptime(date_str, fmt)
    else:
        d = datetime.now()
    return d.strftime("%A")


def format_relative(date_str, fmt="%Y-%m-%d"):
    """
    Return a human-readable relative time string.

    Returns things like: "Today", "Yesterday", "3 days ago", "2 weeks ago"
    """
    d = datetime.strptime(date_str, fmt).date()
    today = date.today()
    delta = (today - d).days

    if delta == 0:
        return "Today"
    elif delta == 1:
        return "Yesterday"
    elif delta < 0:
        return f"In {abs(delta)} days"
    elif delta < 7:
        return f"{delta} days ago"
    elif delta < 30:
        weeks = delta // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif delta < 365:
        months = delta // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = delta // 365
        return f"{years} year{'s' if years > 1 else ''} ago"


if __name__ == "__main__":
    print("Date Tools Module")
    print("-" * 30)
    print(f"Current datetime: {get_current_datetime()}")
    print(f"Days between 2025-01-01 and 2025-12-31: {days_between('2025-01-01', '2025-12-31')}")
    print(f"Age from 2002-06-15: {get_age('2002-06-15')}")
    print(f"Is today a weekend: {is_weekend()}")
    print(f"Today is: {get_day_of_week()}")
    print(f"30 days from today: {add_days(get_current_date(), 30)}")
    print(f"Relative: {format_relative('2025-05-01')}")