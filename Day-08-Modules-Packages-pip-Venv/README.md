# Day 08 — Modules, Packages, pip & Virtual Environments

> **Phase 1 — Foundations** | Week 2 | Day 8 of 180

---

## 📌 What I Learned Today

- What modules are and how Python's import system works
- Importing: import, from...import, aliases, packages
- Python standard library: os, sys, pathlib, collections, datetime, random, string
- Creating custom modules and packages with **init**.py
- pip — installing, upgrading, uninstalling packages
- Virtual environments — isolated Python environments per project
- requirements.txt — sharing and reproducing dependencies
- Environment variables with .env files and python-dotenv
- Professional Python project folder structure
- The if **name** == "**main**" pattern explained deeply

## 🔨 Project Built

**Python Toolkit** — A properly structured multi-module project:

- `src/config.py` — loads environment variables with python-dotenv
- `src/utils/string_tools.py` — palindrome checker, password generator,
  Caesar cipher, word frequency, email extractor
- `src/utils/date_tools.py` — age calculator, days between, relative dates
- `src/utils/file_tools.py` — JSON and CSV read/write utilities
- `src/utils/__init__.py` — exposes functions at package level
- `src/main.py` — imports from all modules, runs interactive demo
- Virtual environment with requirements.txt
- Environment variables via .env

## 🚀 How to Run

```bash
cd Day-08-Modules-Packages-pip-Venv

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # Mac/Linux
# venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run the application
python src/main.py
```

## 🧠 Key Concepts

| Concept                  | Purpose                       |
| ------------------------ | ----------------------------- |
| `import module`          | Import entire module          |
| `from pkg import fn`     | Import specific function      |
| `__init__.py`            | Makes folder a Python package |
| `pip install x`          | Install third party package   |
| `python -m venv venv`    | Create virtual environment    |
| `pip freeze > req.txt`   | Save dependencies             |
| `pip install -r req.txt` | Install from requirements     |
| `load_dotenv()`          | Load .env file variables      |
| `os.environ.get("KEY")`  | Read environment variable     |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
