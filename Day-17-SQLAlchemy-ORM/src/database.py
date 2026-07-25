# ============================================================
# src/database.py
# Database engine, session factory, and utilities
# ============================================================

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

load_dotenv()

# ─── Engine Setup ───────────────────────────────────────────

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://blog_user:secure_password_here@localhost:5432/blog_orm"
)
DB_ECHO = os.environ.get("DB_ECHO", "false").lower() == "true"

engine = create_engine(
    DATABASE_URL,
    echo=DB_ECHO,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,         # verify connection before using
    pool_recycle=3600,          # recycle connections every hour
)

# ─── Session Factory ────────────────────────────────────────

SessionFactory = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,            # explicit flush control
    expire_on_commit=False,     # objects stay accessible after commit
)


def get_session() -> Session:
    """Create and return a new session."""
    return SessionFactory()


@contextmanager
def session_scope():
    """
    Context manager for database sessions.
    Automatically commits on success, rolls back on error.

    Usage:
        with session_scope() as session:
            session.add(user)
        # commits here

    """
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ─── Schema Management ──────────────────────────────────────

def create_all_tables():
    """Create all tables from model definitions."""
    from src.models import Base
    Base.metadata.create_all(bind=engine)
    print("  ✅ All tables created.")


def drop_all_tables():
    """Drop all tables (CAREFUL — deletes all data)."""
    from src.models import Base
    Base.metadata.drop_all(bind=engine)
    print("  ✅ All tables dropped.")


def test_connection() -> bool:
    """Test database connectivity."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT current_database(), current_user, version()"
            ))
            row = result.fetchone()
            print(f"  ✅ Connected: database={row[0]}, user={row[1]}")
            print(f"     {row[2].split(',')[0]}")
            return True
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return False