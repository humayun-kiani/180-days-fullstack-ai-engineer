# ============================================================
# src/api.py
# FastAPI application with full CRUD for expenses
# ============================================================

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from src.database import get_db, wait_for_db, create_tables
from src.models import Expense, Budget
from src.cache import (
    cache_get, cache_set, cache_delete,
    cache_delete_pattern, is_redis_available, CACHE_KEYS
)
import os


# ─────────────────────────────────────────
# PYDANTIC SCHEMAS (Request/Response)
# ─────────────────────────────────────────

class ExpenseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    category: str = Field(default="Other", max_length=50)
    note: Optional[str] = Field(default=None, max_length=500)


class ExpenseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=50)
    note: Optional[str] = None


class ExpenseResponse(BaseModel):
    id: int
    name: str
    amount: float
    category: str
    note: Optional[str]
    created_at: Optional[str]

    class Config:
        from_attributes = True


class BudgetUpdate(BaseModel):
    monthly_limit: float = Field(..., gt=0)


class StatsResponse(BaseModel):
    total_expenses: int
    total_amount: float
    average_amount: float
    max_amount: float
    min_amount: float
    by_category: dict


# ─────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────

app = FastAPI(
    title="Expense Tracker API",
    description="A containerized expense tracking API — Day 14 of 180-Day Roadmap",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS — allow frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # in production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────
# STARTUP EVENT
# ─────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Run on application startup."""
    print("\n" + "=" * 50)
    print("  EXPENSE TRACKER API STARTING UP")
    print("=" * 50)
    print(f"  Environment: {os.environ.get('APP_ENV', 'development')}")
    print(f"  Debug mode:  {os.environ.get('DEBUG', 'false')}")

    # Wait for database
    print("\n  Waiting for database...")
    wait_for_db()

    # Create tables
    print("  Creating/verifying database tables...")
    create_tables()

    # Check Redis
    redis_ok = is_redis_available()
    print(f"  Redis cache: {'✅ Connected' if redis_ok else '⚠️  Not available (caching disabled)'}")

    print("\n  ✅ API ready!")
    print("=" * 50)


# ─────────────────────────────────────────
# HEALTH CHECK ENDPOINTS
# ─────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for Docker health checks."""
    try:
        # Check database
        db.execute(from sqlalchemy import text; text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    redis_status = "healthy" if is_redis_available() else "unavailable"

    status = "healthy" if db_status == "healthy" else "unhealthy"

    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_status,
            "cache": redis_status
        },
        "version": "2.0.0"
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint — basic info."""
    return {
        "name": "Expense Tracker API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "day": "Day 14 of 180-Day Full Stack AI Engineer Roadmap"
    }


# ─────────────────────────────────────────
# EXPENSE ENDPOINTS
# ─────────────────────────────────────────

@app.get("/expenses", response_model=List[ExpenseResponse], tags=["Expenses"])
async def list_expenses(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get all expenses with optional category filter and pagination."""
    # Try cache first
    cache_key = CACHE_KEYS["all_expenses"] if not category else CACHE_KEYS["category"](category)
    cached = cache_get(cache_key)
    if cached:
        return cached

    # Query database
    query = db.query(Expense).filter(Expense.is_deleted == False)
    if category:
        query = query.filter(Expense.category.ilike(f"%{category}%"))

    expenses = query.order_by(Expense.created_at.desc()).offset(offset).limit(limit).all()
    result = [e.to_dict() for e in expenses]

    # Cache for 5 minutes
    cache_set(cache_key, result, ttl_seconds=300)

    return result


@app.get("/expenses/{expense_id}", response_model=ExpenseResponse, tags=["Expenses"])
async def get_expense(expense_id: int, db: Session = Depends(get_db)):
    """Get a specific expense by ID."""
    # Try cache
    cache_key = CACHE_KEYS["expense"](expense_id)
    cached = cache_get(cache_key)
    if cached:
        return cached

    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.is_deleted == False
    ).first()

    if not expense:
        raise HTTPException(status_code=404, detail=f"Expense {expense_id} not found")

    result = expense.to_dict()
    cache_set(cache_key, result, ttl_seconds=300)
    return result


