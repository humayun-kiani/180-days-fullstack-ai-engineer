# ============================================================
# app/main.py
# System Design Simulator — Day 45
# ============================================================

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.designs import DESIGNS
from app.calculator import estimate_capacity, estimate_latency_budget
from app.patterns import PATTERNS, search_patterns, get_pattern, list_patterns
from app.tradeoffs import COMPARISONS, compare, list_comparisons


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 65)
    print("  System Design Simulator — Day 45")
    print("  Phase 5 Capstone: System Design Interview Patterns")
    print("=" * 65)
    print(f"\n  Designs:    {len(DESIGNS)} classic systems")
    print(f"  Patterns:   {len(PATTERNS)} architecture patterns")
    print(f"  Comparisons: {len(COMPARISONS)} trade-off analyses")
    print(f"\n  Docs: http://localhost:8000/docs\n")
    yield
    print("\n  Shutting down...")


app = FastAPI(
    title="System Design Simulator",
    description="""
## 🏗️ System Design Simulator — Day 45

Interactive reference for system design interviews.

### Available Resources

**System Designs** (5 classic systems):
- `url_shortener` — bit.ly at scale
- `rate_limiter` — API rate limiting
- `notification_service` — multi-channel notifications
- `twitter_timeline` — social feed at scale
- `chat_system` — real-time messaging

**Architecture Patterns** (8 patterns):
- Read Replicas, Sharding, CQRS, Event Sourcing
- Circuit Breaker, Saga, Bulkhead, API Gateway

**Trade-off Comparisons** (4 comparisons):
- SQL vs NoSQL, Sync vs Async, CDN vs Origin, Consistency Models

**Tools**:
- Capacity calculator (back-of-envelope estimation)
- Latency budget breakdown
- Pattern search

### Interview Framework
Use `GET /framework` for the 6-step interview guide.
    """,
    version="1.0.0",
    lifespan=lifespan
)


# ─── System Designs ───────────────────────────────────────────

@app.get("/designs", summary="List all system design templates")
def list_designs() -> dict:
    return {
        "designs": [
            {
                "id": k,
                "name": v["name"],
                "difficulty": v["difficulty"],
                "examples": v["examples"]
            }
            for k, v in DESIGNS.items()
        ],
        "count": len(DESIGNS)
    }


@app.get("/designs/{design_id}", summary="Get full system design template")
def get_design(design_id: str) -> dict:
    design = DESIGNS.get(design_id)
    if not design:
        available = list(DESIGNS.keys())
        raise HTTPException(404, f"Design '{design_id}' not found. Available: {available}")
    return {"id": design_id, **design}


# ─── Capacity Calculator ──────────────────────────────────────

class CapacityRequest(BaseModel):
    users: int = Field(ge=1000, example=10_000_000)
    daily_active_rate: float = Field(default=0.1, ge=0.01, le=1.0,
                                      description="Fraction of users active daily")
    writes_per_dau: float = Field(default=1.0, ge=0.01,
                                   description="Average writes per daily active user")
    reads_per_dau: float = Field(default=10.0, ge=0.1,
                                  description="Average reads per daily active user")
    bytes_per_write: int = Field(default=1000, ge=10,
                                  description="Average write size in bytes")
    retention_years: int = Field(default=5, ge=1, le=20)

    class Config:
        json_schema_extra = {
            "example": {
                "users": 100_000_000,
                "daily_active_rate": 0.2,
                "writes_per_dau": 3,
                "reads_per_dau": 100,
                "bytes_per_write": 500,
                "retention_years": 5
            }
        }


@app.post(
    "/calculate/capacity",
    summary="Back-of-envelope capacity estimation"
)
def calculate_capacity(request: CapacityRequest) -> dict:
    """
    Calculate infrastructure requirements from user and usage parameters.

    Returns: QPS, storage, bandwidth, and infrastructure recommendations.
    """
    result = estimate_capacity(
        users=request.users,
        daily_active_rate=request.daily_active_rate,
        writes_per_dau=request.writes_per_dau,
        reads_per_dau=request.reads_per_dau,
        bytes_per_write=request.bytes_per_write,
        retention_years=request.retention_years
    )
    return result


