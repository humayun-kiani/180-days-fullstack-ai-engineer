# ============================================================
# app/ws_auth.py
# WebSocket authentication helpers
# ============================================================

import asyncio
from fastapi import WebSocket
from app.fake_db import get_user_by_token
from app.schemas import MessageType


async def authenticate_websocket(
    websocket: WebSocket,
    token: str | None = None,
    timeout_seconds: float = 10.0
) -> dict | None:
    """
    Authenticate a WebSocket connection.

    Strategy:
    1. If token provided as query param → verify immediately
    2. If no token → wait for first message to contain auth data
    3. Timeout if no auth received within timeout_seconds

    Args:
        websocket: The WebSocket connection (already accepted).
        token: Optional token from query string.
        timeout_seconds: How long to wait for auth message.

    Returns:
        dict: User data if authenticated, None if failed.
    """

    # Strategy 1: Token in query parameter
    if token:
        user = get_user_by_token(token)
        if user:
            await websocket.send_json({
                "type": MessageType.AUTHENTICATED,
                "data": {
                    "user_id": user["id"],
                    "username": user["username"],
                    "role": user["role"]
                }
            })
            return user
        else:
            await websocket.send_json({
                "type": MessageType.AUTH_ERROR,
                "data": {"message": "Invalid token"}
            })
            await websocket.close(code=4001, reason="Invalid token")
            return None

    # Strategy 2: Wait for auth message
    try:
        message = await asyncio.wait_for(
            websocket.receive_json(),
            timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        await websocket.send_json({
            "type": MessageType.AUTH_ERROR,
            "data": {"message": f"Authentication timeout ({timeout_seconds}s)"}
        })
        await websocket.close(code=4001, reason="Auth timeout")
        return None
    except Exception:
        return None

    if message.get("type") != MessageType.AUTHENTICATE:
        await websocket.send_json({
            "type": MessageType.AUTH_ERROR,
            "data": {"message": "First message must be authentication"}
        })
        await websocket.close(code=4001, reason="Expected auth message")
        return None

    token = message.get("token", "")
    user = get_user_by_token(token)

    if not user:
        await websocket.send_json({
            "type": MessageType.AUTH_ERROR,
            "data": {"message": "Invalid credentials"}
        })
        await websocket.close(code=4001, reason="Invalid credentials")
        return None

    await websocket.send_json({
        "type": MessageType.AUTHENTICATED,
        "data": {
            "user_id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "message": f"Welcome, {user['username']}!"
        }
    })
    return user