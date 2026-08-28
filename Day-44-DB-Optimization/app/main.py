# ============================================================
# app/main.py
# Database Optimization API — Day 44
# ============================================================

import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.database import db
from app.profiler import profiler
from app.indexes import apply_optimized_indexes, drop_all_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 65)
    print("  Database Optimization & Query Performance — Day 44")
    print("=" * 65)

    print("\n  Seeding database...")
    db.seed(n_tasks=10000, n_users=100)
    print(f"\n  Docs: http://localhost:8000/docs\n")
    yield
    print("\n  Shutting down...")


app = FastAPI(
    title="DB Optimization & Query Profiler",
    description="""
## 🗄️ Database Optimization & Query Profiler — Day 44

Profile and optimize database queries with simulated EXPLAIN ANALYZE.

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /tasks` | List tasks (seq scan without indexes) |
| `POST /indexes/apply` | Apply optimized indexes |
| `POST /indexes/drop` | Drop all indexes (back to baseline) |
| `POST /benchmark` | Before/after comparison |
| `GET /profiler/report` | Query performance analysis |
| `GET /profiler/recommendations` | Index recommendations |
| `GET /demo/n-plus-1` | N+1 problem demonstration |
| `GET /demo/pagination` | OFFSET vs keyset pagination |

### Workflow
1. `GET /tasks` — see slow seq scan (no indexes)
2. `POST /indexes/apply` — add all recommended indexes
3. `GET /tasks` again — see fast index scan
4. `POST /benchmark` — full before/after comparison
5. `GET /profiler/report` — analyze query patterns
    """,
    version="1.0.0",
    lifespan=lifespan
)


# ─── Schemas ─────────────────────────────────────────────────

class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    priority: str = Field(default="medium", pattern="^(urgent|high|medium|low)$")
    status: str = Field(default="pending")
    owner_id: str = Field(default="user-001")


# ─── Task Query Endpoints ─────────────────────────────────────

