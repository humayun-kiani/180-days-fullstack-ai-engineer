# src/utils/__init__.py
# Makes utils a package and exposes key functions at package level

from .string_tools import (
    is_palindrome,
    generate_password,
    caesar_cipher,
    word_frequency,
    extract_emails,
    truncate
)

from .date_tools import (
    get_current_datetime,
    get_current_date,
    get_age,
    format_relative,
    days_between
)

from .file_tools import (
    read_json,
    write_json,
    read_csv,
    write_csv
)

__all__ = [
    # string tools
    "is_palindrome", "generate_password", "caesar_cipher",
    "word_frequency", "extract_emails", "truncate",
    # date tools
    "get_current_datetime", "get_current_date",
    "get_age", "format_relative", "days_between",
    # file tools
    "read_json", "write_json", "read_csv", "write_csv"
]