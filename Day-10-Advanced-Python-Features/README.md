# Day 10 — Advanced Python: Comprehensions, Generators, Decorators & Functional Programming

> **Phase 1 — Foundations** | Week 2 | Day 10 of 180

---

## 📌 What I Learned Today

- List comprehensions — advanced patterns, nested, with conditions
- Dictionary and set comprehensions
- Generator expressions — memory-efficient lazy evaluation
- Generator functions with yield keyword
- The memory difference: list stores all values, generator produces one at a time
- itertools — count, cycle, chain, islice, groupby, combinations, product
- functools — reduce, lru_cache (memoization), partial
- Lambda functions — when to use and when NOT to use them
- map() — apply function to every item
- filter() — keep items where function returns True
- zip() and zip_longest() — pair up iterables
- Decorators — functions that wrap other functions
- @timer, @retry, @log_calls, @cache_result decorators
- Stacking multiple decorators
- functools.wraps — preserving wrapped function metadata
- Decorator factories — decorators that accept arguments

## 🔨 Project Built

**Data Pipeline Script** — A complete data processing pipeline:

- Fetches posts, users, and comments from JSONPlaceholder API
- @retry decorator: auto-retries on network failure (3 attempts)
- @timer decorator: measures execution time of each step
- @log_calls decorator: logs all function calls with timestamps
- Generator pipeline: clean → filter → enrich → count (lazy evaluation)
- itertools.groupby: groups posts by author
- functools.reduce: computes totals across all posts
- map() and filter(): transforms and filters data functionally
- zip(): pairs word counts with post titles for ranking
- Comprehensions: builds lookup dicts, filters, transforms
- Statistical analysis: averages, distributions, correlations
- Author leaderboard with rankings
- Saves results to timestamped JSON files

## 🚀 How to Run

```bash
cd Day-10-Advanced-Python-Features
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

## 🧠 Key Concepts

| Concept              | Syntax                           | Memory          |
| -------------------- | -------------------------------- | --------------- |
| List comprehension   | `[x for x in items]`             | Stores all      |
| Dict comprehension   | `{k: v for k,v in items}`        | Stores all      |
| Generator expression | `(x for x in items)`             | One at a time   |
| Generator function   | `yield value`                    | One at a time   |
| Decorator            | `@decorator_name`                | Wraps function  |
| lru_cache            | `@functools.lru_cache`           | Caches results  |
| reduce               | `functools.reduce(fn, iterable)` | Folds to single |
| partial              | `functools.partial(fn, arg)`     | Pre-fills arg   |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