@app.get(
    "/tasks",
    summary="List tasks — see seq scan vs index scan in action"
)
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    owner_id: Optional[str] = Query(None, description="Filter by owner"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> dict:
    """
    Query tasks. Check 'scan_type' in response — it shows:
    - 'Seq Scan': reading all rows (slow without index)
    - 'Index Scan': using index (fast)
    - 'Composite Index Scan': using multi-column index (fastest for multi-filter)
    """
    filters = {}
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    if owner_id:
        filters["owner_id"] = owner_id

    results, plan = await db.execute(
        query_name="list_tasks",
        table="tasks",
        filters=filters if filters else None,
        order_by="-created_at",
        limit=limit,
        offset=offset
    )
    profiler.record(plan)

    return {
        "tasks": results,
        "total_returned": len(results),
        "explain_plan": plan,
        "optimization_tip": (
            "Run POST /indexes/apply to add indexes and re-run this query"
            if plan["scan_type"] == "Seq Scan"
            else "✅ Using index — query is optimized"
        )
    }


@app.get("/tasks/{task_id}", summary="Get single task by ID")
async def get_task(task_id: str) -> dict:
    results, plan = await db.execute(
        "get_task_by_id",
        "tasks",
        filters={"task_id": task_id},
        limit=1
    )
    profiler.record(plan)

    if not results:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return {"task": results[0], "plan": plan}


# ─── Index Management ─────────────────────────────────────────

@app.post(
    "/indexes/apply",
    summary="Apply all optimized indexes"
)
async def apply_indexes() -> dict:
    """
    Apply recommended indexes. Run queries again to see speedup.

    Equivalent PostgreSQL:
    CREATE INDEX idx_tasks_status ON tasks(status);
    CREATE INDEX idx_tasks_priority ON tasks(priority);
    CREATE INDEX idx_tasks_status_priority ON tasks(status, priority);
    etc.
    """
    indexes = apply_optimized_indexes()
    db.reset_logs()
    profiler.reset()
    return {
        "message": "Indexes applied successfully",
        "indexes": indexes,
        "tip": "Now run GET /tasks?status=pending to see Index Scan instead of Seq Scan"
    }


@app.post(
    "/indexes/drop",
    summary="Drop all indexes (reset to baseline)"
)
async def drop_indexes() -> dict:
    """Remove all indexes to simulate un-optimized database."""
    drop_all_indexes()
    db.reset_logs()
    profiler.reset()
    return {
        "message": "All indexes dropped",
        "tip": "Run GET /tasks to see slow Seq Scans again"
    }


@app.get("/indexes", summary="List current indexes")
def list_indexes() -> dict:
    indexes = db.list_indexes()
    return {
        "indexes": indexes,
        "count": len(indexes),
        "status": "optimized" if indexes else "no indexes (will use Seq Scan)"
    }


# ─── Benchmarking ─────────────────────────────────────────────

@app.post(
    "/benchmark",
    summary="Full before/after optimization comparison"
)
async def benchmark() -> dict:
    """
    Run the same query workload before and after applying indexes.

    Clearly shows the performance improvement from proper indexing.
    """
    from app.optimizer import run_before_optimization, run_after_optimization

    # Drop indexes for baseline
    drop_all_indexes()
    before = await run_before_optimization()

    # Apply indexes and rerun
    after = await run_after_optimization()

    # Calculate improvement
    before_avg = before["stats"].get("avg_ms", 0)
    after_avg = after["stats"].get("avg_ms", 0)
    speedup = before_avg / after_avg if after_avg > 0 else 1

    return {
        "before": before,
        "after": after,
        "improvement": {
            "avg_latency_speedup": f"{speedup:.1f}x",
            "before_avg_ms": before_avg,
            "after_avg_ms": after_avg,
            "time_saved_ms": round(before["total_time_ms"] - after["total_time_ms"], 1),
            "slow_queries_before": before["stats"].get("slow_queries", 0),
            "slow_queries_after": after["stats"].get("slow_queries", 0)
        }
    }


# ─── Profiler Endpoints ───────────────────────────────────────

@app.get("/profiler/report", summary="Query performance analysis")
def profiler_report() -> dict:
    """
    Full query performance report — like pg_stat_statements.

    Shows: slowest queries, avg latency, seq scan count, recommendations.
    """
    return {
        "overall": profiler.overall_stats(),
        "by_query": profiler.summary_by_query(),
        "top_slow_queries": profiler.top_slow_queries(10),
        "index_recommendations": profiler.index_recommendations(),
        "slow_query_log": db.slow_query_log(threshold_ms=30)
    }


@app.get("/profiler/recommendations", summary="Recommended indexes")
def get_recommendations() -> dict:
    """Get specific CREATE INDEX statements to fix slow queries."""
    return {
        "recommendations": profiler.index_recommendations(),
        "current_indexes": db.list_indexes(),
        "slow_queries": len(db.slow_query_log()),
        "action": "POST /indexes/apply to apply all recommendations"
    }


@app.post("/profiler/reset", summary="Reset profiler stats")
def reset_profiler() -> dict:
    profiler.reset()
    db.reset_logs()
    return {"message": "Profiler stats reset"}


# ─── Demo Endpoints ───────────────────────────────────────────

@app.get(
    "/demo/n-plus-1",
    summary="Demonstrate N+1 problem and fix"
)
async def demo_n_plus_1(
    n_tasks: int = Query(30, ge=5, le=100)
) -> dict:
    """
    Side-by-side comparison of N+1 vs optimized join.

    N+1 makes 1 + N queries. Optimized makes 2 queries.
    """
    results, _ = await db.execute("get_tasks_for_join", "tasks", limit=n_tasks)

    # N+1 approach
    _, n1_info = await db.execute_with_join(results, "n_plus_1")

    # Optimized batch approach
    _, batch_info = await db.execute_with_join(results, "batch")

    speedup = n1_info["execution_time_ms"] / batch_info["execution_time_ms"]

    return {
        "tasks_fetched": n_tasks,
        "n_plus_1": {
            "queries_made": n1_info["queries_made"],
            "execution_time_ms": n1_info["execution_time_ms"],
            "description": f"1 task query + {n_tasks} user queries = {n_tasks+1} total"
        },
        "optimized_batch": {
            "queries_made": batch_info["queries_made"],
            "execution_time_ms": batch_info["execution_time_ms"],
            "description": "1 task query + 1 batch user query = 2 total"
        },
        "speedup": f"{speedup:.1f}x",
        "queries_saved": n1_info["queries_made"] - batch_info["queries_made"],
        "fix": "Use joinedload() in SQLAlchemy or SELECT ... JOIN in raw SQL"
    }


@app.get(
    "/demo/pagination",
    summary="OFFSET vs keyset pagination comparison"
)
async def demo_pagination(
    page_depth: int = Query(100, ge=1, le=5000,
                           description="Page number to fetch (shows OFFSET cost at depth)")
) -> dict:
    """
    Compare OFFSET pagination (slow at depth) vs keyset (fast always).

    OFFSET 10000: scans and discards 10000 rows!
    Keyset: jumps directly to cursor position.
    """
    page_size = 20
    offset_val = page_depth * page_size

    # OFFSET pagination
    start = time.perf_counter()
    results_offset, plan_offset = await db.execute(
        f"offset_page_{page_depth}",
        "tasks",
        order_by="-created_at",
        limit=page_size,
        offset=offset_val
    )
    ms_offset = (time.perf_counter() - start) * 1000

    # Keyset pagination (simulate by using limit without offset)
    # In real DB: WHERE created_at < :cursor ORDER BY created_at DESC LIMIT 20
    start = time.perf_counter()
    results_keyset, plan_keyset = await db.execute(
        f"keyset_page_{page_depth}",
        "tasks",
        order_by="-created_at",
        limit=page_size
        # No offset — keyset uses cursor from last page
    )
    ms_keyset = (time.perf_counter() - start) * 1000

    return {
        "page_depth": page_depth,
        "page_size": page_size,
        "offset_pagination": {
            "sql": f"SELECT * FROM tasks ORDER BY created_at DESC LIMIT {page_size} OFFSET {offset_val}",
            "rows_scanned": plan_offset["rows_scanned"],
            "rows_returned": len(results_offset),
            "execution_time_ms": round(ms_offset, 2),
            "problem": f"Scans and discards {offset_val:,} rows before returning results"
        },
        "keyset_pagination": {
            "sql": "SELECT * FROM tasks WHERE created_at < :cursor ORDER BY created_at DESC LIMIT 20",
            "rows_scanned": page_size,
            "rows_returned": page_size,
            "execution_time_ms": round(ms_keyset, 3),
            "advantage": "Always scans exactly page_size rows regardless of depth"
        },
        "speedup": f"{ms_offset/ms_keyset:.0f}x at page {page_depth}",
        "recommendation": "Use keyset pagination for infinite scroll and large datasets"
    }


# ─── Health ───────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {
        "status": "healthy",
        "database": {
            "tasks": len(db._tasks),
            "users": len(db._users),
            "indexes": len(db.list_indexes()),
            "query_stats": db.query_stats()
        },
        "timestamp": datetime.utcnow().isoformat(),
        "day": "Day 44 — Database Optimization"
    }


@app.get("/")
def root() -> dict:
    return {
        "name": "DB Optimization & Query Profiler",
        "day": "Day 44 — Database Optimization & Query Performance",
        "docs": "/docs",
        "workflow": [
            "1. GET /tasks?status=pending  → see Seq Scan (slow)",
            "2. POST /indexes/apply         → add all indexes",
            "3. GET /tasks?status=pending  → see Index Scan (fast)",
            "4. POST /benchmark             → full before/after comparison",
            "5. GET /profiler/report        → analyze query patterns",
            "6. GET /demo/n-plus-1          → see N+1 vs optimized join",
            "7. GET /demo/pagination        → OFFSET vs keyset comparison"
        ]
    }