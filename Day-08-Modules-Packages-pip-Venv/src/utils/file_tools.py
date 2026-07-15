# ============================================================
# src/utils/file_tools.py
# File utility functions
# ============================================================

import json
import csv
import os
from pathlib import Path


def read_json(filepath):
    """
    Safely read a JSON file.

    Args:
        filepath (str or Path): Path to JSON file.

    Returns:
        dict/list: Parsed JSON data, or None if error.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON parse error in {filepath.name}: {e}")
        return None
    except Exception as e:
        print(f"Error reading {filepath.name}: {e}")
        return None


def write_json(filepath, data, indent=4):
    """
    Write data to a JSON file.

    Args:
        filepath (str or Path): Path to write to.
        data: Data to serialize.
        indent (int): JSON indentation.

    Returns:
        bool: True if successful.
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error writing {filepath.name}: {e}")
        return False


def read_csv(filepath):
    """
    Read a CSV file and return list of dictionaries.

    Returns:
        list: List of row dictionaries.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return []

    try:
        with open(filepath, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        print(f"Error reading CSV {filepath.name}: {e}")
        return []


def write_csv(filepath, data, fieldnames=None):
    """
    Write list of dictionaries to CSV file.

    Args:
        filepath (str or Path): Path to write to.
        data (list): List of dictionaries.
        fieldnames (list): Column names. Inferred from data if None.

    Returns:
        bool: True if successful.
    """
    if not data:
        return False

    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    try:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        return True
    except Exception as e:
        print(f"Error writing CSV {filepath.name}: {e}")
        return False


def get_file_size(filepath):
    """Return file size in human-readable format."""
    size = os.path.getsize(filepath)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def list_files(directory, extension=None):
    """
    List files in a directory.

    Args:
        directory (str or Path): Directory to list.
        extension (str): Filter by extension e.g. ".py". None for all.

    Returns:
        list: List of Path objects.
    """
    directory = Path(directory)
    if not directory.exists():
        return []

    if extension:
        return list(directory.glob(f"*{extension}"))
    return [f for f in directory.iterdir() if f.is_file()]


if __name__ == "__main__":
    print("File Tools Module")
    print("-" * 30)

    # Test write and read JSON
    test_data = {"name": "Humayun", "day": 8, "topic": "Modules"}
    write_json("test_output.json", test_data)
    loaded = read_json("test_output.json")
    print(f"JSON round-trip: {loaded}")

    # Test write and read CSV
    rows = [
        {"name": "Ali", "score": 85},
        {"name": "Sara", "score": 92}
    ]
    write_csv("test_output.csv", rows)
    read_rows = read_csv("test_output.csv")
    print(f"CSV round-trip: {read_rows}")