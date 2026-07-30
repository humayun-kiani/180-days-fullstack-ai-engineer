# Add these imports to existing tasks.py:
from app.api.deps import DB, CurrentUser, AdminUser, PageParams
# CurrentUser is now a real User ORM object, not a dict!

# Update the complete_task endpoint:
@router.patch("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    actual_hours: Optional[float] = Query(None, ge=0),
    db: DB = None,
    current_user: CurrentUser = None    # ← now a real User object
):
    task = task_crud.get_active(db, task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    if task.status == "done":
        raise HTTPException(409, "Task is already completed")

    completed = task_crud.complete_task(db, task, actual_hours)

    background_tasks.add_task(
        log_task_event,
        task.id, task.title, "completed ✅",
        current_user.username    # ← real username from DB
    )
    return completed


# Update delete with real role check:
@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    hard: bool = Query(False),
    db: DB = None,
    current_user: CurrentUser = None
):
    task = task_crud.get_active(db, task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")

    if hard:
        if current_user.role != "admin":    # ← check real role
            raise HTTPException(403, "Hard delete requires admin")
        task_crud.delete(db, task_id)
    else:
        task_crud.soft_delete(db, task)

    background_tasks.add_task(
        log_task_event,
        task_id, task.title,
        f"{'hard' if hard else 'soft'} deleted",
        current_user.username    # ← real username
    )
    return None