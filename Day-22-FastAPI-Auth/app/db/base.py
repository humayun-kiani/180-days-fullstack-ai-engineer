# ============================================================
# app/db/base.py
# SQLAlchemy declarative base — import ALL models here
# so Alembic can discover them for autogenerate
# ============================================================

from sqlalchemy.orm import DeclarativeBase, declared_attr
from datetime import datetime
from sqlalchemy import DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Auto-generate table name from class name (lowercase + s)."""
        return cls.__name__.lower() + "s"


# Import all models here so Alembic sees them
# The order matters if there are foreign key dependencies
from app.db.models.project import Project    # noqa: F401, E402
from app.db.models.user import User          # noqa: F401, E402
from app.db.models.task import Task          # noqa: F401, E402