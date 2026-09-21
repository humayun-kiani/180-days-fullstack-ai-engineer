# backend/benchmarks/benchmark_queries.py
# Standalone benchmark script — run directly with Python

import asyncio
import time
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func, or_, text

DB_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./benchmark.db"
)

engine = create_async_engine(DB_URL, echo=False)
AsyncSession_ = async_sessionmaker(engine, expire_on_commit=False)


def timer(label: str):
    """Context manager for timing code blocks."""
    class Timer:
        def __enter__(self):
            self.start = time.perf_counter()
            return self
        def __exit__(self, *args):
            self.elapsed_ms = (time.perf_counter() - self.start) * 1000
            print(f"  {label}: {self.elapsed_ms:.2f}ms")
    return Timer()


async def seed_data(session: AsyncSession, n: int = 100):
    """Seed benchmark data."""
    from app.db.database import Base
    from app.models.user import User
    from app.models.task import Task
    import uuid
    from datetime import datetime, timezone

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create one user
    user = User(
        id=uuid.uuid4(),
        email="bench@test.com",
        name="Bench User",
        password_hash="$2b$12$fake"
    )
    session.add(user)

    # Create N tasks
    priorities = ["urgent", "high", "medium", "low"]
    statuses = ["pending", "in_progress", "done"]
    now = datetime.now(timezone.utc)

    for i in range(n):
        task = Task(
            id=uuid.uuid4(),
            title=f"Task {i}: {'fix' if i % 3 == 0 else 'add' if i % 3 == 1 else 'update'} something",
            description=f"Description for task {i} with some extra content" if i % 2 == 0 else None,
            status=statuses[i % 3],
            priority=priorities[i % 4],
            owner_id=user.id,
            created_at=now,
            updated_at=now
        )
        session.add(task)

    await session.commit()
    print(f"  ✅ Seeded {n} tasks")
    return user.id


async def run_benchmarks():
    print("\n" + "=" * 60)
    print("  TASKMIND QUERY BENCHMARKS")
    print("=" * 60)

    async with AsyncSession_() as session:
        # Seed data
        print("\n📝 Seeding data...")
        user_id = await seed_data(session, n=500)

        print(f"\n📊 Benchmarking with 500 tasks (5 iterations each):\n")

        # ── Benchmark 1: Simple list ──
        print("1. Simple task listing (SELECT + ORDER BY)")
        from app.models.task import Task
        times = []
        for _ in range(5):
            start = time.perf_counter()
            await session.execute(
                select(Task)
                .where(Task.owner_id == user_id)
                .order_by(Task.created_at.desc())
                .limit(20)
            )
            times.append((time.perf_counter() - start) * 1000)
        print(f"  avg={sum(times)/len(times):.2f}ms  min={min(times):.2f}ms  max={max(times):.2f}ms")

        # ── Benchmark 2: ILIKE search ──
        print("\n2. ILIKE search (title + description)")
        times = []
        for _ in range(5):
            start = time.perf_counter()
            await session.execute(
                select(Task)
                .where(
                    Task.owner_id == user_id,
                    or_(Task.title.ilike("%fix%"), Task.description.ilike("%fix%"))
                )
                .limit(20)
            )
            times.append((time.perf_counter() - start) * 1000)
        print(f"  avg={sum(times)/len(times):.2f}ms  min={min(times):.2f}ms  max={max(times):.2f}ms")

        # ── Benchmark 3: Aggregation (stats) ──
        print("\n3. Aggregation query (stats dashboard)")
        from sqlalchemy import case
        times = []
        for _ in range(5):
            start = time.perf_counter()
            await session.execute(
                select(
                    func.count(Task.id).label("total"),
                    func.sum(case((Task.status == "done", 1), else_=0)).label("done"),
                    func.sum(case((Task.priority == "urgent", 1), else_=0)).label("urgent"),
                )
                .where(Task.owner_id == user_id)
            )
            times.append((time.perf_counter() - start) * 1000)
        print(f"  avg={sum(times)/len(times):.2f}ms  min={min(times):.2f}ms  max={max(times):.2f}ms")

        # ── Benchmark 4: Pagination (page 5) ──
        print("\n4. Pagination to page 5")
        times = []
        for _ in range(5):
            start = time.perf_counter()
            await session.execute(
                select(Task)
                .where(Task.owner_id == user_id)
                .order_by(Task.created_at.desc())
                .offset(80).limit(20)
            )
            times.append((time.perf_counter() - start) * 1000)
        print(f"  avg={sum(times)/len(times):.2f}ms  min={min(times):.2f}ms  max={max(times):.2f}ms")

        # ── Benchmark 5: Count query ──
        print("\n5. COUNT query (for pagination total)")
        times = []
        for _ in range(5):
            start = time.perf_counter()
            await session.execute(
                select(func.count(Task.id)).where(Task.owner_id == user_id)
            )
            times.append((time.perf_counter() - start) * 1000)
        print(f"  avg={sum(times)/len(times):.2f}ms  min={min(times):.2f}ms  max={max(times):.2f}ms")

    print("\n" + "=" * 60)
    print("  BENCHMARK COMPLETE")
    print("  Note: SQLite is faster on small data than PostgreSQL but")
    print("  doesn't scale the same way. Run with PostgreSQL in prod.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_benchmarks())