@app.post("/expenses", response_model=ExpenseResponse, status_code=201, tags=["Expenses"])
async def create_expense(expense_data: ExpenseCreate, db: Session = Depends(get_db)):
    """Create a new expense."""
    expense = Expense(
        name=expense_data.name.strip().title(),
        amount=round(expense_data.amount, 2),
        category=expense_data.category.strip().title(),
        note=expense_data.note
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    # Invalidate list cache
    cache_delete_pattern("expenses:*")

    return expense.to_dict()


@app.put("/expenses/{expense_id}", response_model=ExpenseResponse, tags=["Expenses"])
async def update_expense(
    expense_id: int,
    update_data: ExpenseUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing expense."""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.is_deleted == False
    ).first()

    if not expense:
        raise HTTPException(status_code=404, detail=f"Expense {expense_id} not found")

    # Only update provided fields
    if update_data.name is not None:
        expense.name = update_data.name.strip().title()
    if update_data.amount is not None:
        expense.amount = round(update_data.amount, 2)
    if update_data.category is not None:
        expense.category = update_data.category.strip().title()
    if update_data.note is not None:
        expense.note = update_data.note

    expense.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(expense)

    # Invalidate caches
    cache_delete(CACHE_KEYS["expense"](expense_id))
    cache_delete_pattern("expenses:all*")

    return expense.to_dict()


@app.delete("/expenses/{expense_id}", status_code=204, tags=["Expenses"])
async def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    """Soft delete an expense."""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.is_deleted == False
    ).first()

    if not expense:
        raise HTTPException(status_code=404, detail=f"Expense {expense_id} not found")

    # Soft delete — mark as deleted but keep in DB
    expense.is_deleted = True
    expense.updated_at = datetime.utcnow()
    db.commit()

    # Invalidate caches
    cache_delete(CACHE_KEYS["expense"](expense_id))
    cache_delete_pattern("expenses:*")

    return None    # 204 No Content


# ─────────────────────────────────────────
# STATISTICS ENDPOINT
# ─────────────────────────────────────────

@app.get("/expenses/analytics/stats", response_model=StatsResponse, tags=["Analytics"])
async def get_statistics(db: Session = Depends(get_db)):
    """Get statistical summary of all expenses."""
    # Try cache
    cached = cache_get(CACHE_KEYS["stats"])
    if cached:
        return cached

    expenses = db.query(Expense).filter(Expense.is_deleted == False).all()

    if not expenses:
        return {
            "total_expenses": 0,
            "total_amount": 0,
            "average_amount": 0,
            "max_amount": 0,
            "min_amount": 0,
            "by_category": {}
        }

    amounts = [e.amount for e in expenses]

    # Category breakdown
    by_category = {}
    for expense in expenses:
        cat = expense.category
        if cat not in by_category:
            by_category[cat] = {"count": 0, "total": 0}
        by_category[cat]["count"] += 1
        by_category[cat]["total"] += expense.amount

    stats = {
        "total_expenses": len(expenses),
        "total_amount": round(sum(amounts), 2),
        "average_amount": round(sum(amounts) / len(amounts), 2),
        "max_amount": max(amounts),
        "min_amount": min(amounts),
        "by_category": {
            cat: {"count": v["count"], "total": round(v["total"], 2)}
            for cat, v in sorted(by_category.items(), key=lambda x: x[1]["total"], reverse=True)
        }
    }

    # Cache for 10 minutes
    cache_set(CACHE_KEYS["stats"], stats, ttl_seconds=600)

    return stats


# ─────────────────────────────────────────
# BUDGET ENDPOINT
# ─────────────────────────────────────────

@app.get("/budget", tags=["Budget"])
async def get_budget(db: Session = Depends(get_db)):
    """Get current monthly budget."""
    cached = cache_get(CACHE_KEYS["budget"])
    if cached:
        return cached

    budget = db.query(Budget).first()
    if not budget:
        budget = Budget(monthly_limit=50000)
        db.add(budget)
        db.commit()
        db.refresh(budget)

    result = budget.to_dict()
    cache_set(CACHE_KEYS["budget"], result, ttl_seconds=3600)
    return result


@app.put("/budget", tags=["Budget"])
async def update_budget(budget_data: BudgetUpdate, db: Session = Depends(get_db)):
    """Update monthly budget limit."""
    budget = db.query(Budget).first()
    if not budget:
        budget = Budget(monthly_limit=budget_data.monthly_limit)
        db.add(budget)
    else:
        budget.monthly_limit = budget_data.monthly_limit
        budget.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(budget)
    cache_delete(CACHE_KEYS["budget"])
    return budget.to_dict()