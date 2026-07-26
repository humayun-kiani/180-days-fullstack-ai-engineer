# ============================================================
# src/database.py
# MongoDB connection and database setup
# ============================================================

import os
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.environ.get("MONGODB_DB", "product_catalog")

# Global client instance
_client = None


def get_client() -> MongoClient:
    """Get or create MongoDB client (singleton)."""
    global _client
    if _client is None:
        _client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,    # 5 second timeout
            connectTimeoutMS=5000,
            maxPoolSize=10,                    # connection pool
            retryWrites=True
        )
    return _client


def get_database():
    """Get the application database."""
    return get_client()[MONGODB_DB]


def test_connection() -> dict:
    """Test MongoDB connection and return server info."""
    try:
        client = get_client()
        info = client.admin.command("serverStatus")
        return {
            "success": True,
            "version": info["version"],
            "uptime_hours": round(info["uptime"] / 3600, 1),
            "connections": info["connections"]["current"],
            "database": MONGODB_DB
        }
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def setup_indexes(db) -> None:
    """
    Create all necessary indexes for the product catalog.

    Called once on startup. MongoDB's createIndex is idempotent —
    safe to call even if indexes already exist.
    """
    products = db["products"]

    # Single field indexes for common filters
    products.create_index([("category", ASCENDING)])
    products.create_index([("brand", ASCENDING)])
    products.create_index([("price", ASCENDING)])
    products.create_index([("is_active", ASCENDING)])
    products.create_index([("created_at", DESCENDING)])

    # Compound indexes for common query patterns
    products.create_index([
        ("category", ASCENDING),
        ("price", ASCENDING)
    ])
    products.create_index([
        ("category", ASCENDING),
        ("is_active", ASCENDING),
        ("price", ASCENDING)
    ])

    # Unique index for SKU
    products.create_index([("sku", ASCENDING)], unique=True, sparse=True)

    # Text index for full-text search
    products.create_index([
        ("name", TEXT),
        ("description", TEXT),
        ("brand", TEXT),
        ("tags", TEXT)
    ], name="product_text_search")

    # Rating index (for sorting by rating)
    products.create_index([("rating.average", DESCENDING)])

    # Reviews collection indexes
    reviews = db["reviews"]
    reviews.create_index([("product_id", ASCENDING)])
    reviews.create_index([("user_id", ASCENDING)])
    reviews.create_index([("created_at", DESCENDING)])

    print("  ✅ Database indexes created.")


def close_connection() -> None:
    """Close the MongoDB connection."""
    global _client
    if _client:
        _client.close()
        _client = None