# ============================================================
# app/websocket_manager.py
# Central WebSocket connection and room management
# ============================================================

import asyncio
from collections import defaultdict
from datetime import datetime
from fastapi import WebSocket
from typing import Optional


class ClientInfo:
    """Information about a connected WebSocket client."""

    def __init__(
        self,
        websocket: WebSocket,
        user_id: int,
        username: str,
        role: str
    ):
        self.websocket = websocket
        self.user_id = user_id
        self.username = username
        self.role = role
        self.connected_at = datetime.utcnow().isoformat()
        self.subscribed_projects: set[int] = set()
        self.last_ping = datetime.utcnow()

    def to_presence_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "avatar_initial": self.username[0].upper(),
            "joined_at": self.connected_at
        }


class TaskBoardManager:
    """
    Manages all WebSocket connections for the task board.

    Features:
    - Global connection tracking
    - Project-based rooms (subscribe/unsubscribe)
    - Presence tracking per project
    - Broadcast to all or to specific rooms
    - Automatic cleanup of dead connections
    """

    def __init__(self):
        # All active clients: websocket → ClientInfo
        self._clients: dict[WebSocket, ClientInfo] = {}

        # Project rooms: project_id → set of websockets
        self._project_rooms: dict[int, set[WebSocket]] = defaultdict(set)

    # ─── Connection Lifecycle ────────────────────────────────

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        username: str,
        role: str
    ) -> ClientInfo:
        """Register a new authenticated WebSocket connection."""
        client = ClientInfo(websocket, user_id, username, role)
        self._clients[websocket] = client

        print(f"  🟢 [{username}] connected | Total: {len(self._clients)}")
        return client

    async def disconnect(self, websocket: WebSocket) -> Optional[ClientInfo]:
        """Remove a client and clean up room memberships."""
        client = self._clients.pop(websocket, None)
        if client:
            # Leave all project rooms
            for project_id in client.subscribed_projects.copy():
                await self._leave_project_room(websocket, project_id, client)

            print(f"  🔴 [{client.username}] disconnected | Total: {len(self._clients)}")
        return client

    # ─── Room Management ─────────────────────────────────────

    async def subscribe_project(
        self,
        websocket: WebSocket,
        project_id: int
    ) -> None:
        """Add client to a project room and notify others."""
        client = self._clients.get(websocket)
        if not client:
            return

        if project_id in client.subscribed_projects:
            return    # already subscribed

        client.subscribed_projects.add(project_id)
        self._project_rooms[project_id].add(websocket)

        print(f"  📌 [{client.username}] subscribed to project {project_id}")

        # Notify other room members of the new presence
        await self.broadcast_to_project(
            project_id=project_id,
            message={
                "type": "user_joined",
                "data": {
                    "user": client.to_presence_dict(),
                    "project_id": project_id,
                    "room_size": len(self._project_rooms[project_id])
                }
            },
            exclude=websocket
        )

        # Send current presence list to the new subscriber
        presence_list = self._get_project_presence(project_id)
        await self._send(websocket, {
            "type": "presence_list",
            "data": {
                "project_id": project_id,
                "users": presence_list
            }
        })

        # Confirm subscription
        await self._send(websocket, {
            "type": "subscribed",
            "data": {
                "project_id": project_id,
                "message": f"Subscribed to project {project_id} updates"
            }
        })

    async def unsubscribe_project(
        self,
        websocket: WebSocket,
        project_id: int
    ) -> None:
        """Remove client from a project room."""
        client = self._clients.get(websocket)
        if not client:
            return
        await self._leave_project_room(websocket, project_id, client)

    async def _leave_project_room(
        self,
        websocket: WebSocket,
        project_id: int,
        client: ClientInfo
    ) -> None:
        """Internal: leave a project room and notify others."""
        client.subscribed_projects.discard(project_id)
        self._project_rooms[project_id].discard(websocket)

        # Notify remaining room members
        if self._project_rooms[project_id]:
            await self.broadcast_to_project(
                project_id=project_id,
                message={
                    "type": "user_left",
                    "data": {
                        "username": client.username,
                        "user_id": client.user_id,
                        "project_id": project_id,
                        "room_size": len(self._project_rooms[project_id])
                    }
                }
            )

    # ─── Sending Messages ────────────────────────────────────

    async def _send(
        self,
        websocket: WebSocket,
        message: dict
    ) -> bool:
        """Send a message to one client. Returns False if failed."""
        try:
            await websocket.send_json(message)
            return True
        except Exception:
            # Connection is dead — schedule cleanup
            asyncio.create_task(self.disconnect(websocket))
            return False

    async def broadcast_to_project(
        self,
        project_id: int,
        message: dict,
        exclude: WebSocket | None = None
    ) -> int:
        """
        Send a message to all clients subscribed to a project.

        Returns:
            int: Number of clients the message was sent to.
        """
        connections = self._project_rooms.get(project_id, set()).copy()
        sent_count = 0

        for ws in connections:
            if ws == exclude:
                continue
            success = await self._send(ws, message)
            if success:
                sent_count += 1

        return sent_count

    async def broadcast_global(
        self,
        message: dict,
        exclude: WebSocket | None = None
    ) -> int:
        """Send a message to ALL connected clients."""
        sent_count = 0
        for ws in list(self._clients.keys()):
            if ws == exclude:
                continue
            success = await self._send(ws, message)
            if success:
                sent_count += 1
        return sent_count

    async def send_to_user(
        self,
        username: str,
        message: dict
    ) -> bool:
        """Send a message to a specific user (by username)."""
        for ws, client in self._clients.items():
            if client.username == username:
                return await self._send(ws, message)
        return False    # user not connected

    # ─── Presence ────────────────────────────────────────────

    def _get_project_presence(self, project_id: int) -> list[dict]:
        """Get list of users currently in a project room."""
        presence = []
        for ws in self._project_rooms.get(project_id, set()):
            client = self._clients.get(ws)
            if client:
                presence.append(client.to_presence_dict())
        return presence

    # ─── Stats ───────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get connection statistics."""
        project_stats = {
            pid: len(ws_set)
            for pid, ws_set in self._project_rooms.items()
            if ws_set
        }
        return {
            "total_connections": len(self._clients),
            "connected_users": [
                {"username": c.username, "role": c.role,
                 "subscribed_projects": list(c.subscribed_projects)}
                for c in self._clients.values()
            ],
            "project_viewers": project_stats
        }


# Global singleton
manager = TaskBoardManager()