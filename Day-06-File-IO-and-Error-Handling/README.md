# Day 06 — File I/O & Error Handling

> **Phase 1 — Foundations** | Week 1 | Day 6 of 180

---

## 📌 What I Learned Today

- Reading and writing text files with open()
- File modes: r, w, a, r+
- Context managers — the with statement (automatic file closing)
- CSV files — reading and writing tabular data with csv module
- JSON files — the most important data format in modern development
- json.dump() and json.load() — reading and writing JSON files
- json.dumps() and json.loads() — converting between Python and JSON strings
- try/except/else/finally — the complete error handling structure
- Common exceptions: ValueError, FileNotFoundError, KeyError, TypeError
- Raising exceptions with raise
- Custom exceptions — inheriting from Exception class
- File path handling with pathlib.Path
- Data validation functions that raise meaningful errors

## 🔨 Project Built

**Persistent Expense Tracker** — Upgraded version of Day 5 project:

- All data saved to expenses.json automatically after every change
- Loads previous session data on startup
- Automatic backup before every save (expenses_backup.json)
- Corrupted file recovery — tries backup if main file is unreadable
- Export all expenses to CSV file
- Complete input validation with custom exceptions
- Every file operation wrapped in try/except with helpful error messages
- Budget and spending summary in the menu bar
- Date and time recorded for every expense

## 🚀 How to Run

```bash
cd Day-06-File-IO-and-Error-Handling
python main.py
```

Data persists between runs — stored in expenses.json (gitignored).

## 🧠 Key Concepts

| Concept         | Syntax                     | Purpose                |
| --------------- | -------------------------- | ---------------------- |
| Write file      | `open("f.txt", "w")`       | Create or overwrite    |
| Append file     | `open("f.txt", "a")`       | Add to existing        |
| Read file       | `open("f.txt", "r")`       | Read existing          |
| Context manager | `with open() as f:`        | Auto-close file        |
| Save JSON       | `json.dump(data, file)`    | Python → JSON file     |
| Load JSON       | `json.load(file)`          | JSON file → Python     |
| Handle error    | `try/except`               | Catch exceptions       |
| Custom error    | `class MyError(Exception)` | Domain-specific errors |
| File exists     | `Path("f").exists()`       | Check before opening   |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
