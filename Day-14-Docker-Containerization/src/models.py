# ============================================================
# src/models.py
# SQLAlchemy database models
# ============================================================

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float,
    DateTime, Boolean, Text, ForeignKey
)
from sqlalchemy.orm import relationship
from src.database import Base


class Expense(Base):
    """Expense model — maps to 'expenses' table in PostgreSQL."""

    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False, default="Other")
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    def to_dict(self):
        """Convert expense to dictionary for JSON response."""
        return {
            "id": self.id,
            "name": self.name,
            "amount": self.amount,
            "category": self.category,
            "note": self.note or "",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }

    def __repr__(self):
        return f"<Expense(id={self.id}, name='{self.name}', amount={self.amount})>"


class Budget(Base):
    """Budget model — stores monthly budget settings."""

    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True)
    monthly_limit = Column(Float, nullable=False, default=50000)
    currency = Column(String(10), default="PKR")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "monthly_limit": self.monthly_limit,
            "currency": self.currency,
        }