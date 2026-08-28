# Day 44 — Database Optimization & Query Performance

> **Phase 5 — System Design & Architecture** | Week 8 | Day 44 of 180

---

## 📌 What I Learned Today

- Query execution flow: PARSE → PLAN → EXECUTE → RETURN
- Query planner uses statistics (ANALYZE) to choose execution strategy
- EXPLAIN ANALYZE: cost estimation + actual execution time
- Seq Scan: reads all rows, O(N) — fine for small tables, terrible for large
- Index Scan: follows index to matching rows, O(log N + k)
- Index-Only Scan: all data in index, never touches table — fastest
- B-tree index: default, good for equality, range, ORDER BY, LIKE prefix
- Composite index: multi-column, order matters, equality cols before range
- Partial index: indexes only a subset of rows (WHERE clause at create time)
- Covering index: INCLUDE extra columns — enables Index-Only Scans
- Index selection rule: put most selective / equality columns first
- Index cost: write overhead (INSERT/UPDATE/DELETE update all indexes)
- Max indexes per table: 5-6 in most cases
- N+1 problem: query loop → N extra queries per result row
- N+1 fix: joinedload (SQLAlchemy) or batch SELECT WHERE id IN (...)
- OFFSET pagination: scans and discards offset rows — O(N) at depth
- Keyset pagination: WHERE created_at < cursor — always O(page_size)
- EXISTS vs COUNT(*): EXISTS stops at first match, COUNT scans all
- SELECT * vs SELECT cols: only fetch needed columns → less I/O
- Functions on indexed columns break index usage (use range instead)
- Batch INSERT: N rows in 1 statement vs N statements
- pg_stat_statements: tracks slow queries, call counts, total time
- log_min_duration_statement: log queries slower than threshold
- Connection pool: pool_size + max_overflow connections per app instance
- PgBouncer: reduces actual PostgreSQL connections at scale
- pool_pre_ping=True: verify connection alive before using
- ANALYZE: updates planner statistics → better plan choices

## 🔨 Project Built

**Query Profiler and Optimizer:**

**SimulatedDatabase** (database.py):
- 10,000 tasks, 100 users seeded with realistic distribution
- Sequential scan: ROWS_PER_MS throughput, realistic latency
- Index scan: direct lookup in hash map, INDEX_OVERHEAD_MS
- Composite index: multi-column hash lookup
- create_index() and create_composite_index() methods
- execute_with_join(): N+1 vs batch vs JOIN comparison
- Query log with slow query detection

**QueryProfiler** (profiler.py):
- Records every query execution plan
- top_slow_queries(): slowest N queries with recommendations
- summary_by_query(): aggregate stats per query name
- index_recommendations(): generates CREATE INDEX statements
- overall_stats(): p50/p95/p99 latency

**FastAPI Endpoints:**
- GET /tasks: demonstrates Seq Scan → Index Scan transition
- POST /indexes/apply: applies 6 indexes (4 single + 2 composite)
- POST /indexes/drop: back to baseline
- POST /benchmark: before/after comparison
- GET /profiler/report: full analysis
- GET /demo/n-plus-1: N+1 vs batch (configurable n_tasks)
- GET /demo/pagination: OFFSET vs keyset at configurable depth

## 🚀 How to Run

```bash
cd Day-44-DB-Optimization
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload

# See seq scan (slow)
curl "http://localhost:8000/tasks?status=pending"

# Apply indexes
curl -X POST http://localhost:8000/indexes/apply

# See index scan (fast)
curl "http://localhost:8000/tasks?status=pending"

# Full benchmark
curl -X POST http://localhost:8000/benchmark
```

## 🧠 Index Decision Guide

| Query Pattern | Best Index |
|--------------|-----------|
| WHERE col = ? | Single B-tree |
| WHERE col1 = ? AND col2 = ? | Composite (col1, col2) |
| WHERE col = ? ORDER BY other | Composite (col, other DESC) |
| WHERE col = 'fixed_value' | Partial index |
| SELECT few cols WHERE col = ? | Covering index with INCLUDE |
| JOIN ON other_id | Index on foreign key column |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)