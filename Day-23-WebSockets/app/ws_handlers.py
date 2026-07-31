# ============================================================
# app/ws_handlers.py
# WebSocket message handlers — business logic for WS messages
# ============================================================

from fastapi import WebSocket
from datetime import datetime

from app.websocket_manager import TaskBoardManager
from app.fake_db import (
    get_task, get_tasks, complete_task,
    create_task, update_task_status, PROJECTS
)
from app.schemas import MessageType


async def handle_message(
    websocket: WebSocket,
    message: dict,
    manager: TaskBoardManager,
    username: str,
    user_id: int,
    role: str
) -> None:
    """
    Route incoming WebSocket messages to the correct handler.

    This is the main dispatch function — add new message types here.
    """
    msg_type = message.get("type")
    data = message.get("data", {})

    if msg_type == MessageType.PING:
        await handle_ping(websocket)

    elif msg_type == MessageType.SUBSCRIBE_PROJECT:
        await handle_subscribe(websocket, data, manager, username)

    elif msg_type == MessageType.UNSUBSCRIBE_PROJECT:
        await handle_unsubscribe(websocket, data, manager)

    elif msg_type == MessageType.COMPLETE_TASK:
        await handle_complete_task(websocket, data, manager, username, user_id)

    elif msg_type == MessageType.UPDATE_TASK:
        await handle_update_task(websocket, data, manager, username, role)

    elif msg_type == "create_task":
        await handle_create_task(websocket, data, manager, username)

    elif msg_type == "get_tasks":
        await handle_get_tasks(websocket, data)

    elif msg_type == "get_stats":
        stats = manager.get_stats()
        await websocket.send_json({
            "type": "stats",
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        })

    else:
        await websocket.send_json({
            "type": MessageType.ERROR,
            "data": {"message": f"Unknown message type: '{msg_type}'"},
            "timestamp": datetime.utcnow().isoformat()
        })


async def handle_ping(websocket: WebSocket) -> None:
    """Respond to ping with pong."""
    await websocket.send_json({
        "type": MessageType.PONG,
        "timestamp": datetime.utcnow().isoformat()
    })


async def handle_subscribe(
    websocket: WebSocket,
    data: dict,
    manager: TaskBoardManager,
    username: str
) -> None:
    """Subscribe to real-time updates for a project."""
    project_id = data.get("project_id")
    if not project_id or project_id not in PROJECTS:
        await websocket.send_json({
            "type": MessageType.ERROR,
            "data": {"message": f"Project {project_id} not found"}
        })
        return

    await manager.subscribe_project(websocket, project_id)

    # Send current task list for this project
    tasks = get_tasks(project_id=project_id)
    await websocket.send_json({
        "type": "task_list",
        "data": {
            "project_id": project_id,
            "project_name": PROJECTS[project_id]["name"],
            "tasks": tasks
        },
        "timestamp": datetime.utcnow().isoformat()
    })


async def handle_unsubscribe(
    websocket: WebSocket,
    data: dict,
    manager: TaskBoardManager
) -> None:
    """Unsubscribe from a project's updates."""
    project_id = data.get("project_id")
    if project_id:
        await manager.unsubscribe_project(websocket, project_id)
        await websocket.send_json({
            "type": "unsubscribed",
            "data": {"project_id": project_id}
        })


