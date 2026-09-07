# backend/app/api/websocket.py
import json
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.security import decode_token

router = APIRouter(tags=["websocket"])

# Connection manager — tracks all active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}  # user_id → [ws]

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        """Send a message to all connections for a user."""
        connections = self._connections.get(user_id, set())
        dead = []
        for ws in connections:
            try:
                await ws.send_text(json.dumps(message, default=str))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, user_id)

    @property
    def active_count(self) -> int:
        return sum(len(v) for v in self._connections.values())


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for real-time task updates."""
    user_id = decode_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await manager.connect(websocket, user_id)

    try:
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }))

        # Keep connection alive with ping/pong
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_text(json.dumps({"type": "keepalive"}))

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)