# backend/app/services/task_service.py
import uuid
import math
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


async def create_task(db: AsyncSession, data: TaskCreate, owner_id: uuid.UUID) -> Task:
    task = Task(
        title=data.title,
        description=data.description,
        priority=data.priority,
        due_date=data.due_date,
        owner_id=owner_id
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task(db: AsyncSession, task_id: uuid.UUID, owner_id: uuid.UUID) -> Optional[Task]:
    result = await db.execute(
        select(Task).where(
            and_(Task.id == task_id, Task.owner_id == owner_id)
        )
    )
    return result.scalar_one_or_none()


async def list_tasks(
    db: AsyncSession,
    owner_id: uuid.UUID,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
) -> tuple[list[Task], int]:
    filters = [Task.owner_id == owner_id]
    if status:
        filters.append(Task.status == status)
    if priority:
        filters.append(Task.priority == priority)

    # Count total
    count_result = await db.execute(
        select(func.count(Task.id)).where(and_(*filters))
    )
    total = count_result.scalar_one()

    # Fetch page
    offset = (page - 1) * per_page
    result = await db.execute(
        select(Task)
        .where(and_(*filters))
        .order_by(Task.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    tasks = list(result.scalars().all())

    return tasks, total


async def update_task(
    db: AsyncSession,
    task: Task,
    data: TaskUpdate
) -> Task:
    updates = data.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(task, key, value)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task: Task) -> None:
    await db.delete(task)
    await db.commit()