@app.get(
    "/calculate/latency-budget",
    summary="Break down a latency budget across components"
)
def calculate_latency(
    target_ms: float = Query(200.0, description="Target P99 latency in milliseconds")
) -> dict:
    """Break down how to allocate a latency budget."""
    return estimate_latency_budget(target_ms)


@app.get(
    "/calculate/numbers",
    summary="Reference numbers every engineer should know"
)
def reference_numbers() -> dict:
    return {
        "latency_hierarchy": {
            "l1_cache": "0.5 ns",
            "l2_cache": "7 ns",
            "ram": "100 ns",
            "ssd": "100 μs (1,000x RAM)",
            "network_same_dc": "500 μs",
            "hdd": "10 ms (100x SSD)",
            "network_cross_country": "150 ms",
            "network_cross_globe": "300 ms"
        },
        "throughput": {
            "redis_single": "100,000 ops/second",
            "postgresql_reads": "5,000–10,000 queries/second",
            "postgresql_writes": "1,000–5,000 writes/second",
            "kafka_partition": "100,000 messages/second",
            "api_server": "1,000–10,000 HTTP req/second"
        },
        "availability_sla": {
            "99%": "3.65 days downtime/year",
            "99.9%": "8.76 hours/year (three nines)",
            "99.99%": "52.6 minutes/year (four nines)",
            "99.999%": "5.26 minutes/year (five nines)"
        },
        "data_sizes": {
            "ascii_char": "1 byte",
            "uuid": "16 bytes",
            "timestamp": "8 bytes",
            "typical_api_response": "1–10 KB",
            "photo_compressed": "~200 KB",
            "video_1min_720p": "~50 MB"
        },
        "time_conversions": {
            "1_day": "86,400 seconds ≈ 100,000 (good for estimation)",
            "1_month": "2,500,000 seconds",
            "1_year": "31,500,000 seconds"
        }
    }


# ─── Architecture Patterns ────────────────────────────────────

@app.get("/patterns", summary="List all architecture patterns")
def get_patterns() -> dict:
    return {"patterns": list_patterns(), "count": len(PATTERNS)}


@app.get("/patterns/search", summary="Search patterns by keyword")
def search(q: str = Query(..., min_length=2)) -> dict:
    results = search_patterns(q)
    return {"query": q, "results": results, "count": len(results)}


@app.get("/patterns/{pattern_id}", summary="Get pattern details")
def get_pattern_detail(pattern_id: str) -> dict:
    pattern = get_pattern(pattern_id)
    if not pattern:
        raise HTTPException(404, f"Pattern '{pattern_id}' not found. Available: {list(PATTERNS.keys())}")
    return {"id": pattern_id, **pattern}


# ─── Trade-off Comparisons ────────────────────────────────────

@app.get("/tradeoffs", summary="List all trade-off comparisons")
def get_tradeoffs() -> dict:
    return {"comparisons": list_comparisons()}


@app.get("/tradeoffs/{comparison_id}", summary="Get detailed trade-off comparison")
def get_tradeoff(comparison_id: str) -> dict:
    result = compare(comparison_id)
    if not result:
        raise HTTPException(
            404,
            f"Comparison '{comparison_id}' not found. Available: {list(COMPARISONS.keys())}"
        )
    return {"id": comparison_id, **result}


# ─── Interview Framework ──────────────────────────────────────

