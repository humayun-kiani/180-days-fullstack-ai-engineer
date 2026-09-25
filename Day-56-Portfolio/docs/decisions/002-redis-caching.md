# ADR-002: Redis for Distributed Cache Over In-Process Dict

**Date:** 2025-05-27  
**Status:** Accepted

## Context

Task list queries are expensive (~15ms). With multiple API workers,
an in-process Python dict cache would be inconsistent across workers.

## Decision

Use Redis as a shared cache with cache-aside pattern.

## Consequences

**Positive:**
- Cache is shared across all workers — invalidation is immediate everywhere
- Redis survives API restarts (persistent cache)
- Supports pattern-based key deletion (`KEYS tasks:user-123:*`)

**Negative:**
- Additional service to run and operate
- Network latency (~0.2ms per call)
- Cache invalidation bugs are harder to debug

## Key Design Choices

- TTL = 30s for task lists (freshness vs performance balance)
- Invalidate on ANY write to that user's tasks
- Graceful degradation: if Redis is down, requests hit DB (slower but correct)