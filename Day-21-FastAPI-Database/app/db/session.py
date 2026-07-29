# ============================================================
# app/db/session.py
# Database engine and session factory
# ============================================================

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,       # verify connection before using from pool
    pool_recycle=3600,        # recycle connections every hour
    echo=settings.DEBUG       # log SQL in debug mode
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False    # keep objects accessible after commit
)


def get_db() -> Session:
    """
    FastAPI dependency that provides a database session.

    Ensures session is properly closed after each request.
    Commits on success, rolls back on exception.

    Usage:
        @app.get("/tasks")
        def list_tasks(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()