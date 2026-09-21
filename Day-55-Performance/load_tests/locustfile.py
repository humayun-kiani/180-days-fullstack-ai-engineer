# load_tests/locustfile.py
# Load test scenarios for TaskMind

import random
import uuid
from locust import HttpUser, task, between, events


class TaskMindUser(HttpUser):
    """
    Simulates a real TaskMind user.

    Task weights represent real usage patterns:
    - Users list tasks much more than they create
    - Search happens frequently
    - AI features are used occasionally
    """
    wait_time = between(0.5, 2.0)

    def on_start(self):
        """Register and log in when virtual user starts."""
        self.email = f"load_{uuid.uuid4().hex[:8]}@test.com"
        self.password = "loadtestpass123"
        self.task_ids = []
        self.headers = {}

        # Register
        r = self.client.post("/api/auth/register", json={
            "email": self.email,
            "name": "Load Test User",
            "password": self.password
        }, name="/api/auth/register")

        if r.status_code not in (200, 201):
            return

        # Login
        r = self.client.post("/api/auth/login", json={
            "email": self.email,
            "password": self.password
        }, name="/api/auth/login")

        if r.status_code == 200:
            token = r.json().get("access_token", "")
            self.headers = {"Authorization": f"Bearer {token}"}
            # Pre-create some tasks
            self._seed_tasks(5)

    def _seed_tasks(self, count: int):
        priorities = ["urgent", "high", "medium", "low"]
        for i in range(count):
            r = self.client.post("/api/tasks", json={
                "title": f"Seed task {i}: fix something important",
                "priority": random.choice(priorities)
            }, headers=self.headers, name="/api/tasks [seed]")
            if r.status_code == 201:
                self.task_ids.append(r.json()["id"])

    @task(10)
    def list_tasks(self):
        """Most common operation: browse task board."""
        self.client.get("/api/tasks", headers=self.headers, name="/api/tasks")

    @task(6)
    def search_tasks(self):
        """Search for tasks."""
        queries = ["fix", "update", "urgent", "bug", "feature", "test"]
        q = random.choice(queries)
        self.client.get(
            f"/api/search?q={q}",
            headers=self.headers,
            name="/api/search"
        )

    @task(3)
    def create_task(self):
        """Create a new task."""
        r = self.client.post("/api/tasks", json={
            "title": f"Load test task {random.randint(1, 10000)}",
            "priority": random.choice(["high", "medium", "low"]),
            "description": "Created during load test"
        }, headers=self.headers, name="/api/tasks [POST]")
        if r.status_code == 201:
            self.task_ids.append(r.json()["id"])

    @task(3)
    def update_task(self):
        """Update task status."""
        if not self.task_ids:
            return
        task_id = random.choice(self.task_ids)
        self.client.patch(
            f"/api/tasks/{task_id}",
            json={"status": random.choice(["pending", "in_progress", "done"])},
            headers=self.headers,
            name="/api/tasks/{id} [PATCH]"
        )

    @task(2)
    def view_stats(self):
        """View statistics dashboard."""
        self.client.get("/api/stats", headers=self.headers, name="/api/stats")

    @task(1)
    def ai_analyze(self):
        """Use AI to analyze a task (mocked without API key)."""
        self.client.post("/api/ai/analyze", json={
            "title": "Fix critical authentication bug",
            "description": "Users with special characters fail to log in"
        }, headers=self.headers, name="/api/ai/analyze")

    @task(1)
    def health_check(self):
        self.client.get("/health", name="/health")


class ReadHeavyUser(HttpUser):
    """
    Simulates a read-heavy user (monitoring dashboard, admin).
    Only reads, no writes.
    """
    wait_time = between(0.2, 1.0)
    weight = 3  # 3x less common than regular users

    def on_start(self):
        self.email = f"read_{uuid.uuid4().hex[:8]}@test.com"
        self.client.post("/api/auth/register", json={
            "email": self.email, "name": "Reader", "password": "readpass123"
        })
        r = self.client.post("/api/auth/login", json={
            "email": self.email, "password": "readpass123"
        })
        token = r.json().get("access_token", "") if r.status_code == 200 else ""
        self.headers = {"Authorization": f"Bearer {token}"}

    @task(5)
    def list_tasks(self):
        self.client.get("/api/tasks?per_page=20", headers=self.headers, name="/api/tasks")

    @task(3)
    def search(self):
        self.client.get("/api/search?q=fix", headers=self.headers, name="/api/search")

    @task(2)
    def stats(self):
        self.client.get("/api/stats", headers=self.headers, name="/api/stats")