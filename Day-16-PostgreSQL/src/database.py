# ============================================================
# src/database.py
# PostgreSQL connection management
# ============================================================

import os
import psycopg2
import psycopg2.extras
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Connection configuration
DB_CONFIG = {
    "host":     os.environ.get("POSTGRES_HOST", "localhost"),
    "port":     int(os.environ.get("POSTGRES_PORT", 5432)),
    "dbname":   os.environ.get("POSTGRES_DB", "blog_platform"),
    "user":     os.environ.get("POSTGRES_USER", "blog_user"),
    "password": os.environ.get("POSTGRES_PASSWORD", ""),
}

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def get_connection():
    """
    Get a PostgreSQL connection.

    Returns:
        psycopg2 connection with DictCursor factory.
    """
    conn = psycopg2.connect(
        **DB_CONFIG,
        cursor_factory=psycopg2.extras.RealDictCursor  # rows as dicts
    )
    return conn


def run_migrations(conn):
    """
    Apply all pending SQL migration files.

    Args:
        conn: psycopg2 connection.
    """
    cursor = conn.cursor()

    # Create migrations table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version     INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            applied_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    conn.commit()

    # Get applied versions
    cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
    applied = {row["version"] for row in cursor.fetchall()}

    # Find and apply pending migrations
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    applied_count = 0

    for filepath in migration_files:
        version = int(filepath.stem.split("_")[0])
        if version not in applied:
            print(f"  Applying migration {filepath.name}...")
            try:
                sql = filepath.read_text()
                cursor.execute(sql)
                conn.commit()
                print(f"  ✅ Migration {version} applied.")
                applied_count += 1
            except Exception as e:
                conn.rollback()
                print(f"  ❌ Migration {version} failed: {e}")
                raise

    if applied_count == 0:
        print("  ✅ All migrations already applied.")
    else:
        print(f"  ✅ Applied {applied_count} new migration(s).")

    return applied_count


def test_connection():
    """Test database connection and return server info."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version(), current_database(), current_user")
        row = cursor.fetchone()
        conn.close()
        return {
            "success": True,
            "version": row["version"].split(",")[0],
            "database": row["current_database"],
            "user": row["current_user"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}