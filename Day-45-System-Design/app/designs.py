# ============================================================
# app/designs.py
# Classic system design templates
# ============================================================

DESIGNS = {
    "url_shortener": {
        "name": "URL Shortener",
        "examples": ["bit.ly", "tinyurl.com", "t.co"],
        "difficulty": "easy",
        "requirements": {
            "functional": [
                "POST /shorten {long_url} → short_url",
                "GET /{shortCode} → 301/302 redirect",
                "Optional: custom aliases, expiry, analytics"
            ],
            "non_functional": [
                "100M URLs created per day",
                "Read:Write = 100:1",
                "< 10ms redirect latency",
                "99.99% availability"
            ]
        },
        "capacity": {
            "write_qps": "100M / 86400 ≈ 1,200 writes/second",
            "read_qps": "10B / 86400 ≈ 115,000 reads/second",
            "storage_per_record": "500 bytes",
            "total_storage_5yr": "100M × 365 × 5 × 500B ≈ 90 TB"
        },
        "api": {
            "shorten": "POST /api/v1/urls  Body: {url, alias?, ttl?}",
            "redirect": "GET /{shortCode}  → 301 Location: {longUrl}",
            "stats":    "GET /api/v1/urls/{shortCode}/stats"
        },
        "data_model": {
            "urls": {
                "short_code": "VARCHAR(7) PK",
                "long_url": "TEXT NOT NULL",
                "user_id": "UUID",
                "created_at": "TIMESTAMP",
                "expires_at": "TIMESTAMP",
                "click_count": "BIGINT DEFAULT 0"
            }
        },
        "architecture": [
            "Client → CDN (cache 301 redirects) → Load Balancer",
            "Load Balancer → API Servers (stateless, horizontal scale)",
            "API Servers → Redis Cache (shortCode→longURL, TTL=24h)",
            "Redis MISS → PostgreSQL (sharded by first 2 chars of shortCode)",
            "Analytics: click events → Kafka → ClickHouse (columnar DB)"
        ],
        "short_code_generation": {
            "chosen": "Random base62 (a-zA-Z0-9), 7 characters = 62^7 = 3.5T combos",
            "alternatives": {
                "md5_prefix": "Collision risk at scale",
                "auto_increment": "Predictable (security risk)",
                "snowflake_id": "Distributed unique IDs, complex setup"
            }
        },
        "bottlenecks": [
            "Hot URLs: serve from CDN (301 cached at edge)",
            "DB writes at 1200/s: single PostgreSQL handles fine",
            "DB reads at 115K/s: Redis cache handles 99% of reads",
            "Storage at 90TB: object storage (S3) for analytics, DB for metadata"
        ],
        "key_decisions": [
            "301 vs 302: 301 = browser caches (fewer requests), 302 = track analytics",
            "Shard key: shortCode hash → consistent hashing for easy addition of nodes",
            "Cache TTL: 24h for popular URLs, 1h for rare ones"
        ]
    },

    "rate_limiter": {
        "name": "Rate Limiter",
        "examples": ["API gateway limiting", "GitHub API 5000 req/hr", "Twitter 300 req/15min"],
        "difficulty": "medium",
        "requirements": {
            "functional": [
                "Limit requests per user per time window",
                "Return 429 with Retry-After header",
                "Support different limits per API endpoint",
                "Works across multiple API server instances"
            ],
            "non_functional": [
                "< 2ms additional latency per request",
                "Highly available (rate limiter down = all requests allowed or blocked?)",
                "Eventually consistent (brief over-limit acceptable)"
            ]
        },
        "algorithms": {
            "token_bucket": {
                "description": "Bucket fills at rate R, max capacity C. Each request consumes 1 token.",
                "pros": "Handles bursts well, easy to understand",
                "cons": "Slightly complex to implement distributed"
            },
            "sliding_window_counter": {
                "description": "current_count + prev_count × (1 - elapsed_fraction)",
                "pros": "Accurate, memory efficient",
                "cons": "Approximate (within 1% error)"
            },
            "fixed_window": {
                "description": "Reset counter every N seconds",
                "pros": "Simple",
                "cons": "2x burst possible at window boundaries"
            },
            "chosen": "Sliding Window Counter — best balance of accuracy and efficiency"
        },
        "architecture": [
            "Client → API Gateway (rate limiter lives here)",
            "API Gateway → Redis (centralized counter, shared across servers)",
            "Redis: INCR key, EXPIRE key  (atomic operations)",
            "On limit exceeded: 429 response, no upstream call"
        ],
        "redis_operations": [
            "key = f'rl:{user_id}:{window_bucket}'",
            "count = INCR key",
            "if count == 1: EXPIRE key window_seconds",
            "if count > limit: return 429"
        ],
        "bottlenecks": [
            "Redis single point of failure: use Redis Cluster or Sentinel",
            "Redis latency: < 1ms with local Redis, use async pipeline",
            "What if Redis is down: fail open (allow all) vs fail closed (block all)"
        ],
        "key_decisions": [
            "Fail open vs fail closed: usually fail open (availability > security for most APIs)",
            "Client-side vs server-side: client-side reduces traffic but can be bypassed",
            "Per-endpoint limits: use composite key = user_id + endpoint"
        ]
    },

    "notification_service": {
        "name": "Notification Service",
        "examples": ["Push notifications", "Email alerts", "SMS verification"],
        "difficulty": "medium",
        "requirements": {
            "functional": [
                "Send via email, push, SMS, in-app",
                "User opt-in/out per channel and notification type",
                "Respect quiet hours",
                "Template rendering with personalization",
                "Delivery status tracking"
            ],
            "non_functional": [
                "10M users, 100M notifications/day (1,150/second)",
                "At-least-once delivery",
                "Email within 5 minutes for 99% of notifications",
                "Support retry with exponential backoff"
            ]
        },
        "capacity": {
            "notification_qps": "100M / 86400 ≈ 1,150 notifications/second",
            "storage_per_notification": "500 bytes",
            "total_storage_1yr": "100M × 365 × 500B ≈ 17 TB"
        },
        "architecture": [
            "Producer Services → Message Queue (Kafka) → Notification Router",
            "Router: check user preferences → fan-out to channel workers",
            "Email Worker → AWS SES / SendGrid",
            "Push Worker → Firebase FCM / Apple APNs",
            "SMS Worker → Twilio",
            "In-App → Redis Pub/Sub → WebSocket connections",
            "Failed sends → Dead Letter Queue → retry with backoff"
        ],
        "data_model": {
            "notifications": "id, user_id, type, template, payload(JSONB), status, retry_count, created_at, sent_at",
            "user_preferences": "user_id, channel, enabled, quiet_hours_start, quiet_hours_end",
            "device_tokens": "user_id, platform, token, active, last_seen"
        },
        "failure_handling": {
            "retry_strategy": "30s → 2m → 10m → 1h → DLQ after 5 failures",
            "idempotency": "Store notification_id in provider records, skip if already sent",
            "monitoring": "Alert if DLQ depth > 1000, alert if email delivery rate < 95%"
        },
        "key_decisions": [
            "Template rendering: in notification service (single responsibility)",
            "Fan-in pattern: all services publish to one Kafka topic, router decides channels",
            "Async by default: producers don't wait for delivery confirmation"
        ]
    },

    "twitter_timeline": {
        "name": "Twitter/Social Feed Timeline",
        "examples": ["Twitter Home Timeline", "Facebook News Feed", "Instagram Feed"],
        "difficulty": "hard",
        "requirements": {
            "functional": [
                "POST a tweet",
                "GET home timeline (tweets from people you follow)",
                "Follow/unfollow users",
                "Like, retweet, reply"
            ],
            "non_functional": [
                "500M registered users, 100M DAU",
                "300M tweets/day (3,500 writes/second)",
                "Timeline loads < 200ms",
                "Read:Write = 100:1",
                "Eventual consistency acceptable (timeline can be seconds stale)"
            ]
        },
        "timeline_approaches": {
            "pull_model": {
                "description": "On timeline load: query all followed users' tweets, merge, sort",
                "pros": "Simple, no fan-out on write",
                "cons": "Slow (N queries per load, where N = following count)",
                "good_for": "Users with few followers (< 1000)"
            },
            "push_model": {
                "description": "On tweet: push to all followers' timeline caches",
                "pros": "Fast timeline reads (single cache lookup)",
                "cons": "Slow for celebrities (1 tweet → push to 10M followers)",
                "good_for": "Users with few followers"
            },
            "hybrid_model": {
                "description": "Push for normal users, pull for celebrities",
                "pros": "Best of both worlds",
                "cons": "Complex implementation",
                "chosen": True,
                "threshold": "Push if follower count < 10,000, pull for celebrities"
            }
        },
        "data_model": {
            "tweets": "tweet_id(Snowflake), user_id, content, media_ids, created_at",
            "follows": "follower_id, followee_id, created_at",
            "timeline_cache": "Redis sorted set per user: key=user_id, members=(tweet_id), score=(timestamp)"
        },
        "bottlenecks": [
            "Kylie Jenner problem: 100M followers, 1 tweet → 100M cache writes",
            "Solution: async fan-out via Kafka, celebrity tweets pulled at read time",
            "Storage: 300M tweets/day × 365 × 5yr × 500B ≈ 270 TB → object storage",
            "Follower graph: graph DB (Neo4j) or adjacency list in PostgreSQL"
        ]
    },

    "chat_system": {
        "name": "Chat System (WhatsApp/Slack)",
        "examples": ["WhatsApp", "Slack", "Discord"],
        "difficulty": "hard",
        "requirements": {
            "functional": [
                "1-on-1 messaging",
                "Group chats (up to 100 members)",
                "Online/offline presence",
                "Message delivery receipts (sent, delivered, read)",
                "Push notifications for offline users"
            ],
            "non_functional": [
                "50M DAU",
                "40M messages/day (460/second)",
                "< 100ms message delivery when both online",
                "Message history: last 5 years"
            ]
        },
        "architecture": [
            "WebSocket servers (maintain persistent connections)",
            "Connection registry in Redis (user_id → server_id mapping)",
            "On message: look up recipient's server → route to that server → deliver via WebSocket",
            "If recipient offline: push notification via FCM/APNs",
            "Message storage: Cassandra (write-heavy, append-only, massive scale)"
        ],
        "key_decisions": [
            "WebSocket vs long polling: WebSocket for real-time, long polling as fallback",
            "Message ID generation: Snowflake IDs (timestamp + server_id + sequence)",
            "Message ordering: client-side clock + server timestamp, display chronologically",
            "Read receipts: separate table, batch updates to reduce write overhead"
        ]
    }
}