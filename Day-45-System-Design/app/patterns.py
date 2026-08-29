# ============================================================
# app/patterns.py
# Architecture pattern library
# ============================================================

PATTERNS = {
    "read_replicas": {
        "name": "Read Replicas",
        "category": "scaling",
        "problem": "Single database can't handle read traffic at scale",
        "solution": "Primary handles writes → async replication to N read replicas → reads distributed across replicas",
        "when_to_use": [
            "Read:Write ratio > 5:1",
            "Read QPS exceeds single DB capacity (>5000 reads/second)",
            "Acceptable to read slightly stale data (replication lag = ms)"
        ],
        "trade_offs": {
            "pros": ["Scales reads linearly with replicas", "Simple to implement", "No schema changes"],
            "cons": ["Replication lag (reads may be stale)", "Writes still limited to primary", "Operational complexity"]
        },
        "latency": "Reads: same as primary, Writes: primary latency",
        "consistency": "Eventual (millisecond lag typical)"
    },

    "sharding": {
        "name": "Database Sharding",
        "category": "scaling",
        "problem": "Single database can't handle write volume or data size",
        "solution": "Split data across N independent database instances by shard key. Each shard owns a subset of data.",
        "when_to_use": [
            "Write QPS > 10,000/second",
            "Dataset > 10 TB (exceeds single server capacity)",
            "Query patterns are mostly key-based (avoid cross-shard joins)"
        ],
        "shard_key_selection": [
            "High cardinality (many distinct values)",
            "Even distribution (no hot spots)",
            "Query-aligned (most queries filter by this key)",
            "Common choices: user_id, order_id, geographic region"
        ],
        "trade_offs": {
            "pros": ["Scales writes linearly", "Scales storage linearly"],
            "cons": ["Cross-shard queries are expensive or impossible", "Resharding is painful", "Application complexity"]
        },
        "consistency": "Strong within shard, complex across shards"
    },

    "cqrs": {
        "name": "CQRS (Command Query Responsibility Segregation)",
        "category": "architecture",
        "problem": "Write model (normalized) is inefficient for complex reads. Read model (denormalized) is inefficient for writes.",
        "solution": "Separate write model (commands) from read model (queries). Events propagate changes from write to read model.",
        "when_to_use": [
            "Read and write workloads have very different shapes",
            "Need multiple read projections of the same data",
            "Using event sourcing"
        ],
        "trade_offs": {
            "pros": ["Optimized separately for reads and writes", "Flexible read projections"],
            "cons": ["Eventual consistency between write and read models", "Complexity", "Duplicate code"]
        },
        "consistency": "Eventual (seconds to milliseconds)"
    },

    "event_sourcing": {
        "name": "Event Sourcing",
        "category": "architecture",
        "problem": "Need full audit trail. Current state is insufficient — need to know HOW we got here.",
        "solution": "Store every change as an immutable event. Current state = replay all events from the beginning.",
        "when_to_use": [
            "Compliance/audit requirements (financial, healthcare)",
            "Need to replay history",
            "Temporal queries ('what was the state on date X?')",
            "Complex domain with many state transitions"
        ],
        "trade_offs": {
            "pros": ["Complete audit trail", "Time travel queries", "Replay to fix bugs"],
            "cons": ["Complex", "Replay time grows with history", "Schema evolution is hard"]
        }
    },

    "circuit_breaker": {
        "name": "Circuit Breaker",
        "category": "resilience",
        "problem": "A failing downstream service causes cascading failures. All requests queue, threads exhaust, entire system fails.",
        "solution": "Track failure rate. After N failures, 'open' circuit → immediately fail requests without calling downstream. Periodically test if service recovered.",
        "states": {
            "closed": "Normal operation — requests pass through",
            "open": "Service is failing — requests immediately rejected",
            "half_open": "Testing recovery — allow one request to test"
        },
        "when_to_use": [
            "Calling external services (payment, email, maps)",
            "Service-to-service calls in microservices",
            "Any I/O operation that can fail"
        ],
        "trade_offs": {
            "pros": ["Prevents cascade failures", "Faster failure (no waiting for timeout)", "Automatic recovery testing"],
            "cons": ["False positives (opens on temporary blip)", "Adds complexity"]
        }
    },

    "saga": {
        "name": "Saga Pattern",
        "category": "distributed_transactions",
        "problem": "Distributed transactions across microservices (2-phase commit is too slow and complex).",
        "solution": "Break transaction into local transactions per service. Each step publishes an event. On failure: compensating transactions undo completed steps.",
        "types": {
            "choreography": "Services react to events autonomously. No central coordinator. Simpler but harder to track.",
            "orchestration": "Central saga orchestrator tells services what to do. Easier to track, single point of failure."
        },
        "example": "Order placement: Create Order → Reserve Inventory → Charge Payment → Confirm. Failure at Charge: Cancel Order, Release Inventory.",
        "when_to_use": [
            "Cross-service transactions",
            "Long-running business processes",
            "When 2-phase commit is too slow"
        ],
        "trade_offs": {
            "pros": ["No distributed locks", "Services stay independent"],
            "cons": ["Eventual consistency", "Complex rollback logic", "Hard to debug"]
        }
    },

    "bulkhead": {
        "name": "Bulkhead Pattern",
        "category": "resilience",
        "problem": "One overloaded resource (DB connection pool) blocks all other operations.",
        "solution": "Isolate resources into pools. If one pool exhausts, others continue normally. Like watertight compartments in a ship.",
        "example": "Separate thread pools for: payment service calls, inventory service calls, email service calls. Payment pool exhaustion doesn't affect inventory.",
        "when_to_use": [
            "Multiple downstream dependencies with different criticality",
            "Need to isolate failures",
            "High-availability requirements"
        ]
    },

    "api_gateway": {
        "name": "API Gateway",
        "category": "microservices",
        "problem": "Clients must know about all microservices. Auth, rate limiting, logging in every service.",
        "solution": "Single entry point for all clients. Gateway handles: routing, auth, rate limiting, SSL termination, request transformation.",
        "when_to_use": [
            "Microservices architecture",
            "Multiple client types (mobile, web, 3rd party)",
            "Need centralized cross-cutting concerns"
        ],
        "trade_offs": {
            "pros": ["Single point for cross-cutting concerns", "Clients don't know service topology"],
            "cons": ["Single point of failure (mitigate with HA)", "Potential bottleneck", "Added network hop"]
        }
    }
}


def search_patterns(query: str) -> list[dict]:
    """Search patterns by keyword."""
    query_lower = query.lower()
    results = []
    for key, pattern in PATTERNS.items():
        text = f"{pattern['name']} {pattern['problem']} {' '.join(pattern.get('when_to_use', []))}".lower()
        if query_lower in text:
            results.append({"id": key, **pattern})
    return results


def get_pattern(pattern_id: str) -> dict | None:
    return PATTERNS.get(pattern_id)


def list_patterns() -> list[dict]:
    return [{"id": k, "name": v["name"], "category": v["category"],
             "problem": v["problem"][:100] + "..."}
            for k, v in PATTERNS.items()]