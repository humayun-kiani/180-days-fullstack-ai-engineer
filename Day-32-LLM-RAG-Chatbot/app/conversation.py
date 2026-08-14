# ============================================================
# app/conversation.py
# Multi-turn conversation session management
# ============================================================

import uuid
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class Message:
    """A single message in a conversation."""
    role: str       # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tokens: int = 0


class ConversationSession:
    """
    Manages a multi-turn conversation with token budget awareness.

    Keeps full history for context, trims oldest messages
    when approaching token limits.
    """

    MAX_HISTORY_MESSAGES = 20    # keep last 20 messages
    MAX_HISTORY_CHARS = 8000     # approx token proxy (1 token ≈ 4 chars)

    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.messages: list[Message] = []
        self.created_at = datetime.utcnow().isoformat()
        self.turn_count = 0
        self.total_tokens = 0

    def add_user_message(self, content: str) -> None:
        self.messages.append(Message(role="user", content=content))
        self.turn_count += 1

    def add_assistant_message(self, content: str, tokens: int = 0) -> None:
        self.messages.append(Message(
            role="assistant",
            content=content,
            tokens=tokens
        ))
        self.total_tokens += tokens

    def get_api_messages(self) -> list[dict]:
        """
        Get messages in Anthropic API format.
        Trims history to stay within budget.
        """
        messages = [
            {"role": m.role, "content": m.content}
            for m in self.messages
        ]

        # Trim to max messages
        if len(messages) > self.MAX_HISTORY_MESSAGES:
            messages = messages[-self.MAX_HISTORY_MESSAGES:]

        # Trim to approximate char limit (proxy for tokens)
        total_chars = sum(len(m["content"]) for m in messages)
        while total_chars > self.MAX_HISTORY_CHARS and len(messages) > 2:
            # Remove oldest exchange (pair of messages)
            total_chars -= len(messages[0]["content"])
            total_chars -= len(messages[1]["content"])
            messages = messages[2:]

        return messages

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "turn_count": self.turn_count,
            "total_tokens": self.total_tokens,
            "message_count": len(self.messages)
        }


class SessionStore:
    """
    In-memory session store.
    In production: use Redis with TTL.
    """

    def __init__(self):
        self._sessions: dict[str, ConversationSession] = {}

    def get_or_create(self, session_id: str | None) -> ConversationSession:
        """Get existing session or create a new one."""
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]

        session = ConversationSession(session_id)
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> ConversationSession | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[dict]:
        return [s.to_dict() for s in self._sessions.values()]

    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False


# Global session store
session_store = SessionStore()