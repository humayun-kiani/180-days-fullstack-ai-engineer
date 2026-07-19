# Day 11 — Regular Expressions & CLI Tools with argparse

> **Phase 1 — Foundations** | Week 2 | Day 11 of 180

---

## 📌 What I Learned Today

- What regular expressions are and why they matter
- Regex syntax: literal chars, metacharacters, character classes
- Shorthand classes: \d, \w, \s and their uppercase negations
- Quantifiers: \*, +, ?, {n}, {n,m} and non-greedy variants
- Anchors: ^ (start), $ (end), \b (word boundary)
- Groups () for capturing, named groups (?P<name>...)
- Alternation | for OR matching
- re.search(), re.match(), re.findall(), re.finditer()
- re.sub() for find-and-replace including replacement functions
- re.split() for splitting on patterns
- re.compile() for reusing patterns efficiently
- Flags: IGNORECASE, MULTILINE, DOTALL, VERBOSE
- Common patterns: email, IP, phone, URL, date, log level
- argparse: positional args, optional args, flags, types, choices
- argparse: subcommands (like git commit, git push)
- argparse: --help auto-generation
- Building professional CLI tools with argparse

## 🔨 Project Built

**Log File Analyzer CLI Tool** — A complete professional CLI tool:

- `generate` command: creates realistic 500-line log files
- `analyze` command: parses and displays log entries with filters
  - --level: filter by DEBUG/INFO/WARNING/ERROR/CRITICAL
  - --since / --until: filter by date range
  - --source: filter by source file (regex)
  - --pattern: filter by message content (regex)
  - --limit: control output size
  - --output: table, json, or csv format
- `search` command: regex search with optional context lines
- `stats` command: comprehensive statistical analysis
  - Level distribution with visual bars
  - Top source files
  - IP address frequency
  - User activity tracking
  - HTTP status code counts
  - Hourly activity chart
- All regex compiled for efficiency
- Named groups for clean data extraction
- Export to JSON and CSV

## 🚀 How to Run

```bash
cd Day-11-Regex-and-CLI-Tools
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Generate sample data first
python src/main.py generate logs/server.log --lines 500

# Then analyze
python src/main.py analyze logs/server.log --level ERROR
python src/main.py search "database" logs/server.log --context 2
python src/main.py stats logs/server.log
```

## 🧠 Key Concepts

| Regex           | Meaning                    |
| --------------- | -------------------------- |
| `.`             | Any char except newline    |
| `\d`            | Any digit [0-9]            |
| `\w`            | Any word char [a-zA-Z0-9_] |
| `\s`            | Any whitespace             |
| `*`             | Zero or more               |
| `+`             | One or more                |
| `?`             | Zero or one                |
| `{n,m}`         | Between n and m            |
| `^`             | Start of string            |
| `$`             | End of string              |
| `(...)`         | Capture group              |
| `(?P<name>...)` | Named group                |
| `[abc]`         | Match a, b, or c           |
| `\|`            | OR                         |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
