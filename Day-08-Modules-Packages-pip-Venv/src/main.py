# ============================================================
# src/main.py
# Main entry point for the Python Toolkit
# Day 08 - 180 Days Full Stack AI Engineer Roadmap
# ============================================================

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import APP_NAME, VERSION, AUTHOR, DEBUG, DATA_DIR
from src.utils import (
    is_palindrome, generate_password, caesar_cipher,
    word_frequency, extract_emails, truncate,
    get_current_datetime, get_current_date, get_age,
    format_relative, days_between,
    read_json, write_json, read_csv, write_csv
)


def display_header():
    """Display application header."""
    print("\n" + "=" * 58)
    print(f"  {APP_NAME} v{VERSION}")
    print(f"  Built by: {AUTHOR}")
    print(f"  Date: {get_current_datetime()}")
    if DEBUG:
        print(f"  [DEBUG MODE ON]")
    print("=" * 58)


def demo_string_tools():
    """Demonstrate string utility functions."""
    print("\n--- STRING TOOLS DEMO ---")

    # Palindrome checker
    words = ["racecar", "python", "madam", "hello", "level", "kayak"]
    print("\nPalindrome Checker:")
    for word in words:
        result = "✅" if is_palindrome(word) else "❌"
        print(f"  {result} {word}")

    # Password generator
    print("\nGenerated Passwords:")
    for i in range(3):
        pwd = generate_password(length=14, use_symbols=True)
        print(f"  {i+1}. {pwd}")

    # Caesar cipher
    message = "Hello World from Python"
    encoded = caesar_cipher(message, shift=5)
    decoded = caesar_cipher(encoded, shift=5, decode=True)
    print(f"\nCaesar Cipher:")
    print(f"  Original: {message}")
    print(f"  Encoded:  {encoded}")
    print(f"  Decoded:  {decoded}")

    # Word frequency
    text = "python is great python is powerful and python is fun to learn"
    freq = word_frequency(text)
    top_3 = list(freq.items())[:3]
    print(f"\nTop 3 words in text:")
    for word, count in top_3:
        print(f"  '{word}': {count} times")

    # Email extraction
    sample = "Reach us at info@company.com or support@help.org for queries"
    emails = extract_emails(sample)
    print(f"\nExtracted emails: {emails}")

    # Truncate
    long_text = "This is a very long description that needs to be shortened"
    print(f"\nTruncated: {truncate(long_text, 30)}")


def demo_date_tools():
    """Demonstrate date utility functions."""
    print("\n--- DATE TOOLS DEMO ---")

    print(f"\nCurrent date: {get_current_date()}")
    print(f"Current datetime: {get_current_datetime()}")

    # Age calculator
    birth_dates = [
        ("2002-06-15", "Humayun"),
        ("1990-03-22", "Ali"),
        ("1985-11-08", "Sara"),
    ]
    print("\nAge Calculator:")
    for dob, name in birth_dates:
        age = get_age(dob)
        print(f"  {name} (born {dob}): {age} years old")

    # Days between dates
    pairs = [
        ("2025-01-01", "2025-12-31"),
        ("2025-06-15", "2025-08-15"),
    ]
    print("\nDays Between Dates:")
    for d1, d2 in pairs:
        diff = days_between(d1, d2)
        print(f"  {d1} → {d2}: {diff} days")

    # Relative dates
    past_dates = ["2025-05-01", "2025-05-20", "2025-04-01", "2024-01-01"]
    print("\nRelative Dates:")
    for d in past_dates:
        print(f"  {d}: {format_relative(d)}")


def demo_file_tools():
    """Demonstrate file utility functions."""
    print("\n--- FILE TOOLS DEMO ---")

    # JSON round-trip
    data = {
        "toolkit": APP_NAME,
        "version": VERSION,
        "author": AUTHOR,
        "features": ["string tools", "date tools", "file tools"],
        "day": 8
    }

    json_path = DATA_DIR / "toolkit_info.json"
    success = write_json(json_path, data)
    print(f"\nJSON write: {'✅ Success' if success else '❌ Failed'}")

    loaded = read_json(json_path)
    if loaded:
        print(f"JSON read: ✅ Loaded '{loaded['toolkit']}' v{loaded['version']}")
        print(f"  Features: {', '.join(loaded['features'])}")

    # CSV round-trip
    students = [
        {"name": "Humayun", "score": 95, "grade": "A"},
        {"name": "Ali", "score": 82, "grade": "B"},
        {"name": "Sara", "score": 98, "grade": "A+"},
        {"name": "Omar", "score": 71, "grade": "C"},
    ]

    csv_path = DATA_DIR / "students.csv"
    success = write_csv(csv_path, students)
    print(f"\nCSV write: {'✅ Success' if success else '❌ Failed'}")

    loaded_students = read_csv(csv_path)
    print(f"CSV read: ✅ Loaded {len(loaded_students)} students")
    for student in loaded_students:
        print(f"  {student['name']}: {student['score']} ({student['grade']})")


def main():
    """Main function — runs the toolkit demo."""
    display_header()

    print("\nThis toolkit demonstrates proper Python project structure:")
    print("  - Multiple modules organized in packages")
    print("  - Environment variables with python-dotenv")
    print("  - Virtual environment with requirements.txt")
    print("  - Clean imports between modules")

    while True:
        print("\n" + "─" * 58)
        print("  TOOLKIT MENU")
        print("─" * 58)
        print("  1. Demo string tools")
        print("  2. Demo date tools")
        print("  3. Demo file tools")
        print("  4. Run all demos")
        print("  5. Exit")
        print("─" * 58)

        choice = input("  Choose option (1-5): ").strip()

        if choice == "1":
            demo_string_tools()
        elif choice == "2":
            demo_date_tools()
        elif choice == "3":
            demo_file_tools()
        elif choice == "4":
            demo_string_tools()
            demo_date_tools()
            demo_file_tools()
        elif choice == "5":
            print("\n  See you on Day 9! 💪")
            print("=" * 58 + "\n")
            break
        else:
            print("  ❌ Invalid option. Choose between 1 and 5.")


if __name__ == "__main__":
    main()