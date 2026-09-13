# backend/app/models/audit.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class TaskAuditLog(Base):
    """
    Immutable audit trail for task changes.

    Every INSERT, UPDATE, DELETE on tasks is recorded here.
    Never delete from this table — it is a compliance record.
    """
    __tablename__ = "task_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    action: Mapped[str] = mapped_column(String(50))  # created/updated/deleted/status_changed
    changed_fields: Mapped[dict] = mapped_column(JSON, default=dict)
    old_values: Mapped[dict] = mapped_column(JSON, default=dict)
    new_values: Mapped[dict] = mapped_column(JSON, default=dict)
    user_name: Mapped[str] = mapped_column(String(255), default="")  # denormalized for fast reads
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )