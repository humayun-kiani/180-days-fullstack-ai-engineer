# backend/app/db/init_db.py
"""Initialize database tables."""

from app.db.database import engine, Base
from app.models.user import User  # noqa — needed for table creation
from app.models.task import Task  # noqa


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  ✅ Database tables created")