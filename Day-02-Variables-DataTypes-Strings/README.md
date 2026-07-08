# Day 02 — Variables, Data Types, Operators & String Methods

> **Phase 1 — Foundations** | Week 1 | Day 2 of 180

---

## 📌 What I Learned Today

- Variables and how Python stores data in memory
- The 4 core data types: str, int, float, bool
- Type conversion: int(), float(), str()
- Arithmetic operators: +, -, \*, /, //, %, \*\*
- Comparison operators: ==, !=, >, <, >=, <=
- Logical operators: and, or, not
- 15+ string methods: upper, lower, strip, replace, split, join, find, count
- Advanced f-string formatting: decimal places, comma separators, alignment

## 🔨 Project Built

**Mad Libs Generator** — An interactive word game that:

- Collects 7 words from the user (name, adjective, noun, verb, place, animal, food)
- Randomly picks from 2 different story templates
- Inserts the user's words into a funny story
- Shows word statistics using string methods
- Lets the user play again with different words

## 🚀 How to Run

```bash
cd Day-02-Variables-DataTypes-Strings
python main.py
```

## 🧠 Key Concepts

| Concept      | Example                  | Result                 |
| ------------ | ------------------------ | ---------------------- |
| String       | `"Hello"`                | Text data              |
| Integer      | `22`                     | Whole number           |
| Float        | `5.9`                    | Decimal number         |
| Boolean      | `True`                   | True or False          |
| `int()`      | `int("22")`              | Converts string to int |
| `str()`      | `str(22)`                | Converts int to string |
| `.upper()`   | `"hello".upper()`        | `"HELLO"`              |
| `.strip()`   | `" hi ".strip()`         | `"hi"`                 |
| `.replace()` | `"cat".replace("c","b")` | `"bat"`                |
| `.split()`   | `"a b c".split(" ")`     | `["a","b","c"]`        |
| f-string     | `f"Hi {name}"`           | `"Hi Humayun"`         |
| Modulo `%`   | `7 % 2`                  | `1`                    |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
