# ============================================================
# src/database.py
# Database connection and session management
# ============================================================

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
import time

# Build database URL from environment variables
DB_URL = (
    f"postgresql://"
    f"{os.environ.get('POSTGRES_USER', 'expense_user')}:"
    f"{os.environ.get('POSTGRES_PASSWORD', 'password')}@"
    f"{os.environ.get('POSTGRES_HOST', 'localhost')}:"
    f"{os.environ.get('POSTGRES_PORT', '5432')}/"
    f"{os.environ.get('POSTGRES_DB', 'expense_tracker')}"
)

# Create engine
engine = create_engine(
    DB_URL,
    pool_pre_ping=True,     # check connection before using it
    pool_size=5,            # keep 5 connections in pool
    max_overflow=10,        # allow 10 extra connections when pool is full
    echo=os.environ.get("DEBUG", "false").lower() == "true"
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency function that provides a database session.
    Automatically closes the session when done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def wait_for_db(max_retries=30, delay=2):
    """
    Wait for database to be ready.
    Used during startup to wait for PostgreSQL health check.

    Args:
        max_retries (int): Maximum number of connection attempts.
        delay (int): Seconds between attempts.
    """
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"  ✅ Database connected successfully!")
            return True
        except OperationalError as e:
            if attempt == max_retries:
                print(f"  ❌ Could not connect to database after {max_retries} attempts.")
                raise
            print(f"  ⏳ Database not ready (attempt {attempt}/{max_retries}). "
                  f"Retrying in {delay}s...")
            time.sleep(delay)
    return False


def create_tables():
    """Create all database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
    print("  ✅ Database tables created/verified.")