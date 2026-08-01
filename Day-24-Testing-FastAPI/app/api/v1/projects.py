# ============================================================
# app/api/v1/projects.py
# Project endpoints
# ============================================================

import math
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.schemas.common import PaginatedResponse, MessageResponse
from app.schemas.task import TaskResponse
from app.crud import project_crud, task_crud
from app.api.deps import DB, CurrentUser, AdminUser, PageParams

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=PaginatedResponse[ProjectResponse])
def list_projects(
    status: Optional[str] = Query(None, regex="^(active|paused|completed|cancelled)$"),
    db: DB = None,
    current_user: CurrentUser = None,
    pagination: PageParams = None
):
    items, total = project_crud.get_multi_active(
        db, skip=pagination.skip, limit=pagination.limit, status=status
    )
    pages = math.ceil(total / pagination.per_page) if total > 0 else 1
    return PaginatedResponse(
        items=items, total=total,
        page=pagination.page, per_page=pagination.per_page,
        pages=pages, has_next=pagination.page < pages,
        has_prev=pagination.page > 1
    )


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    project_in: ProjectCreate,
    db: DB = None,
    current_user: CurrentUser = None
):
    return project_crud.create(db, project_in)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: DB = None,
    current_user: CurrentUser = None
):
    project = project_crud.get_with_tasks(db, project_id)
    if not project:
        raise HTTPException(404, f"Project {project_id} not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: DB = None,
    current_user: CurrentUser = None
):
    project = project_crud.get(db, project_id)
    if not project:
        raise HTTPException(404, f"Project {project_id} not found")
    return project_crud.update(db, project, project_in)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: DB = None,
    admin: AdminUser = None
):
    if not project_crud.get(db, project_id):
        raise HTTPException(404, f"Project {project_id} not found")
    project_crud.soft_delete(db, project_id)
    return None


@router.get("/{project_id}/tasks", response_model=list[TaskResponse])
def get_project_tasks(
    project_id: int,
    status: Optional[str] = Query(None),
    db: DB = None,
    current_user: CurrentUser = None
):
    if not project_crud.exists(db, project_id):
        raise HTTPException(404, f"Project {project_id} not found")
    tasks, _ = task_crud.get_multi_filtered(
        db, project_id=project_id, status=status, limit=100
    )
    return tasks


@router.get("/{project_id}/stats", response_model=dict)
def get_project_stats(
    project_id: int,
    db: DB = None,
    current_user: CurrentUser = None
):
    if not project_crud.exists(db, project_id):
        raise HTTPException(404, f"Project {project_id} not found")
    return project_crud.get_project_stats(db, project_id)