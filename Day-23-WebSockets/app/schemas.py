# ============================================================
# app/schemas.py
# Message schemas for WebSocket communication
# ============================================================

from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    # Authentication
    AUTHENTICATE = "authenticate"
    AUTHENTICATED = "authenticated"
    AUTH_ERROR = "auth_error"

    # Subscriptions
    SUBSCRIBE_PROJECT = "subscribe_project"
    UNSUBSCRIBE_PROJECT = "unsubscribe_project"
    SUBSCRIBED = "subscribed"

    # Task events (server → client)
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_DELETED = "task_deleted"

    # Task actions (client → server)
    COMPLETE_TASK = "complete_task"
    UPDATE_TASK = "update_task"

    # Presence
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    PRESENCE_LIST = "presence_list"

    # Notifications
    NOTIFICATION = "notification"

    # System
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    CONNECTED = "connected"


class WSMessage(BaseModel):
    """Base message model for all WebSocket messages."""
    type: MessageType
    data: Optional[Any] = None
    timestamp: str = ""

    def __init__(self, **data):
        if not data.get("timestamp"):
            data["timestamp"] = datetime.utcnow().isoformat()
        super().__init__(**data)

    def to_dict(self) -> dict:
        return self.model_dump()


class TaskEvent(BaseModel):
    """Task-related event data."""
    task_id: int
    title: str
    status: str
    priority: str
    project_id: Optional[int] = None
    updated_by: str
    project_name: Optional[str] = None


class NotificationData(BaseModel):
    """Notification event data."""
    title: str
    message: str
    level: str = "info"    # info, success, warning, error
    task_id: Optional[int] = None
    project_id: Optional[int] = None


class PresenceUser(BaseModel):
    """User presence data."""
    user_id: int
    username: str
    avatar_initial: str    # first letter of username
    joined_at: str