@app.get("/framework", summary="6-step system design interview framework")
def get_framework() -> dict:
    return {
        "framework": "6-Step System Design Interview Framework",
        "total_time": "45 minutes",
        "steps": [
            {
                "step": 1,
                "name": "Clarify Requirements",
                "time": "5 minutes",
                "questions_to_ask": [
                    "What are the core features? (prioritize top 3)",
                    "How many users? DAU?",
                    "Read-heavy or write-heavy? What ratio?",
                    "What is the acceptable latency?",
                    "Availability requirement: 99.9% or 99.99%?",
                    "Is strong consistency required or eventual OK?"
                ],
                "red_flag": "Starting to design without asking these → wrong assumptions"
            },
            {
                "step": 2,
                "name": "Capacity Estimation",
                "time": "5 minutes",
                "what_to_calculate": [
                    "QPS (write and read, average and peak)",
                    "Storage per record and total",
                    "Bandwidth (in and out)",
                    "Peak = 3x average"
                ],
                "tip": "Use POST /calculate/capacity during prep. One order of magnitude off → wrong architecture."
            },
            {
                "step": 3,
                "name": "High-Level Design",
                "time": "10 minutes",
                "cover": [
                    "Core APIs (just the important ones)",
                    "Data model (main tables/collections)",
                    "Major components (boxes and arrows)",
                    "Data flow for the main use cases"
                ],
                "tip": "Draw left to right: Client → LB → API → Cache → DB"
            },
            {
                "step": 4,
                "name": "Component Deep Dive",
                "time": "15 minutes",
                "focus_on": [
                    "The hardest part of the design",
                    "What the interviewer seems most interested in",
                    "Novel or non-obvious design decisions"
                ],
                "examples": [
                    "ID generation strategy",
                    "Timeline fan-out algorithm",
                    "Consistent hashing for sharding",
                    "Cache invalidation strategy"
                ]
            },
            {
                "step": 5,
                "name": "Bottlenecks & Scale",
                "time": "5 minutes",
                "questions_to_answer": [
                    "Where does your design break at 10x traffic?",
                    "What's the single point of failure?",
                    "How do you handle a celebrity with 100M followers?"
                ],
                "common_solutions": [
                    "Database bottleneck → read replicas or sharding",
                    "API bottleneck → horizontal scaling behind load balancer",
                    "Cache bottleneck → Redis Cluster or consistent hashing",
                    "Network bottleneck → CDN for static/popular content"
                ]
            },
            {
                "step": 6,
                "name": "Trade-offs & Alternatives",
                "time": "5 minutes",
                "show": [
                    "You considered multiple approaches",
                    "You know why you chose what you chose",
                    "You know the costs of your choices"
                ],
                "template": "I chose X over Y. X gives us [benefit]. The trade-off is [cost]. We accept this because [reason]."
            }
        ],
        "common_mistakes": [
            "Jumping to implementation before clarifying requirements",
            "Skipping capacity estimation (design doesn't match scale)",
            "Not mentioning trade-offs (every choice has a cost!)",
            "Over-engineering small problems (don't shard a 1K-user system)",
            "Under-engineering large problems (single DB for 1B users)",
            "Not asking for feedback (interviewer may want different direction)"
        ]
    }


@app.get("/cap-theorem", summary="CAP theorem explained")
def cap_theorem() -> dict:
    return {
        "cap_theorem": {
            "definition": "In a distributed system, you can guarantee at most 2 of: Consistency, Availability, Partition Tolerance",
            "practical_reality": "Network partitions ALWAYS happen → real choice is CP vs AP",
            "cp_systems": {
                "guarantee": "Strong consistency, may be unavailable during partition",
                "examples": ["PostgreSQL", "HBase", "ZooKeeper", "etcd"],
                "use_for": ["Banking", "Inventory", "Leader election", "Config management"]
            },
            "ap_systems": {
                "guarantee": "Always available, may return stale data during partition",
                "examples": ["Cassandra", "DynamoDB", "CouchDB", "DNS"],
                "use_for": ["Social feeds", "Shopping carts", "Product catalogs", "User preferences"]
            },
            "pacelc": "Even without partition: choose Latency (read nearest replica) vs Consistency (always read primary)"
        }
    }


# ─── Health ───────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {
        "status": "healthy",
        "designs": len(DESIGNS),
        "patterns": len(PATTERNS),
        "comparisons": len(COMPARISONS),
        "timestamp": datetime.utcnow().isoformat(),
        "day": "Day 45 — System Design Interview Patterns"
    }


@app.get("/")
def root() -> dict:
    return {
        "name": "System Design Simulator",
        "day": "Day 45 — Phase 5 Capstone",
        "docs": "/docs",
        "endpoints": {
            "designs": "GET /designs | GET /designs/{id}",
            "capacity": "POST /calculate/capacity",
            "latency": "GET /calculate/latency-budget",
            "numbers": "GET /calculate/numbers",
            "patterns": "GET /patterns | GET /patterns/search?q=... | GET /patterns/{id}",
            "tradeoffs": "GET /tradeoffs | GET /tradeoffs/{id}",
            "framework": "GET /framework",
            "cap": "GET /cap-theorem"
        }
    }