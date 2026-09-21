# Day 55 — Performance Optimization

> **Phase 7 — Full Stack Integration** | Day 55 of 180

---

## 📌 What I Learned Today

- Always measure first — never guess where the bottleneck is
- User perception: < 100ms instant, 100-300ms fast, > 1s slow
- EXPLAIN ANALYZE: runs the query and shows real execution plan
- Seq Scan vs Index Scan: full table vs index lookup
- Composite index: CREATE INDEX ON tasks(owner_id, created_at DESC)
- N+1 problem: 1 query for N items + N queries for relations = slow
- selectinload: 2 queries (1 tasks + 1 all owners) — eliminates N+1
- joinedload: 1 query with JOIN — good for many-to-one
- Query event listener: sqlalchemy.event.listens_for + before/after
- Per-request tracking with threading.local for thread safety
- N+1 detection: same query statement repeated 3+ times in one request
- Connection pool: pool_size × workers must be < PostgreSQL max_connections
- pool_pre_ping: test connection before using — handles disconnects
- Cache-aside pattern: check cache → miss → DB → populate cache
- Cache invalidation: delete_pattern(f"tasks:{user_id}:*") on write
- TTL strategy: lists=30s, stats=300s, AI=3600s, profiles=1800s
- Cache stampede: concurrent misses all hit DB — use asyncio.Lock
- Hit rate target: > 70% for list endpoints to be worth caching
- Code splitting: lazy() + Suspense defers loading non-critical code
- useCallback: memoizes function reference — prevents child re-renders
- useMemo: memoizes expensive computation — recalculates only on deps change
- React.memo: skips component render if props didn't change
- Virtual scrolling: render only visible items from a large list
- ITEM_HEIGHT × index = absolute position in virtual container
- Locust: Python load testing — task weights simulate real usage patterns
- wait_time between(1, 3): realistic user think time
- p50/p95/p99: percentile latency — p99 catches worst-case users
- Web Vitals: LCP < 2.5s, CLS < 0.1, FID < 100ms (Lighthouse targets)
- X-Query-Count header: see DB query count on every API response
- Profiling middleware: wraps every request, tracks DB time and N+1

## 🔨 Project Built

**Performance Profiling and Optimization Stack:**

**Backend profiling:**
- QueryProfiler: SQLAlchemy event listener counts and times every query
- N+1 detector: flags when same statement runs 3+ times per request
- ProfilingMiddleware: adds X-Query-Count, X-DB-Time-Ms to every response
- CacheAnalyzer: tracks hit rate, avg hit/miss time per key prefix

**Profiling API endpoints:**
- GET /api/profile/queries: slow query log + global aggregates
- GET /api/profile/cache: hit rate by prefix + recommendations
- GET /api/profile/n-plus-1-demo: live benchmark of N+1 vs eager load
- GET /api/profile/benchmark/list-tasks: DB vs cache timing
- GET /api/profile/benchmark/search: ILIKE performance by row count
- GET /api/profile/memory: process RSS memory
- GET /api/profile/recommendations: specific fixes based on observed data

**Benchmarks:**
- benchmark_queries.py: 5 query types × 5 iterations on 500 tasks
- benchmark_cache.py: cache vs no-cache across TTL scenarios

**Load tests:**
- TaskMindUser: 10 task weights simulate real usage (list 10x vs create 3x)
- ReadHeavyUser: monitoring/admin persona
- 4 scenarios: smoke, load, stress, spike

**Frontend optimizations:**
- useOptimizedTasks: stable callbacks + memoized tasksByStatus/counts
- useDebounce: 250ms delay on search input
- VirtualTaskList: renders only visible + overscan tasks
- performance.js: TTI, Web Vitals, render count tracking

## 🚀 How to Run

```bash
# Benchmarks (no running server needed)
cd backend
python benchmarks/benchmark_queries.py
python benchmarks/benchmark_cache.py

# Profiled API
uvicorn app.main:app --reload

# Load test
cd load_tests
locust -f locustfile.py --host=http://localhost:8000 --headless \
  --users 20 --spawn-rate 2 --run-time 60s
```

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)