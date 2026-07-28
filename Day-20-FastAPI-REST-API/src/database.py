# ============================================================
# src/database.py
# In-memory database — simulates a real database for today
# No actual DB setup needed — focus is on API design
# ============================================================

from datetime import datetime, timedelta
from typing import Optional
from src.models import Priority, TaskStatus, ProjectStatus


class InMemoryDB:
    """
    Thread-safe in-memory database for the task manager.

    In a real application this would be SQLAlchemy + PostgreSQL.
    Today we use in-memory storage so you can focus on
    FastAPI concepts without database setup overhead.
    """

    def __init__(self):
        self._tasks: dict[int, dict] = {}
        self._projects: dict[int, dict] = {}
        self._tags: dict[int, dict] = {}
        self._task_counter = 0
        self._project_counter = 0
        self._tag_counter = 0
        self._seed_data()

    def _seed_data(self):
        """Seed with realistic sample data."""
        now = datetime.utcnow()

        # Projects
        projects_data = [
            {
                "name": "180-Day Roadmap",
                "description": "Full Stack AI Engineer learning journey",
                "status": "active",
                "color": "#3B82F6",
                "deadline": now + timedelta(days=160)
            },
            {
                "name": "Portfolio Website",
                "description": "Personal portfolio to showcase projects",
                "status": "active",
                "color": "#10B981",
                "deadline": now + timedelta(days=30)
            },
            {
                "name": "Open Source Contribution",
                "description": "Contribute to 3 open source Python projects",
                "status": "paused",
                "color": "#8B5CF6",
                "deadline": now + timedelta(days=90)
            },
        ]
        for p in projects_data:
            self.create_project(p)

        # Tags
        tags_data = [
            ("learning", "#3B82F6"),
            ("coding", "#10B981"),
            ("review", "#F59E0B"),
            ("urgent", "#EF4444"),
            ("backend", "#8B5CF6"),
            ("frontend", "#EC4899"),
            ("devops", "#14B8A6"),
            ("database", "#F97316"),
        ]
        for name, color in tags_data:
            self.create_tag({"name": name, "color": color})

        # Tasks
        tasks_data = [
            {
                "title": "Complete Day 20 — FastAPI Tutorial",
                "description": "Build the task management REST API",
                "priority": "high",
                "status": "in_progress",
                "project_id": 1,
                "tags": ["learning", "backend"],
                "estimated_hours": 4.0,
                "due_date": now + timedelta(hours=6)
            },
            {
                "title": "Write LinkedIn post for Day 19",
                "description": "Document Redis caching learnings",
                "priority": "medium",
                "status": "pending",
                "project_id": 1,
                "tags": ["learning"],
                "due_date": now + timedelta(days=1)
            },
            {
                "title": "Review PR #15 — Auth module",
                "description": "Review and provide feedback on authentication PR",
                "priority": "urgent",
                "status": "pending",
                "project_id": 2,
                "tags": ["review", "backend", "urgent"],
                "estimated_hours": 1.5,
                "due_date": now - timedelta(hours=2)    # overdue!
            },
            {
                "title": "Set up portfolio homepage",
                "description": "Create hero section and about page",
                "priority": "high",
                "status": "pending",
                "project_id": 2,
                "tags": ["frontend", "coding"],
                "estimated_hours": 6.0,
                "due_date": now + timedelta(days=5)
            },
            {
                "title": "Deploy to Vercel",
                "description": "Configure CI/CD and deploy portfolio",
                "priority": "medium",
                "status": "pending",
                "project_id": 2,
                "tags": ["devops"],
                "estimated_hours": 2.0,
                "due_date": now + timedelta(days=7)
            },
            {
                "title": "Study PostgreSQL advanced features",
                "description": "Window functions, CTEs, and query optimization",
                "priority": "low",
                "status": "done",
                "project_id": 1,
                "tags": ["learning", "database"],
                "estimated_hours": 3.0,
                "actual_hours": 3.5
            },
            {
                "title": "Push Day 18 to GitHub",
                "description": "Commit MongoDB project and update README",
                "priority": "medium",
                "status": "done",
                "project_id": 1,
                "tags": ["learning"],
                "actual_hours": 0.5
            },
            {
                "title": "Find open source issue to fix",
                "description": "Browse GitHub for beginner-friendly Python issues",
                "priority": "low",
                "status": "pending",
                "project_id": 3,
                "tags": ["coding"],
                "due_date": now + timedelta(days=14)
            },
        ]
        for t in tasks_data:
            self.create_task(t)

    # ─── TASKS ────────────────────────────────────────────────

    def create_task(self, data: dict) -> dict:
        self._task_counter += 1
        now = datetime.utcnow()
        task = {
            "id": self._task_counter,
            "title": data["title"],
            "description": data.get("description"),
            "priority": data.get("priority", "medium"),
            "status": data.get("status", "pending"),
            "project_id": data.get("project_id"),
            "due_date": data.get("due_date"),
            "tags": data.get("tags", []),
            "estimated_hours": data.get("estimated_hours"),
            "actual_hours": data.get("actual_hours"),
            "created_at": now,
            "updated_at": now
        }
        self._tasks[self._task_counter] = task
        return task

    def get_task(self, task_id: int) -> Optional[dict]:
        task = self._tasks.get(task_id)
        if task:
            return self._enrich_task(task.copy())
        return None

    def get_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        project_id: Optional[int] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        overdue: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        per_page: int = 20
    ) -> tuple[list[dict], int]:
        tasks = [self._enrich_task(t.copy()) for t in self._tasks.values()]

        # Filters
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        if priority:
            tasks = [t for t in tasks if t["priority"] == priority]
        if project_id:
            tasks = [t for t in tasks if t.get("project_id") == project_id]
        if tag:
            tasks = [t for t in tasks if tag.lower() in t.get("tags", [])]
        if search:
            q = search.lower()
            tasks = [t for t in tasks if q in t["title"].lower()
                     or q in (t.get("description") or "").lower()]
        if overdue is True:
            tasks = [t for t in tasks if t.get("is_overdue", False)]
        if overdue is False:
            tasks = [t for t in tasks if not t.get("is_overdue", False)]

        # Sort
        reverse = sort_order == "desc"
        valid_sort = ["created_at", "updated_at", "due_date",
                      "priority", "status", "title"]
        if sort_by not in valid_sort:
            sort_by = "created_at"

        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        status_order = {"in_progress": 0, "pending": 1, "done": 2, "archived": 3}

        def sort_key(t):
            if sort_by == "priority":
                return priority_order.get(t.get("priority", "medium"), 99)
            if sort_by == "status":
                return status_order.get(t.get("status", "pending"), 99)
            val = t.get(sort_by)
            if val is None:
                return datetime.min if "date" in sort_by else ""
            return val

        tasks.sort(key=sort_key, reverse=reverse)

        # Paginate
        total = len(tasks)
        start = (page - 1) * per_page
        end = start + per_page
        return tasks[start:end], total

    def update_task(self, task_id: int, data: dict) -> Optional[dict]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        for key, value in data.items():
            if value is not None:
                task[key] = value
        task["updated_at"] = datetime.utcnow()
        return self._enrich_task(task.copy())

    def delete_task(self, task_id: int) -> bool:
        if task_id not in self._tasks:
            return False
        del self._tasks[task_id]
        return True

    def _enrich_task(self, task: dict) -> dict:
        """Add computed fields to task."""
        # Add project name
        if task.get("project_id"):
            project = self._projects.get(task["project_id"])
            task["project_name"] = project["name"] if project else None
        else:
            task["project_name"] = None

        # Check if overdue
        due = task.get("due_date")
        if due and isinstance(due, datetime):
            task["is_overdue"] = (
                due < datetime.utcnow() and
                task.get("status") not in ("done", "archived")
            )
        else:
            task["is_overdue"] = False

        return task

    # ─── PROJECTS ─────────────────────────────────────────────

    def create_project(self, data: dict) -> dict:
        self._project_counter += 1
        now = datetime.utcnow()
        project = {
            "id": self._project_counter,
            "name": data["name"],
            "description": data.get("description"),
            "status": data.get("status", "active"),
            "color": data.get("color", "#3B82F6"),
            "deadline": data.get("deadline"),
            "created_at": now,
            "updated_at": now
        }
        self._projects[self._project_counter] = project
        return self._enrich_project(project.copy())

    def get_project(self, project_id: int) -> Optional[dict]:
        project = self._projects.get(project_id)
        if project:
            return self._enrich_project(project.copy())
        return None

    def get_projects(
        self,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> tuple[list[dict], int]:
        projects = [self._enrich_project(p.copy()) for p in self._projects.values()]
        if status:
            projects = [p for p in projects if p["status"] == status]
        total = len(projects)
        start = (page - 1) * per_page
        return projects[start:start + per_page], total

    def update_project(self, project_id: int, data: dict) -> Optional[dict]:
        project = self._projects.get(project_id)
        if not project:
            return None
        for key, value in data.items():
            if value is not None:
                project[key] = value
        project["updated_at"] = datetime.utcnow()
        return self._enrich_project(project.copy())

    def delete_project(self, project_id: int) -> bool:
        if project_id not in self._projects:
            return False
        # Unlink tasks
        for task in self._tasks.values():
            if task.get("project_id") == project_id:
                task["project_id"] = None
        del self._projects[project_id]
        return True

    def _enrich_project(self, project: dict) -> dict:
        project_tasks = [
            t for t in self._tasks.values()
            if t.get("project_id") == project["id"]
        ]
        total = len(project_tasks)
        completed = len([t for t in project_tasks if t["status"] == "done"])
        project["task_count"] = total
        project["completed_task_count"] = completed
        project["completion_pct"] = round(
            completed / total * 100 if total > 0 else 0, 1
        )
        return project

    # ─── TAGS ─────────────────────────────────────────────────

    def create_tag(self, data: dict) -> dict:
        # Check duplicate
        for tag in self._tags.values():
            if tag["name"] == data["name"].lower():
                return tag

        self._tag_counter += 1
        tag = {
            "id": self._tag_counter,
            "name": data["name"].lower().strip(),
            "color": data.get("color", "#6B7280"),
            "created_at": datetime.utcnow()
        }
        self._tags[self._tag_counter] = tag
        return self._enrich_tag(tag.copy())

    def get_tags(self) -> list[dict]:
        return [self._enrich_tag(t.copy()) for t in self._tags.values()]

    def get_tag(self, tag_id: int) -> Optional[dict]:
        tag = self._tags.get(tag_id)
        return self._enrich_tag(tag.copy()) if tag else None

    def _enrich_tag(self, tag: dict) -> dict:
        tag["task_count"] = len([
            t for t in self._tasks.values()
            if tag["name"] in t.get("tags", [])
        ])
        return tag

    def delete_tag(self, tag_id: int) -> bool:
        tag = self._tags.get(tag_id)
        if not tag:
            return False
        tag_name = tag["name"]
        for task in self._tasks.values():
            if tag_name in task.get("tags", []):
                task["tags"].remove(tag_name)
        del self._tags[tag_id]
        return True

    # ─── STATS ────────────────────────────────────────────────

    def get_stats(self) -> dict:
        tasks = list(self._tasks.values())
        now = datetime.utcnow()
        next_week = now + timedelta(days=7)

        by_status = {}
        by_priority = {}
        for t in tasks:
            by_status[t["status"]] = by_status.get(t["status"], 0) + 1
            by_priority[t["priority"]] = by_priority.get(t["priority"], 0) + 1

        done = by_status.get("done", 0)
        total = len(tasks)

        overdue = [
            t for t in tasks
            if t.get("due_date") and isinstance(t["due_date"], datetime)
            and t["due_date"] < now
            and t["status"] not in ("done", "archived")
        ]
        upcoming = [
            t for t in tasks
            if t.get("due_date") and isinstance(t["due_date"], datetime)
            and now <= t["due_date"] <= next_week
            and t["status"] not in ("done", "archived")
        ]

        projects = list(self._projects.values())
        projects_by_status = {}
        for p in projects:
            projects_by_status[p["status"]] = projects_by_status.get(p["status"], 0) + 1

        return {
            "total_tasks": total,
            "tasks_by_status": by_status,
            "tasks_by_priority": by_priority,
            "total_projects": len(projects),
            "projects_by_status": projects_by_status,
            "total_tags": len(self._tags),
            "completion_rate_pct": round(done / total * 100 if total > 0 else 0, 1),
            "overdue_tasks": len(overdue),
            "upcoming_tasks_7_days": len(upcoming)
        }


# Global DB instance (simulates a singleton connection)
db = InMemoryDB()