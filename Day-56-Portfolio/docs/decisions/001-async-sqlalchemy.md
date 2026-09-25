# ADR-001: Use SQLAlchemy 2.0 Async Over Synchronous

**Date:** 2025-05-27  
**Status:** Accepted  
**Context:** TaskMind Phase 7, Day 51

## Context

FastAPI uses asyncio. SQLAlchemy has both sync and async APIs.
Synchronous DB calls inside async routes block the event loop.

## Decision

Use SQLAlchemy 2.0 async API with asyncpg driver.

## Consequences

**Positive:**
- Non-blocking DB queries — event loop handles other requests during DB wait
- asyncpg is the fastest PostgreSQL Python driver (benchmarks: ~4x faster than psycopg2)
- Full ORM features: models, migrations, query building

**Negative:**
- Every DB function must be `async def` and `await`ed
- `expire_on_commit=False` needed on session (objects expire by default after commit)
- Cannot use sync SQLAlchemy patterns (lazy loading works differently)

## Alternatives Rejected

- **Sync SQLAlchemy in thread pool:** Works but wastes threads, limits concurrency
- **Raw asyncpg:** Faster but loses ORM convenience (no models, no migrations)