# ============================================================
# app/memory_store.py
# Conversation memory management for the agent
# ============================================================

import uuid
from datetime import datetime
from dataclasses import dataclass, field
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage


@dataclass
class AgentSession:
    """One conversation session with the agent."""
    session_id: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    turn_count: int = 0
    memory: ConversationBufferWindowMemory = field(
        default_factory=lambda: ConversationBufferWindowMemory(
            k=10,
            return_messages=True,
            memory_key="chat_history",
            input_key="input",
            output_key="output"
        )
    )

    def add_exchange(self, user_msg: str, ai_msg: str) -> None:
        """Add a human-AI exchange to memory."""
        self.memory.chat_memory.add_user_message(user_msg)
        self.memory.chat_memory.add_ai_message(ai_msg)
        self.turn_count += 1

    def get_history_messages(self) -> list[dict]:
        """Get conversation history in Anthropic API format."""
        messages = []
        for msg in self.memory.chat_memory.messages:
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})
        return messages

    def to_dict(self) -> dict:
        history = self.get_history_messages()
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "turn_count": self.turn_count,
            "message_count": len(history),
            "preview": history[-1]["content"][:100] + "..." if history else ""
        }


class AgentMemoryStore:
    """Manages conversation sessions for the agent."""

    def __init__(self):
        self._sessions: dict[str, AgentSession] = {}

    def get_or_create(self, session_id: str | None = None) -> AgentSession:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        new_id = session_id or str(uuid.uuid4())[:8]
        session = AgentSession(session_id=new_id)
        self._sessions[new_id] = session
        return session

    def get(self, session_id: str) -> AgentSession | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[dict]:
        return [s.to_dict() for s in self._sessions.values()]

    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False


# Global memory store
memory_store = AgentMemoryStore()