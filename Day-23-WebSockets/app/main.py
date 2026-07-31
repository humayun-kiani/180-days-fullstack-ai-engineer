# ============================================================
# app/main.py
# FastAPI application with WebSocket support
# ============================================================

import json
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional

from app.websocket_manager import manager
from app.ws_auth import authenticate_websocket
from app.ws_handlers import handle_message
from app.fake_db import get_tasks, PROJECTS


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("  Real-Time Task Board — WebSocket Server")
    print("  Day 23 — 180-Day Full Stack AI Engineer Roadmap")
    print(f"  App:      http://localhost:8000")
    print(f"  WS:       ws://localhost:8000/ws?token=demo_token_humayun")
    print(f"  Docs:     http://localhost:8000/docs")
    print("=" * 60 + "\n")
    yield
    print("\n  Server shutting down...")


app = FastAPI(
    title="Real-Time Task Board",
    description="""
## Real-Time Task Board — WebSocket Demo

This API demonstrates **real-time WebSocket communication** for a task management board.

### WebSocket Endpoint
Connect to: `ws://localhost:8000/ws?token=<demo_token>`

**Demo Tokens:**
- `demo_token_humayun` — admin user
- `demo_token_ali` — editor user
- `demo_token_sara` — regular user

### Message Types (Client → Server)
| Type | Data | Description |
|------|------|-------------|
| `subscribe_project` | `{"project_id": 1}` | Subscribe to project updates |
| `complete_task` | `{"task_id": 1}` | Mark task as done |
| `update_task` | `{"task_id": 1, "status": "in_progress"}` | Update task status |
| `create_task` | `{"title": "...", "project_id": 1, "priority": "high"}` | Create new task |
| `get_tasks` | `{"project_id": 1}` | Get task list |
| `get_stats` | `{}` | Get connection stats |
| `ping` | `{}` | Heartbeat |

### Message Types (Server → Client)
Events are broadcast to all subscribers of the affected project.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Serve static files (the HTML client)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── HTTP Endpoints ─────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the WebSocket demo client."""
    with open("static/index.html") as f:
        return f.read()


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "connections": manager.get_stats()["total_connections"],
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/stats")
def api_stats():
    """Get current WebSocket server statistics."""
    return manager.get_stats()


@app.get("/api/tasks")
def api_tasks(project_id: Optional[int] = Query(None)):
    """REST endpoint to get tasks (complement to WebSocket)."""
    return {"tasks": get_tasks(project_id=project_id)}


@app.get("/api/projects")
def api_projects():
    return {"projects": list(PROJECTS.values())}


# ─── WebSocket Endpoint ─────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    Main WebSocket endpoint for the real-time task board.

    Connection URL: ws://localhost:8000/ws?token=<your_token>

    Flow:
    1. Accept WebSocket connection
    2. Authenticate user (via query token or first message)
    3. Register in connection manager
    4. Enter message loop
    5. Handle disconnect on exit
    """

    # STEP 1: Accept the WebSocket upgrade
    await websocket.accept()

    # STEP 2: Authenticate
    user = await authenticate_websocket(websocket, token=token)
    if not user:
        return    # Connection already closed in authenticate_websocket

    username = user["username"]
    user_id = user["id"]
    role = user["role"]

    # STEP 3: Register in manager
    client = await manager.connect(websocket, user_id, username, role)

    # STEP 4: Send welcome message
    await websocket.send_json({
        "type": "connected",
        "data": {
            "message": f"Welcome to the Real-Time Task Board, {username}!",
            "user_id": user_id,
            "username": username,
            "role": role,
            "total_connections": len(manager._clients),
            "projects": list(PROJECTS.values()),
            "hint": "Subscribe to a project: {\"type\": \"subscribe_project\", \"data\": {\"project_id\": 1}}"
        },
        "timestamp": datetime.utcnow().isoformat()
    })

    # Notify all other clients of new connection
    await manager.broadcast_global(
        {
            "type": "notification",
            "data": {
                "title": "User Connected",
                "message": f"{username} joined the board",
                "level": "info"
            },
            "timestamp": datetime.utcnow().isoformat()
        },
        exclude=websocket
    )

    # STEP 5: Message loop
    try:
        while True:
            # Wait for next message from client
            raw_message = await websocket.receive_text()

            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Invalid JSON"},
                    "timestamp": datetime.utcnow().isoformat()
                })
                continue

            # Route message to appropriate handler
            await handle_message(
                websocket=websocket,
                message=message,
                manager=manager,
                username=username,
                user_id=user_id,
                role=role
            )

    except WebSocketDisconnect as e:
        # STEP 6: Clean up on disconnect
        print(f"  🔌 {username} disconnected (code: {e.code})")
        departed_client = await manager.disconnect(websocket)

        # Notify others
        await manager.broadcast_global({
            "type": "notification",
            "data": {
                "title": "User Disconnected",
                "message": f"{username} left the board",
                "level": "info"
            },
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        print(f"  ❌ Unexpected error for {username}: {type(e).__name__}: {e}")
        await manager.disconnect(websocket)