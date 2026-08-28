# ============================================================
# app/database.py
# Simulated database with indexing support and realistic latency
# ============================================================

import asyncio
import time
import random
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Any


class SimulatedDatabase:
    """
    Simulates a PostgreSQL-like database with:
    - Realistic sequential scan latency
    - Index structures for fast lookups
    - Query statistics tracking
    - Slow query log
    """

    ROWS_PER_MS = 5000        # Rows scanned per millisecond (seq scan)
    INDEX_OVERHEAD_MS = 0.5   # Index lookup overhead
    NETWORK_LATENCY_MS = 1.0  # DB network round-trip

    def __init__(self):
        self._tasks: dict[str, dict] = {}
        self._users: dict[str, dict] = {}
        self._comments: dict[str, list] = defaultdict(list)

        # Index structures
        self._indexes: dict[str, dict] = {}
        self._composite_indexes: dict[str, Any] = {}

        # Query tracking
        self._query_log: list[dict] = []
        self._slow_query_threshold_ms = 50.0
        self._total_queries = 0

    # ── Data seeding ──────────────────────────────────────────

    def seed(self, n_tasks: int = 10000, n_users: int = 100):
        """Seed with realistic data."""
        statuses = ["pending", "in_progress", "done"]
        priorities = ["urgent", "high", "medium", "low"]
        owners = [f"user-{i:03d}" for i in range(n_users)]

        # Seed users
        for i in range(n_users):
            uid = f"user-{i:03d}"
            self._users[uid] = {
                "user_id": uid,
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "department": ["engineering", "product", "design"][i % 3]
            }

        # Seed tasks with realistic distribution
        base_date = datetime(2025, 1, 1)
        for i in range(n_tasks):
            task_id = f"task-{i:06d}"
            # Non-uniform distribution (more medium/low, fewer urgent)
            priority_weights = [0.05, 0.20, 0.50, 0.25]  # urgent, high, medium, low
            priority = random.choices(priorities, weights=priority_weights)[0]
            status_weights = [0.40, 0.35, 0.25]  # pending, in_progress, done
            status = random.choices(statuses, weights=status_weights)[0]

            days_offset = random.randint(0, 365)
            created_at = base_date + timedelta(days=days_offset,
                                              seconds=random.randint(0, 86400))

            self._tasks[task_id] = {
                "task_id": task_id,
                "title": f"Task {i}: {'Fix bug' if i%3==0 else 'Add feature' if i%3==1 else 'Update docs'}",
                "description": f"Description for task {i}",
                "status": status,
                "priority": priority,
                "owner_id": random.choice(owners),
                "created_at": created_at.isoformat(),
                "updated_at": (created_at + timedelta(hours=random.randint(0, 48))).isoformat(),
                "tags": random.sample(["backend", "frontend", "api", "db", "auth", "ci"], 2),
                "view_count": random.randint(0, 1000)
            }

            # Add 0-3 comments per task
            for _ in range(random.randint(0, 3)):
                self._comments[task_id].append({
                    "comment_id": str(uuid.uuid4())[:8],
                    "author_id": random.choice(owners),
                    "body": f"Comment on task {i}",
                    "created_at": created_at.isoformat()
                })

        print(f"  Seeded: {len(self._tasks):,} tasks, {len(self._users)} users")

    # ── Index management ──────────────────────────────────────

    def create_index(self, table: str, column: str) -> None:
        """Create a single-column index."""
        key = f"{table}.{column}"
        if table == "tasks":
            data = defaultdict(list)
            for row in self._tasks.values():
                data[row.get(column, "")].append(row)
            self._indexes[key] = dict(data)

    def create_composite_index(self, table: str, columns: list[str]) -> None:
        """Create a composite index."""
        key = f"{table}.{'+'.join(columns)}"
        if table == "tasks":
            data = defaultdict(list)
            for row in self._tasks.values():
                composite_key = tuple(row.get(c, "") for c in columns)
                data[composite_key].append(row)
            self._composite_indexes[key] = dict(data)

    def has_index(self, table: str, column: str) -> bool:
        return f"{table}.{column}" in self._indexes

    def has_composite_index(self, table: str, columns: list[str]) -> bool:
        return f"{table}.{'+'.join(columns)}" in self._composite_indexes

    def list_indexes(self) -> list[str]:
        return list(self._indexes.keys()) + list(self._composite_indexes.keys())

    # ── Query execution ───────────────────────────────────────

    async def execute(
        self,
        query_name: str,
        table: str,
        filters: dict | None = None,
        order_by: str | None = None,
        limit: int | None = None,
        offset: int | None = None
    ) -> tuple[list[dict], dict]:
        """
        Execute a simulated query. Returns (results, explain_plan).

        Automatically determines whether to use index or seq scan.
        """
        start = time.perf_counter()
        self._total_queries += 1
        filters = filters or {}

        # ── Determine execution strategy ──────────────────────
        all_rows = list(self._tasks.values()) if table == "tasks" else list(self._users.values())
        n_total = len(all_rows)

        # Check for composite index match
        composite_key_used = None
        if filters and len(filters) > 1:
            cols = list(filters.keys())
            ck = f"{table}.{'+'.join(cols)}"
            if ck in self._composite_indexes:
                composite_key_used = ck

        # Check for single-column index
        index_key_used = None
        if filters and not composite_key_used:
            for col in filters:
                if self.has_index(table, col):
                    index_key_used = f"{table}.{col}"
                    break

        # ── Execute with realistic latency ────────────────────
        if composite_key_used:
            # Composite index scan
            composite_vals = tuple(filters[c] for c in composite_key_used.split('.')[1].split('+'))
            candidates = self._composite_indexes[composite_key_used].get(composite_vals, [])
            rows_scanned = len(candidates)
            scan_type = "Composite Index Scan"
            extra_ms = self.INDEX_OVERHEAD_MS + 0.5

        elif index_key_used:
            # Single index scan
            col = index_key_used.split('.')[1]
            val = filters[col]
            candidates = self._indexes[index_key_used].get(val, [])
            # Apply remaining filters not covered by index
            remaining_filters = {k: v for k, v in filters.items() if k != col}
            if remaining_filters:
                candidates = [
                    r for r in candidates
                    if all(r.get(k) == v for k, v in remaining_filters.items())
                ]
            rows_scanned = len(candidates)
            scan_type = "Index Scan"
            extra_ms = self.INDEX_OVERHEAD_MS

        else:
            # Sequential scan
            candidates = all_rows
            if filters:
                candidates = [
                    r for r in all_rows
                    if all(r.get(k) == v for k, v in filters.items())
                ]
            rows_scanned = n_total
            scan_type = "Seq Scan"
            extra_ms = 0

        # Apply ORDER BY (simulate sorting cost)
        sort_ms = 0
        if order_by:
            col = order_by.lstrip("-")
            reverse = order_by.startswith("-")
            candidates = sorted(candidates, key=lambda r: r.get(col, ""), reverse=reverse)
            sort_ms = len(candidates) * 0.0001    # small sort cost

        # Apply OFFSET + LIMIT
        if offset:
            candidates = candidates[offset:]
        if limit:
            candidates = candidates[:limit]

        results = candidates

        # ── Calculate realistic latency ───────────────────────
        seq_scan_ms = rows_scanned / self.ROWS_PER_MS
        total_ms = self.NETWORK_LATENCY_MS + extra_ms + seq_scan_ms + sort_ms
        await asyncio.sleep(total_ms / 1000)

        elapsed = (time.perf_counter() - start) * 1000

        # ── Build EXPLAIN ANALYZE output ──────────────────────
        plan = {
            "query_name": query_name,
            "scan_type": scan_type,
            "table": table,
            "filters": filters,
            "rows_total": n_total,
            "rows_scanned": rows_scanned,
            "rows_returned": len(results),
            "sort": order_by,
            "limit": limit,
            "execution_time_ms": round(elapsed, 3),
            "index_used": composite_key_used or index_key_used or "none",
            "is_slow": elapsed > self._slow_query_threshold_ms
        }

        # Log the query
        self._query_log.append(plan)

        return results, plan

    # ── User join simulation ──────────────────────────────────

    async def execute_with_join(
        self,
        tasks: list[dict],
        join_type: str = "n_plus_1"
    ) -> tuple[list[dict], dict]:
        """Simulate join query — N+1 vs batched vs JOIN."""
        start = time.perf_counter()
        queries_made = 0

        if join_type == "n_plus_1":
            results = []
            for task in tasks:
                await asyncio.sleep(0.005)    # 5ms per query
                queries_made += 1
                user = self._users.get(task["owner_id"], {})
                results.append({**task, "owner_name": user.get("name", "Unknown")})

        elif join_type == "batch":
            owner_ids = list({t["owner_id"] for t in tasks})
            await asyncio.sleep(0.005)    # 1 query for all owners
            queries_made = 1
            user_map = {uid: self._users.get(uid, {}) for uid in owner_ids}
            results = [{
                **task,
                "owner_name": user_map.get(task["owner_id"], {}).get("name", "Unknown")
            } for task in tasks]

        else:  # "join"
            await asyncio.sleep(0.008)    # single slightly heavier JOIN query
            queries_made = 1
            results = [{
                **task,
                "owner_name": self._users.get(task["owner_id"], {}).get("name", "Unknown")
            } for task in tasks]

        elapsed = (time.perf_counter() - start) * 1000
        return results, {
            "join_type": join_type,
            "tasks": len(tasks),
            "queries_made": queries_made,
            "execution_time_ms": round(elapsed, 3)
        }

    # ── Stats and analysis ────────────────────────────────────

    def slow_query_log(self, threshold_ms: float = 50.0) -> list[dict]:
        return [q for q in self._query_log if q["execution_time_ms"] > threshold_ms]

    def query_stats(self) -> dict:
        if not self._query_log:
            return {"total": 0}
        times = [q["execution_time_ms"] for q in self._query_log]
        seq_scans = [q for q in self._query_log if q["scan_type"] == "Seq Scan"]
        import statistics as st
        return {
            "total_queries": len(self._query_log),
            "avg_ms": round(st.mean(times), 2),
            "max_ms": round(max(times), 2),
            "slow_queries": len(self.slow_query_log()),
            "seq_scans": len(seq_scans),
            "index_scans": len(self._query_log) - len(seq_scans)
        }

    def reset_logs(self):
        self._query_log.clear()
        self._total_queries = 0


# Global DB instance
db = SimulatedDatabase()