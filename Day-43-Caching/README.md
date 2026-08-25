# Day 43 — Caching Strategies & Performance Architecture

> **Phase 5 — System Design & Architecture** | Week 8 | Day 43 of 180

---

## 📌 What I Learned Today

- Cache hierarchy: registers → L1/L2/L3 CPU → in-process → Redis → DB → CDN
- Cache-Aside (Lazy Loading): check cache → miss → query DB → cache → return
- Write-Through: update both cache and DB on write → always consistent
- Write-Behind: update cache first, DB in background → fastest writes, risk data loss
- Cache invalidation: the hardest problem — delete or update on write
- Pattern-based invalidation: delete all keys matching prefix on list changes
- TTL: time-to-live — how long to keep a cached value
- TTL jitter: add ±10% random to TTL → spread expiry → prevent thundering herd
- Cache stampede: many requests miss at same time, all hit DB → crash
- Distributed lock (SET NX): only one request fetches on miss, others wait
- Probabilistic early expiration (XFetch): refresh before expiry, spread load
- L1 cache: in-process Python dict, ~microsecond reads, per-process only
- L2 cache: Redis, ~1ms reads, shared across all instances
- L1 eviction: simple LRU by hit count — remove least-hit entry at capacity
- MultiLayerCache.get_or_set(): cache-aside in one method with stampede protection
- Cache key naming: "resource:id", "resource:list:filter1:filter2"
- read_task: L1 → L2 → DB → populate both → return
- write_task: update DB → delete L1 → delete L2 (invalidate, not update)
- create_task: insert DB → delete_prefix("tasks:list:") all lists invalidated
- X-Cache header: HIT-L1, HIT-L2, or MISS for observability
- Sliding window rate limiter: sorted timestamps, remove old, count remaining
- Request metrics: latency p50/p95/p99, cache hit rate by layer

## 🔨 Project Built

**High-Performance Task API:**

**MultiLayerCache** (cache.py):

- L1: in-process dict, max 500 entries, 10s TTL, LRU eviction
- L2: MockRedis (1ms simulated latency), TTL jitter, pattern delete
- get_or_set(): cache-aside + stampede protection via SET NX lock
- delete_prefix(): invalidate all related keys atomically
- stats(): per-layer hit rate, miss count, stored keys

**MockRedis** (cache.py):

- Async get/setex/delete with 1ms simulated latency
- set_nx() for distributed locking
- delete_pattern() for prefix-based cache invalidation
- Per-operation hit/miss/set/delete counters

**Simulated DB** (database.py):

- Realistic 30-80ms query latency (random uniform)
- db_get_task, db_list_tasks, db_create_task, db_update_task, db_delete_task
- db_get_stats() expensive aggregation (always slow)
- Query count and P95 latency tracking

**SlidingWindowRateLimiter** (rate_limiter.py):

- Per-client timestamp deque
- Configurable window and limit
- Returns remaining, reset_in, retry_after

**FastAPI endpoints:**

- GET /tasks/{id}: L1 → L2 → DB with X-Cache header
- GET /tasks: cached list query with filter-aware cache key
- GET /stats: 10-minute cache for expensive aggregation
- POST /tasks: create + invalidate lists
- PATCH /tasks/{id}: update + invalidate task + lists
- DELETE /tasks/{id}: delete + invalidate
- POST /benchmark: automated speedup measurement
- GET /performance: live cache/DB/request metrics
- DELETE /cache: manual cache flush

## 🚀 How to Run

```bash
cd Day-43-Caching
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload

# See cache in action
curl http://localhost:8000/tasks/task-seed-001    # MISS (~50ms)
curl http://localhost:8000/tasks/task-seed-001    # HIT-L1 (<1ms)

# Benchmark
curl -X POST "http://localhost:8000/benchmark?n_requests=50"

# Performance dashboard
curl http://localhost:8000/performance
```

## 🧠 Cache Invalidation Rule

```
On READ:  check cache → hit: return | miss: DB → cache → return
On WRITE: update DB → delete cache (specific key + related lists)
On CREATE: insert DB → delete all list caches (prefix)
```

Never update cache on write — always invalidate and let reads repopulate.
Except for write-through, where you explicitly update both.

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
