# ============================================================
# src/exceptions.py
# Custom exceptions and error handlers
# ============================================================

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError


# ─── Custom Exception Classes ───────────────────────────────

class TaskNotFoundError(Exception):
    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"Task {task_id} not found")


class ProjectNotFoundError(Exception):
    def __init__(self, project_id: int):
        self.project_id = project_id
        super().__init__(f"Project {project_id} not found")


class DuplicateTagError(Exception):
    def __init__(self, tag_name: str):
        self.tag_name = tag_name
        super().__init__(f"Tag '{tag_name}' already exists")


# ─── Exception Handlers ─────────────────────────────────────

def setup_exception_handlers(app):
    """Register all custom exception handlers on the app."""

    @app.exception_handler(TaskNotFoundError)
    async def task_not_found(request: Request, exc: TaskNotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                "error": "task_not_found",
                "message": f"Task with ID {exc.task_id} does not exist",
                "task_id": exc.task_id
            }
        )

    @app.exception_handler(ProjectNotFoundError)
    async def project_not_found(request: Request, exc: ProjectNotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                "error": "project_not_found",
                "message": f"Project with ID {exc.project_id} does not exist",
                "project_id": exc.project_id
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        """Custom validation error format."""
        errors = []
        for error in exc.errors():
            location = " → ".join(str(loc) for loc in error["loc"] if loc != "body")
            errors.append({
                "field": location,
                "message": error["msg"],
                "input": error.get("input", None)
            })
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_failed",
                "message": "Request data failed validation",
                "details": errors
            }
        )

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception):
        """Catch-all for unhandled exceptions."""
        print(f"UNHANDLED ERROR: {type(exc).__name__}: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred"
            }
        )