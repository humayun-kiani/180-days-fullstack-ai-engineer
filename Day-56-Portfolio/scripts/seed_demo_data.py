#!/usr/bin/env python3
# scripts/seed_demo_data.py
# Creates realistic demo data for screenshots/demos

import httpx
import random
import time

BASE_URL = "http://localhost:8000"

DEMO_TASKS = [
    {"title": "URGENT: Fix production login failure", "priority": "urgent",
     "description": "Users with special characters in passwords cannot authenticate"},
    {"title": "Security audit: review JWT token handling", "priority": "urgent",
     "description": "Quarterly security review of authentication system"},
    {"title": "Fix pagination bug on mobile board view", "priority": "high",
     "description": "Task cards overflow on iPhone SE (375px viewport)"},
    {"title": "Add rate limiting to AI endpoints", "priority": "high",
     "description": "Prevent API abuse — limit to 100 AI calls per user per hour"},
    {"title": "Implement cursor-based pagination", "priority": "high",
     "description": "Replace OFFSET pagination with cursor approach for large datasets"},
    {"title": "Add task due date reminders", "priority": "medium",
     "description": "Email/push notification 24h before task due date"},
    {"title": "Build team collaboration features", "priority": "medium",
     "description": "Allow sharing tasks and boards with team members"},
    {"title": "Add Slack integration for task notifications", "priority": "medium",
     "description": "Post task updates to designated Slack channel"},
    {"title": "Write API documentation", "priority": "medium",
     "description": "Complete OpenAPI spec with examples for all endpoints"},
    {"title": "Implement dark/light mode toggle", "priority": "medium",
     "description": "User preference with system default detection"},
    {"title": "Add CSV import functionality", "priority": "low",
     "description": "Import tasks from Jira, Asana, or generic CSV"},
    {"title": "Research WebAuthn for passwordless auth", "priority": "low",
     "description": "Investigate biometric/hardware key authentication"},
    {"title": "Update dependency versions", "priority": "low",
     "description": "Quarterly dependency audit and upgrade"},
    {"title": "Add task templates", "priority": "low",
     "description": "Pre-defined task sets for common workflows (sprint setup, code review)"},
    {"title": "Explore vector search for semantic task matching", "priority": "low",
     "description": "Use embeddings to find semantically similar tasks"},
]

DONE_TASKS = [
    {"title": "Deploy TaskMind v1.0 to production", "priority": "urgent"},
    {"title": "Set up PostgreSQL backups", "priority": "high"},
    {"title": "Add WebSocket real-time sync", "priority": "high"},
    {"title": "Implement JWT authentication", "priority": "high"},
    {"title": "Write 116 tests (82% coverage)", "priority": "medium"},
]


def seed(email: str = "demo@taskmind.dev", password: str = "demopassword123"):
    client = httpx.Client(base_url=BASE_URL)

    # Register
    r = client.post("/api/auth/register", json={
        "email": email, "name": "Humayun Kiani", "password": password
    })
    if r.status_code == 409:
        r = client.post("/api/auth/login", json={"email": email, "password": password})

    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print(f"  Logged in as {email}")
    print(f"  Creating {len(DEMO_TASKS)} pending/in-progress tasks...")

    # Create pending and in-progress tasks
    for i, task in enumerate(DEMO_TASKS):
        status = "in_progress" if i < 3 else "pending"
        r = client.post("/api/tasks", json=task, headers=headers)
        if r.status_code == 201:
            task_id = r.json()["id"]
            if status == "in_progress":
                client.patch(f"/api/tasks/{task_id}",
                             json={"status": status}, headers=headers)
        time.sleep(0.1)

    print(f"  Creating {len(DONE_TASKS)} completed tasks...")
    for task in DONE_TASKS:
        r = client.post("/api/tasks", json=task, headers=headers)
        if r.status_code == 201:
            task_id = r.json()["id"]
            client.patch(f"/api/tasks/{task_id}",
                         json={"status": "done"}, headers=headers)
        time.sleep(0.1)

    print(f"\n  ✅ Demo data created!")
    print(f"  Email:    {email}")
    print(f"  Password: {password}")
    print(f"  Token:    {token[:40]}...")
    print(f"\n  Open: http://localhost")


if __name__ == "__main__":
    seed()