async def handle_complete_task(
    websocket: WebSocket,
    data: dict,
    manager: TaskBoardManager,
    username: str,
    user_id: int
) -> None:
    """Mark a task as complete and broadcast to all subscribers."""
    task_id = data.get("task_id")
    if not task_id:
        await websocket.send_json({
            "type": MessageType.ERROR,
            "data": {"message": "task_id is required"}
        })
        return

    task = complete_task(task_id, username)
    if not task:
        await websocket.send_json({
            "type": MessageType.ERROR,
            "data": {"message": f"Task {task_id} not found"}
        })
        return

    now = datetime.utcnow().isoformat()

    # Build broadcast message
    broadcast_msg = {
        "type": MessageType.TASK_COMPLETED,
        "data": {
            "task_id": task_id,
            "title": task["title"],
            "status": "done",
            "priority": task.get("priority", "medium"),
            "project_id": task.get("project_id"),
            "completed_by": username,
            "completed_by_id": user_id
        },
        "timestamp": now
    }

    project_id = task.get("project_id")

    if project_id:
        # Broadcast to all subscribers of this project
        sent = await manager.broadcast_to_project(project_id, broadcast_msg)
        print(f"  ✅ Task {task_id} completed by {username} → broadcast to {sent} clients")
    else:
        # Broadcast globally if no project
        await manager.broadcast_global(broadcast_msg)

    # Send confirmation to the completer
    await websocket.send_json({
        "type": "task_complete_confirmed",
        "data": {"task_id": task_id, "message": "Task marked as complete!"},
        "timestamp": now
    })

    # Send notification to task assignee if different
    assignee = task.get("assigned_to")
    if assignee and assignee != username:
        await manager.send_to_user(assignee, {
            "type": MessageType.NOTIFICATION,
            "data": {
                "title": "Task Completed",
                "message": f"{username} completed '{task['title']}'",
                "level": "success",
                "task_id": task_id
            },
            "timestamp": now
        })


async def handle_update_task(
    websocket: WebSocket,
    data: dict,
    manager: TaskBoardManager,
    username: str,
    role: str
) -> None:
    """Update task status and broadcast."""
    task_id = data.get("task_id")
    new_status = data.get("status")

    valid_statuses = ["pending", "in_progress", "done", "archived"]
    if not task_id or not new_status or new_status not in valid_statuses:
        await websocket.send_json({
            "type": MessageType.ERROR,
            "data": {"message": f"task_id and valid status required. Valid: {valid_statuses}"}
        })
        return

    task = update_task_status(task_id, new_status, username)
    if not task:
        await websocket.send_json({
            "type": MessageType.ERROR,
            "data": {"message": f"Task {task_id} not found"}
        })
        return

    now = datetime.utcnow().isoformat()
    broadcast_msg = {
        "type": MessageType.TASK_UPDATED,
        "data": {
            "task_id": task_id,
            "title": task["title"],
            "status": new_status,
            "priority": task.get("priority", "medium"),
            "project_id": task.get("project_id"),
            "updated_by": username
        },
        "timestamp": now
    }

    project_id = task.get("project_id")
    if project_id:
        await manager.broadcast_to_project(project_id, broadcast_msg)
    else:
        await manager.broadcast_global(broadcast_msg)


async def handle_create_task(
    websocket: WebSocket,
    data: dict,
    manager: TaskBoardManager,
    username: str
) -> None:
    """Create a new task and broadcast to project subscribers."""
    title = data.get("title", "").strip()
    project_id = data.get("project_id")
    priority = data.get("priority", "medium")

    if not title:
        await websocket.send_json({
            "type": MessageType.ERROR,
            "data": {"message": "Task title is required"}
        })
        return

    if project_id and project_id not in PROJECTS:
        await websocket.send_json({
            "type": MessageType.ERROR,
            "data": {"message": f"Project {project_id} not found"}
        })
        return

    task = create_task(title, project_id, priority, username)
    now = datetime.utcnow().isoformat()

    broadcast_msg = {
        "type": MessageType.TASK_CREATED,
        "data": {
            "task_id": task["id"],
            "title": task["title"],
            "status": "pending",
            "priority": task["priority"],
            "project_id": project_id,
            "created_by": username
        },
        "timestamp": now
    }

    if project_id:
        sent = await manager.broadcast_to_project(project_id, broadcast_msg)
        print(f"  🆕 Task '{title}' created by {username} → broadcast to {sent} clients")
    else:
        await manager.broadcast_global(broadcast_msg)

    await websocket.send_json({
        "type": "task_created_confirmed",
        "data": {"task": task},
        "timestamp": now
    })


async def handle_get_tasks(websocket: WebSocket, data: dict) -> None:
    """Send task list to the requesting client."""
    project_id = data.get("project_id")
    tasks = get_tasks(project_id=project_id)
    await websocket.send_json({
        "type": "task_list",
        "data": {"tasks": tasks, "project_id": project_id},
        "timestamp": datetime.utcnow().isoformat()
    })