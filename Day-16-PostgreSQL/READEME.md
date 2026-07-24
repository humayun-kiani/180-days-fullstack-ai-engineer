# Day 16 — PostgreSQL: Production Database, psql & Advanced Features

> **Phase 1 — Foundations** | Week 3 | Day 16 of 180

---

## 📌 What I Learned Today

- Why PostgreSQL over SQLite — scale, concurrency, features
- Installing PostgreSQL and using psql CLI
- Essential psql meta-commands: \l, \c, \dt, \d, \di, \x
- Creating databases, users, and granting privileges
- PostgreSQL-specific data types:
  - UUID with uuid_generate_v4()
  - JSONB — binary JSON with GIN indexing
  - TEXT[] — native arrays with ANY, @>, unnest()
  - ENUM — custom type constraints
  - TIMESTAMPTZ — timestamps with timezone
  - INET — validated IP addresses
  - NUMERIC(12,2) — exact decimal for money
- Advanced indexes: partial, composite, GIN, expression
- Views — saved queries used as virtual tables
- Materialized views — cached query results
- Stored functions in PL/pgSQL
- Triggers — automatic actions on table events
- Auto-updating search_vector with BEFORE INSERT trigger
- Full-text search: tsvector, tsquery, ts_rank, ts_headline
- Weight-based search: setweight() for title > excerpt > content
- Window functions: RANK, SUM OVER, AVG OVER, LAG, LEAD
- PARTITION BY in window functions
- Migration system — versioned SQL files applied in order
- COALESCE, NULLIF, FILTER clause on aggregates
- Array unnesting with unnest()
- GROUP_CONCAT equivalent: string_agg()

## 🔨 Project Built

**Blog Platform Database** — Production-quality PostgreSQL schema:

- 3 migration files with version tracking
- 8 tables: users, categories, posts, comments, post_likes,
  user_follows, page_views, schema_migrations
- UUID primary keys throughout
- ENUM types: post_status, user_role, notification_type
- JSONB for flexible user preferences and post metadata
- TEXT[] for post tags with GIN index
- TSVECTOR search_vector with weighted full-text search
- Auto-update trigger: search_vector, updated_at, post counts
- 3 database views: published_posts_detail, author_leaderboard,
  tag_analytics, daily_analytics
- Custom PL/pgSQL function: get_user_stats(UUID)
- 14 analytical queries including window functions
- Full-text search with snippet highlighting
- Tag analytics using unnest() on arrays
- Interactive SQL query mode

## 🚀 How to Run

```bash
# First, set up PostgreSQL:
psql -U postgres
CREATE DATABASE blog_platform;
CREATE USER blog_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE blog_platform TO blog_user;
\c blog_platform
GRANT ALL ON SCHEMA public TO blog_user;
\q

# Then run the project:
cd Day-16-PostgreSQL
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your password
python src/main.py
```

## 🧠 Key PostgreSQL Features

| Feature          | Syntax                                      |
| ---------------- | ------------------------------------------- |
| UUID             | `DEFAULT uuid_generate_v4()`                |
| JSONB query      | `data->>'key'` or `data @> '{"k":"v"}'`     |
| Array contains   | `'python' = ANY(tags)`                      |
| GIN index        | `CREATE INDEX ON t USING GIN(col)`          |
| Full-text search | `col @@ to_tsquery('english', 'python')`    |
| Window rank      | `RANK() OVER (PARTITION BY x ORDER BY y)`   |
| Trigger          | `BEFORE INSERT OR UPDATE FOR EACH ROW`      |
| View             | `CREATE OR REPLACE VIEW name AS SELECT ...` |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
