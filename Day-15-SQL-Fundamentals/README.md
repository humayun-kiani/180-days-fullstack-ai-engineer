# Day 15 — SQL Fundamentals: Relational Databases, Queries & Indexes

> **Phase 1 — Foundations** | Week 3 | Day 15 of 180

---

## 📌 What I Learned Today

- What relational databases are and why they exist
- Tables, rows, columns, and SQL data types
- Primary keys and foreign keys — relationships between tables
- SQLite — zero-config database built into Python
- sqlite3 module — connecting, querying, row_factory
- CREATE TABLE with constraints: NOT NULL, UNIQUE, CHECK, DEFAULT
- INSERT — single and multi-row inserts
- SELECT — basic, with aliases, DISTINCT, LIMIT, OFFSET
- WHERE — filtering with AND, OR, IN, BETWEEN, LIKE, IS NULL
- ORDER BY — ascending and descending, multiple columns
- Aggregate functions — COUNT, SUM, AVG, MIN, MAX
- GROUP BY — grouping rows for aggregation
- HAVING — filtering groups (like WHERE but after GROUP BY)
- UPDATE and DELETE — modifying and removing data
- INNER JOIN — rows matching in both tables
- LEFT JOIN — all left rows with matching right (NULL if none)
- Self JOIN — joining a table to itself (manager hierarchy)
- Subqueries — queries inside queries
- CASE WHEN — conditional logic inside SQL
- COALESCE — handle NULL values with defaults
- GROUP_CONCAT — concatenate grouped values
- Indexes — how they work, when to create them
- EXPLAIN QUERY PLAN — analyze query performance
- Transactions — BEGIN, COMMIT, ROLLBACK

## 🔨 Project Built

**Student Analytics Database** — Full university analytics system:

- 5-table schema: departments, students, courses, enrollments, attendance
- 50 students across 5 departments with realistic fake data (Faker)
- 7 database indexes for query performance
- 15 analytical SQL queries demonstrating all major concepts:
  1. Overview statistics (COUNT, AVG across tables)
  2. Department comparison (JOIN + GROUP BY + aggregates)
  3. Top 10 students leaderboard (JOIN + ORDER BY + LIMIT)
  4. GPA distribution with CASE WHEN bucketing
  5. Hardest courses by average marks
  6. City-wise distribution with percentages
  7. Enrollment year analysis
  8. Students above average GPA (subquery)
  9. Attendance risk analysis (attendance < 75%)
  10. Grade distribution per course (CASE WHEN pivot)
  11. Perfect attendance students
  12. Department ranking (correlated subquery)
  13. At-risk students failing 2+ courses (GROUP_CONCAT)
  14. Credit hours summary per student
  15. Attendance vs performance correlation
- Interactive SQL query mode — type any SQL and see results
- Export full report to JSON
- Colored terminal output with bar charts

## 🚀 How to Run

```bash
cd Day-15-SQL-Fundamentals
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

## 🧠 Key SQL Reference

| Statement                    | Purpose                   |
| ---------------------------- | ------------------------- |
| `SELECT col FROM tbl`        | Read data                 |
| `WHERE col = val`            | Filter rows               |
| `GROUP BY col`               | Group for aggregation     |
| `HAVING COUNT(*) > 5`        | Filter groups             |
| `ORDER BY col DESC`          | Sort results              |
| `JOIN t2 ON t1.id = t2.fk`   | Combine tables            |
| `LEFT JOIN`                  | Include non-matching rows |
| `COUNT(*) / SUM() / AVG()`   | Aggregates                |
| `CASE WHEN ... THEN ... END` | Conditional logic         |
| `CREATE INDEX ON tbl(col)`   | Speed up queries          |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
