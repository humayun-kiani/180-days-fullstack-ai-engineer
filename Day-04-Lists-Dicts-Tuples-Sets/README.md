# Day 04 — Lists, Dictionaries, Tuples & Sets

> **Phase 1 — Foundations** | Week 1 | Day 4 of 180

---

## 📌 What I Learned Today

- Lists — ordered, changeable collections with indexing and slicing
- List methods: append, insert, remove, pop, sort, reverse, count, index
- Dictionaries — key-value pairs for structured data storage
- Dictionary methods: get, update, pop, keys, values, items
- Tuples — immutable ordered collections for fixed data
- Tuple unpacking — assign multiple variables in one line
- Sets — unique value collections with no duplicates
- Set operations: union, intersection, difference, symmetric difference
- When to use each data structure and why
- zip() to pair two lists together
- List comprehensions — creating lists in one line

## 🔨 Project Built

**Student Grade Calculator** — A complete grade management system:

- Stores 5 students with their grades across 5 subjects
- Calculates average, letter grade, and GPA per student
- Finds best and weakest subject per student using zip()
- Visual grade bars using string multiplication
- Grade distribution using a dictionary counter
- Unique grade letters using a set
- Filter students by grade letter
- Add new students interactively
- Full menu-driven interface

## 🚀 How to Run

```bash
cd Day-04-Lists-Dicts-Tuples-Sets
python main.py
```

## 🧠 Key Concepts

| Concept         | Example            | Use Case           |
| --------------- | ------------------ | ------------------ |
| List            | `[1, 2, 3]`        | Ordered collection |
| Dict            | `{"key": "value"}` | Key-value lookup   |
| Tuple           | `(x, y)`           | Fixed data pairs   |
| Set             | `{1, 2, 3}`        | Unique values      |
| `list[0]`       | Index access       | Get first item     |
| `list[1:4]`     | Slicing            | Get sublist        |
| `dict.get(key)` | Safe access        | No KeyError        |
| `set1 & set2`   | Intersection       | Common items       |
| `zip(a, b)`     | Pair two lists     | Parallel iteration |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
