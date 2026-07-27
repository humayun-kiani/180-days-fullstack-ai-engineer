# Day 19 — Redis: In-Memory Data Store, Caching & Pub/Sub

> **Phase 1 — Foundations** | Week 3 | Day 19 of 180

---

## 📌 What I Learned Today

- Why Redis is 100-500x faster than PostgreSQL
- Redis data structures and when to use each:
  - Strings: simple values, counters, flags, JSON blobs
  - Hashes: objects/records with multiple fields
  - Lists: queues, stacks, activity logs, notifications
  - Sets: unique collections, tags, online users, favorites
  - Sorted Sets: leaderboards, priority queues, rate limiting
- TTL and key expiration — self-cleaning cache entries
- SET EX, SETEX, EXPIRE, TTL, PERSIST commands
- Cache-Aside pattern: check cache → miss → DB → store in cache
- Write-Through pattern: write to DB and cache simultaneously
- Cache invalidation strategies
- Rate limiting with INCR + EXPIRE (fixed window)
- Session management with Hashes and SET for favorites
- Connection pooling with ConnectionPool
- Atomic operations: INCR, HINCRBY, ZINCRBY
- ZADD, ZREVRANGE, ZINCRBY for sorted set leaderboards
- LPUSH + LTRIM for fixed-size activity logs
- SADD, SMEMBERS, SISMEMBER for unique sets
- redis-py: Redis client, from_url, decode_responses
- Pipeline for batching multiple commands
- WATCH for optimistic locking in transactions
- Pub/Sub concepts: PUBLISH, SUBSCRIBE, listen()

## 🔨 Project Built

**Smart Weather Caching Layer** — Full Redis integration:

- Weather API wrapper with Cache-Aside caching
- Multi-tier TTL: 10 min (current), 30 min (forecast), 24h (history)
- STRING keys: weather:current:{city} → JSON-serialized weather
- HASH keys: cache:stats → hit/miss counters, session data
- LIST keys: search:history:{session} → recent searches (LPUSH/LTRIM)
- SET keys: favorites:{session} → unique favorite cities
- SORTED SET: city:search_count → real-time search leaderboard
- Rate limiter: 20 requests/60s with INCR + EXPIRE
- Session manager: create/get/destroy with sliding TTL
- Analytics: response time tracking, hit rate calculation
- Cache benchmark: cold vs warm comparison (6-7x speedup)
- All 5 data structures demonstrated with real data

## 🚀 How to Run

```bash
# Start Redis first:
brew services start redis     # Mac
sudo systemctl start redis    # Linux
docker run -d -p 6379:6379 redis:7-alpine   # Docker

# Then run:
cd Day-19-Redis-Caching
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python src/main.py
```

## 🧠 Key Redis Commands

| Data Structure | Key Commands                                            |
| -------------- | ------------------------------------------------------- |
| String         | `SET key value EX ttl`, `GET key`, `INCR key`           |
| Hash           | `HSET key field value`, `HGETALL key`, `HINCRBY`        |
| List           | `LPUSH key val`, `LRANGE key 0 -1`, `LTRIM key 0 N`     |
| Set            | `SADD key val`, `SMEMBERS key`, `SISMEMBER key val`     |
| Sorted Set     | `ZADD key score member`, `ZREVRANGE key 0 N WITHSCORES` |
| TTL            | `EXPIRE key seconds`, `TTL key`, `PERSIST key`          |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
