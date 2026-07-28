# Day 20 — FastAPI: Building Production REST APIs

> **Phase 2 — Web Development** | Week 4 | Day 20 of 180

---

## 📌 What I Learned Today

- What REST means — resources as nouns, HTTP methods as verbs
- HTTP status codes: 200, 201, 204, 400, 401, 403, 404, 409, 422, 500
- FastAPI setup: creating app, running with uvicorn
- Auto-generated Swagger UI — test endpoints directly in browser
- Path parameters with type validation: `{task_id: int}`
- Query parameters with defaults, validation, and regex
- Path() and Query() for advanced parameter constraints
- Pydantic BaseModel for request validation
- Field() with constraints: min_length, max_length, ge, le, regex, pattern
- @validator decorators for custom validation logic
- Response models — control exactly what gets returned
- Optional fields and default values in Pydantic
- Enum types for controlled string values
- Dependency injection with Depends()
- Chained dependencies (require_admin depends on get_current_user)
- Annotated type aliases for cleaner function signatures
- APIRouter for organizing endpoints into logical groups
- app.include_router() to assemble the full API
- Middleware with @app.middleware("http")
- CORSMiddleware for allowing frontend requests
- Custom exception handlers with @app.exception_handler()
- HTTPException for standard HTTP errors
- BackgroundTasks for fire-and-forget async work
- lifespan context manager for startup/shutdown
- Returning None from 204 No Content endpoints

## 🔨 Project Built

**Task Manager REST API** — Complete production-quality API:

- 16 endpoints across Tasks, Projects, Tags, and System
- Full CRUD with correct HTTP methods and status codes
- Advanced task filtering: status, priority, project, tag, search, overdue
- Sorting: by created_at, updated_at, due_date, priority, status, title
- Pagination with has_next, has_prev, total pages
- POST /tasks → 201 Created with created task
- PATCH /tasks/{id}/complete → quick-complete shortcut
- GET /tasks/overdue/list → overdue tasks endpoint
- GET /projects/{id}/tasks → nested resource endpoint
- DELETE /tags/{id} requires admin role
- Custom validation errors (422) with field-level detail
- Background task notification on create, complete, delete
- Request timing middleware adds X-Process-Time-Ms header
- Request ID middleware adds X-Request-ID header
- In-memory DB pre-seeded with 8 tasks, 3 projects, 8 tags
- Full OpenAPI spec at /openapi.json
- Interactive docs at /docs (Swagger) and /redoc (ReDoc)

## 🚀 How to Run

```bash
cd Day-20-FastAPI-REST-API
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn src.main:app --reload

# Open: http://localhost:8000/docs
```

## 🧠 Key FastAPI Patterns

| Pattern        | Code                                                  |
| -------------- | ----------------------------------------------------- |
| Route          | `@app.get("/tasks/{id}")`                             |
| Path param     | `task_id: int = Path(gt=0)`                           |
| Query param    | `limit: int = Query(20, ge=1, le=100)`                |
| Request body   | `task: TaskCreate` (Pydantic model)                   |
| Response model | `response_model=TaskResponse`                         |
| Dependency     | `user: CurrentUser = Depends(get_current_user)`       |
| Router         | `router = APIRouter(prefix="/tasks", tags=["Tasks"])` |
| HTTP error     | `raise HTTPException(status_code=404, detail="...")`  |
| Background     | `background_tasks.add_task(fn, arg1, arg2)`           |
| 204 response   | `return None` with `status_code=204`                  |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
