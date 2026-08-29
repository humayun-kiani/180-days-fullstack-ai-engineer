# Day 45 — System Design Interview Patterns

> **Phase 5 — System Design & Architecture** | Week 8 Capstone | Day 45 of 180

---

## 📌 What I Learned Today

- 6-step framework: Clarify → Estimate → High-Level → Deep Dive → Bottlenecks → Trade-offs
- Always clarify before designing — wrong assumptions waste 45 minutes
- Capacity estimation: users × DAU_rate × writes_per_dau / 86400 = write QPS
- Peak = 3x average (rule of thumb)
- Numbers: Redis 100K ops/s, PostgreSQL 5-10K reads/s, API server 1-10K req/s
- CAP theorem: CP vs AP — the real choice (P is mandatory in distributed systems)
- CP: strong consistency, may reject during partition (banking, inventory)
- AP: always available, may be stale (social feeds, catalogs)
- PACELC: even without partition, choose Latency vs Consistency
- URL shortener: base62 7-char codes, CDN for redirects, 301 vs 302 trade-off
- Rate limiter: sliding window counter in Redis, fail open vs fail closed
- Notification service: fan-in to Kafka → per-channel workers → retry → DLQ
- Twitter timeline: hybrid push/pull model (push < 10K followers, pull for celebrities)
- Read replicas: scale reads linearly, eventual consistency acceptable
- Sharding: scale writes, shard key selection critical (cardinality + distribution)
- CQRS: separate write model (normalized) from read model (denormalized)
- Event sourcing: store events not state, replay to rebuild
- Circuit breaker: CLOSED → OPEN → HALF_OPEN state machine
- Saga pattern: distributed transactions without 2PC
- Bulkhead: isolate resource pools to prevent cascade failures
- API gateway: single entry point for cross-cutting concerns
- Trade-off template: "I chose X over Y. X gives [benefit]. Trade-off is [cost]. Acceptable because [reason]."
- Hot spots: celebrity problem → pull for high-follower accounts
- Keyset vs offset pagination: offset O(depth), keyset O(1) always

## 🔨 Project Built

**System Design Simulator API:**

5 classic designs with:

- Functional + non-functional requirements
- Capacity calculations
- API design
- Data model
- Architecture (boxes and arrows)
- Bottlenecks + solutions
- Key decisions with trade-offs

8 architecture patterns:

- read_replicas, sharding, cqrs, event_sourcing
- circuit_breaker, saga, bulkhead, api_gateway
- Each: problem, solution, when to use, trade-offs

Capacity calculator:

- Input: users, DAU rate, reads/writes per user, bytes, retention
- Output: QPS, storage, bandwidth, infrastructure recommendations

4 trade-off comparisons:

- sql_vs_nosql, sync_vs_async, cdn_vs_origin, consistency_models

6-step framework endpoint with timing + common mistakes

## 🚀 How to Run

```bash
cd Day-45-System-Design
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

curl http://localhost:8000/designs/url_shortener
curl -X POST http://localhost:8000/calculate/capacity -d '{"users":100000000,...}'
curl http://localhost:8000/framework
curl http://localhost:8000/patterns/sharding
```

## 🧠 Interview Cheat Sheet

| Scenario                    | Solution          |
| --------------------------- | ----------------- |
| Read QPS > 5K               | Add read replicas |
| Read QPS > 100K             | Add CDN + Redis   |
| Write QPS > 10K             | Shard database    |
| Need full audit trail       | Event sourcing    |
| Cross-service transactions  | Saga pattern      |
| Cascade failure prevention  | Circuit breaker   |
| One service for all clients | API gateway       |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
