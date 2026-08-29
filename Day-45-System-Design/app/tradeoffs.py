# ============================================================
# app/tradeoffs.py
# Trade-off comparison tool
# ============================================================

COMPARISONS = {
    "sql_vs_nosql": {
        "title": "SQL vs NoSQL",
        "options": {
            "sql": {
                "name": "SQL (PostgreSQL, MySQL)",
                "strengths": [
                    "ACID transactions (strong consistency)",
                    "Complex queries with JOINs",
                    "Schema enforcement catches data bugs early",
                    "Mature tooling and ecosystem",
                    "Best for: structured relational data"
                ],
                "weaknesses": [
                    "Harder to scale writes horizontally",
                    "Schema changes require migrations",
                    "Less flexible for varying data shapes"
                ],
                "use_when": ["Financial data", "User accounts", "Inventory", "Any data needing ACID"]
            },
            "nosql_document": {
                "name": "NoSQL Document (MongoDB, DynamoDB)",
                "strengths": [
                    "Flexible schema (add fields anytime)",
                    "Horizontal scaling built-in",
                    "Good for hierarchical/nested data",
                    "Fast reads with proper indexing"
                ],
                "weaknesses": [
                    "No JOINs (must denormalize or do in application)",
                    "Eventual consistency by default",
                    "Harder to ensure data integrity"
                ],
                "use_when": ["Product catalogs", "User profiles", "Content management", "Variable schema data"]
            },
            "nosql_columnar": {
                "name": "Wide Column (Cassandra, HBase)",
                "strengths": [
                    "Massive write throughput",
                    "Linear horizontal scaling",
                    "Time-series data is natural fit",
                    "High availability (no single master)"
                ],
                "weaknesses": [
                    "No JOINs, no ad-hoc queries",
                    "Schema design must match query patterns",
                    "Limited secondary indexes"
                ],
                "use_when": ["IoT time-series", "Chat messages", "Activity logs", "Write-heavy at billions of events"]
            }
        }
    },

    "sync_vs_async": {
        "title": "Synchronous vs Asynchronous Communication",
        "options": {
            "synchronous_rest": {
                "name": "Synchronous REST/gRPC",
                "strengths": [
                    "Simple to implement and debug",
                    "Immediate response (caller knows result)",
                    "Easy error handling (HTTP status codes)",
                    "Natural fit for request-response patterns"
                ],
                "weaknesses": [
                    "Caller blocks waiting for response",
                    "Tight coupling (caller must know callee address)",
                    "Cascade failures if downstream is slow/down",
                    "Can't fan-out to multiple consumers easily"
                ],
                "use_when": ["Need immediate answer to proceed", "Simple CRUD operations", "Low traffic inter-service calls"]
            },
            "async_events": {
                "name": "Asynchronous Events (Kafka, RabbitMQ)",
                "strengths": [
                    "Loose coupling (producer doesn't know consumers)",
                    "Fan-out: one event, many consumers",
                    "Resilient: consumer down = events wait in queue",
                    "Temporal decoupling: process at your own pace"
                ],
                "weaknesses": [
                    "No immediate response",
                    "Harder to debug (distributed traces needed)",
                    "Eventual consistency",
                    "Operational overhead (queue management)"
                ],
                "use_when": ["Notifications", "Audit logs", "Background processing", "Fan-out to multiple systems"]
            }
        }
    },

    "cdn_vs_origin": {
        "title": "CDN vs Origin Server",
        "options": {
            "cdn": {
                "name": "CDN (CloudFront, Fastly, Cloudflare)",
                "strengths": [
                    "Global edge nodes (low latency worldwide)",
                    "Absorbs massive traffic (100TB+/s aggregate)",
                    "DDoS protection",
                    "Offloads origin (origin handles cache misses only)"
                ],
                "weaknesses": [
                    "Stale content (TTL-based, not real-time)",
                    "Cache invalidation can take minutes to propagate",
                    "Cost per GB",
                    "Dynamic content still hits origin"
                ],
                "use_when": ["Static assets (images, CSS, JS)", "Popular read-only API responses", "Global user base", "Media streaming"]
            },
            "origin": {
                "name": "Direct Origin Server",
                "strengths": [
                    "Always fresh data",
                    "Full control",
                    "Simpler architecture"
                ],
                "weaknesses": [
                    "Higher latency for geographically distant users",
                    "Must scale origin for full traffic",
                    "No DDoS protection by default"
                ],
                "use_when": ["Highly personalized content", "Real-time data", "Low traffic", "Simple apps"]
            }
        }
    },

    "consistency_models": {
        "title": "Consistency Models",
        "options": {
            "strong": {
                "name": "Strong Consistency (CP)",
                "description": "All reads see the most recent write. No stale reads.",
                "examples": ["PostgreSQL", "ZooKeeper", "etcd"],
                "latency_impact": "Higher (must coordinate across nodes before responding)",
                "availability_impact": "Lower (may reject requests during partition)",
                "use_when": ["Financial transactions", "Inventory management", "Configuration data", "Leader election"]
            },
            "eventual": {
                "name": "Eventual Consistency (AP)",
                "description": "Reads may return stale data. Eventually all nodes agree.",
                "examples": ["Cassandra", "DynamoDB (default)", "DNS"],
                "latency_impact": "Lower (read from nearest replica immediately)",
                "availability_impact": "Higher (always responds, even during partition)",
                "use_when": ["Social media feeds", "Shopping carts", "Product catalogs", "User preferences"]
            },
            "causal": {
                "name": "Causal Consistency",
                "description": "Causally related operations are seen in order. Unrelated may be out of order.",
                "examples": ["MongoDB (causal sessions)", "Amazon Aurora"],
                "use_when": ["Comments on posts", "Chat messages (preserving reply order)"]
            }
        }
    }
}


def compare(comparison_id: str) -> dict | None:
    return COMPARISONS.get(comparison_id)


def list_comparisons() -> list[dict]:
    return [
        {"id": k, "title": v["title"],
         "options": list(v["options"].keys())}
        for k, v in COMPARISONS.items()
    ]