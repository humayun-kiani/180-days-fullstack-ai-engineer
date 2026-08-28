# ============================================================
# app/indexes.py
# Index configuration and management
# ============================================================

from app.database import db


def apply_optimized_indexes():
    """
    Apply all recommended indexes to the database.

    This is equivalent to running these in PostgreSQL:
    CREATE INDEX idx_tasks_status ON tasks(status);
    CREATE INDEX idx_tasks_priority ON tasks(priority);
    CREATE INDEX idx_tasks_status_priority ON tasks(status, priority);
    CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
    CREATE INDEX idx_tasks_owner_id ON tasks(owner_id);
    """
    print("\n  Applying optimized indexes...")

    indexes = [
        ("tasks", ["status"]),
        ("tasks", ["priority"]),
        ("tasks", ["owner_id"]),
        ("tasks", ["created_at"]),
    ]

    composite_indexes = [
        ("tasks", ["status", "priority"]),
        ("tasks", ["owner_id", "status"]),
    ]

    for table, columns in indexes:
        db.create_index(table, columns[0])

    for table, columns in composite_indexes:
        db.create_composite_index(table, columns)

    total = len(indexes) + len(composite_indexes)
    print(f"  ✅ Applied {total} indexes")
    return db.list_indexes()


def drop_all_indexes():
    """Remove all indexes (simulate baseline state)."""
    db._indexes.clear()
    db._composite_indexes.clear()
    print("  ✅ All indexes dropped")