# ============================================================
# seed.py
# Seed the database with sample data
# ============================================================
from app.core.security import hash_password
import hashlib
from datetime import datetime, timedelta
import sys

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def seed():
    from app.db.session import SessionLocal
    from app.db.base import Base
    from app.db.session import engine
    from app.db.models.user import User
    from app.db.models.project import Project
    from app.db.models.task import Task

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("  Database already has data. Skipping seed.")
            print("  To re-seed, drop and recreate the database.")
            return

        print("  Seeding database...")
        now = datetime.utcnow()

        # ── Users ──
users = [
    User(
        username="humayun",
        email="humayun@example.com",
        hashed_password=hash_password("password123"),    # bcrypt
        full_name="Humayun Kiani",
        role="admin"
    ),
    User(
        username="ali",
        email="ali@example.com",
        hashed_password=hash_password("password123"),
        full_name="Ali Hassan",
        role="editor"
    ),
    User(
        username="sara",
        email="sara@example.com",
        hashed_password=hash_password("password123"),
        full_name="Sara Ahmed",
        role="user"
    ),
]
        for u in users:
            db.add(u)
        db.flush()
        print(f"  ✅ {len(users)} users")

        # ── Projects ──
        projects_data = [
            Project(name="180-Day Roadmap",
                    description="Full Stack AI Engineer learning journey",
                    status="active", color="#3B82F6"),
            Project(name="Portfolio Website",
                    description="Personal portfolio site",
                    status="active", color="#10B981"),
            Project(name="Open Source",
                    description="OSS contributions",
                    status="paused", color="#8B5CF6"),
        ]
        for p in projects_data:
            db.add(p)
        db.flush()
        print(f"  ✅ {len(projects_data)} projects")

        # ── Tasks ──
        tasks_data = [
            Task(title="Complete Day 21 — FastAPI + DB",
                 description="Connect FastAPI to PostgreSQL",
                 priority="high", status="in_progress",
                 project_id=1, owner_id=1,
                 tags=["learning", "backend"],
                 estimated_hours=4.0,
                 due_date=now + timedelta(hours=8)),
            Task(title="Write Day 20 LinkedIn Post",
                 priority="medium", status="pending",
                 project_id=1, owner_id=1,
                 tags=["learning"],
                 due_date=now + timedelta(days=1)),
            Task(title="Review PR #15",
                 description="Auth module code review",
                 priority="urgent", status="pending",
                 project_id=2, owner_id=2,
                 tags=["review", "backend"],
                 estimated_hours=1.5,
                 due_date=now - timedelta(hours=3)),    # overdue!
            Task(title="Set up portfolio homepage",
                 priority="high", status="pending",
                 project_id=2, owner_id=1,
                 tags=["frontend"],
                 estimated_hours=6.0,
                 due_date=now + timedelta(days=5)),
            Task(title="Configure GitHub Actions",
                 priority="medium", status="pending",
                 project_id=2, owner_id=1,
                 tags=["devops"],
                 estimated_hours=2.0,
                 due_date=now + timedelta(days=7)),
            Task(title="Study PostgreSQL window functions",
                 priority="low", status="done",
                 project_id=1, owner_id=1,
                 tags=["learning", "database"],
                 estimated_hours=3.0, actual_hours=3.5,
                 completed_at=now - timedelta(days=1)),
            Task(title="Push Day 18 MongoDB project",
                 priority="medium", status="done",
                 project_id=1, owner_id=1,
                 tags=["learning"],
                 actual_hours=0.5,
                 completed_at=now - timedelta(days=2)),
            Task(title="Find OSS issue to fix",
                 priority="low", status="pending",
                 project_id=3, owner_id=1,
                 tags=["coding"],
                 due_date=now + timedelta(days=14)),
        ]
        for t in tasks_data:
            db.add(t)
        db.flush()
        print(f"  ✅ {len(tasks_data)} tasks")

        db.commit()
        print(f"\n  🎉 Database seeded successfully!")
        print(f"\n  Now run: uvicorn app.main:app --reload")
        print(f"  Then open: http://localhost:8000/docs")

    except Exception as e:
        db.rollback()
        print(f"  ❌ Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()