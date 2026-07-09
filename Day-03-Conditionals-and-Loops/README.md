# Day 03 — Conditionals, Loops & Program Flow

> **Phase 1 — Foundations** | Week 1 | Day 3 of 180

---

## 📌 What I Learned Today

- if / elif / else — making decisions in code
- Truthy and Falsy values in Python
- The ternary operator for one-line conditions
- for loops — iterating over sequences and ranges
- while loops — repeating until a condition changes
- break — exit a loop early
- continue — skip current iteration
- pass — placeholder for empty blocks
- range() — generating number sequences
- enumerate() — looping with index and value
- Nested loops — loops inside loops

## 🔨 Project Built

**Number Guessing Game** — A complete CLI game that:

- Generates a random secret number between 1 and 100
- Gives the player 7 attempts to guess it
- Provides temperature-based hints (ice cold, lukewarm, hot, very close)
- Validates all user input (handles non-numbers, out-of-range values)
- Tracks best score across multiple games
- Shows win rate, average attempts, and performance rating
- Displays complete guess history at the end of each round

## 🚀 How to Run

```bash
cd Day-03-Conditionals-and-Loops
python main.py
```

## 🧠 Key Concepts

| Concept                   | Purpose                                 |
| ------------------------- | --------------------------------------- |
| `if / elif / else`        | Make decisions based on conditions      |
| `for i in range(n)`       | Repeat exactly n times                  |
| `while condition:`        | Repeat until condition is False         |
| `break`                   | Exit loop immediately                   |
| `continue`                | Skip to next iteration                  |
| `random.randint(1, 100)`  | Generate random integer in range        |
| `abs(a - b)`              | Absolute difference between two numbers |
| `try / except ValueError` | Handle invalid input gracefully         |

## 💡 Key Insight

The binary search strategy is the optimal way to play:
always guess the middle of the remaining range.
This guarantees finding any number in 7 or fewer guesses
(since 2^7 = 128 > 100). This is a real algorithm called
Binary Search — used in databases and search engines daily.

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
