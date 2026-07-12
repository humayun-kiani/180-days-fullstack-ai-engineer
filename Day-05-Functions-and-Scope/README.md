# Day 05 — Functions, Scope & Code Reusability

> **Phase 1 — Foundations** | Week 1 | Day 5 of 180

---

## 📌 What I Learned Today

- Defining and calling functions with def
- Parameters vs arguments — the difference explained
- Return values — sending data back from functions
- Returning multiple values as tuples
- Default arguments — making parameters optional
- Keyword arguments — naming arguments on call
- \*args — accepting any number of positional arguments (tuple)
- \*\*kwargs — accepting any number of keyword arguments (dict)
- Local vs global scope — where variables live and die
- The LEGB rule — how Python finds variables
- The global keyword — modifying globals from inside functions
- Docstrings — documenting functions professionally
- Function composition — functions calling other functions

## 🔨 Project Built

**Personal Expense Tracker** — A full-featured CLI expense manager:

- Add expenses with name, amount, category, and optional note
- View all expenses in a formatted table
- Delete expenses by ID
- Filter expenses by category
- Search expenses by keyword
- Category summary with percentage breakdown and visual bars
- Statistics: total, average, highest, lowest expense
- Monthly budget tracker with visual progress bar
- Budget warning system (caution at 80%, alert at 100%)
- Sample data pre-loaded for immediate exploration
- Every feature is its own clean, documented function

## 🚀 How to Run

```bash
cd Day-05-Functions-and-Scope
python main.py
```

## 🧠 Key Concepts

| Concept         | Syntax              | Purpose                          |
| --------------- | ------------------- | -------------------------------- |
| Define function | `def name(params):` | Create reusable block            |
| Call function   | `name(args)`        | Execute the function             |
| Return value    | `return value`      | Send data back                   |
| Default param   | `def f(x, y=10):`   | Optional parameter               |
| Keyword arg     | `f(y=5, x=2)`       | Named argument                   |
| \*args          | `def f(*args):`     | Variable positional args         |
| \*\*kwargs      | `def f(**kwargs):`  | Variable keyword args            |
| Local scope     | Inside function     | Variable dies when function ends |
| Global scope    | Outside functions   | Available everywhere             |
| Docstring       | `"""Description"""` | Professional documentation       |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
