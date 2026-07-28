# ============================================================
# routers/projects.py
# Project CRUD endpoints
# ============================================================

from fastapi import APIRouter, Query
from typing import Optional
import math

from src.models import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    PaginatedProjects, TaskResponse, ProjectStatus
)
from src.dependencies import CurrentUser, Database, Pagination
from src.exceptions import ProjectNotFoundError

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


@router.get("/", response_model=PaginatedProjects, summary="List projects")
def list_projects(
    status: Optional[ProjectStatus] = Query(None),
    pagination: Pagination = None,
    current_user: CurrentUser = None,
    db: Database = None
):
    items, total = db.get_projects(
        status=status.value if status else None,
        page=pagination.page,
        per_page=pagination.per_page
    )
    pages = math.ceil(total / pagination.per_page) if total > 0 else 1
    return PaginatedProjects(
        items=items, total=total,
        page=pagination.page, per_page=pagination.per_page, pages=pages
    )


@router.post("/", response_model=ProjectResponse, status_code=201, summary="Create project")
def create_project(
    project_data: ProjectCreate,
    current_user: CurrentUser = None,
    db: Database = None
):
    return db.create_project(project_data.model_dump())


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get project")
def get_project(
    project_id: int,
    current_user: CurrentUser = None,
    db: Database = None
):
    project = db.get_project(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)
    return project


@router.put("/{project_id}", response_model=ProjectResponse, summary="Update project")
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: CurrentUser = None,
    db: Database = None
):
    if not db.get_project(project_id):
        raise ProjectNotFoundError(project_id)
    return db.update_project(
        project_id,
        {k: v for k, v in project_data.model_dump().items() if v is not None}
    )


@router.delete("/{project_id}", status_code=204, summary="Delete project")
def delete_project(
    project_id: int,
    current_user: CurrentUser = None,
    db: Database = None
):
    if not db.get_project(project_id):
        raise ProjectNotFoundError(project_id)
    db.delete_project(project_id)
    return None


@router.get(
    "/{project_id}/tasks",
    response_model=list[TaskResponse],
    summary="Get project tasks"
)
def get_project_tasks(
    project_id: int,
    status: Optional[str] = Query(None),
    current_user: CurrentUser = None,
    db: Database = None
):
    if not db.get_project(project_id):
        raise ProjectNotFoundError(project_id)
    tasks, _ = db.get_tasks(
        project_id=project_id,
        status=status,
        per_page=100
    )
    return tasks