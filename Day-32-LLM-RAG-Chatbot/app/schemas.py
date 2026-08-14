# ============================================================
# app/schemas.py
# Pydantic schemas for the RAG chatbot API
# ============================================================

from pydantic import BaseModel, Field
from typing import Optional


class ChatMessage(BaseModel):
    role: str                   # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Single-turn or multi-turn chat request."""
    message: str = Field(
        min_length=1,
        max_length=2000,
        example="How do I fix JWT token expiration errors?"
    )
    session_id: Optional[str] = Field(
        None,
        description="Session ID for multi-turn conversation",
        example="session-abc123"
    )
    use_knowledge_base: bool = Field(
        True,
        description="Whether to retrieve knowledge base context (RAG)"
    )
    stream: bool = Field(
        False,
        description="Whether to stream the response token by token"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "My API keeps returning 401 errors after login. What should I check?",
                "session_id": "session-humayun-001",
                "use_knowledge_base": True,
                "stream": False
            }
        }


class ChatResponse(BaseModel):
    """Response from the RAG chatbot."""
    answer: str
    session_id: str
    sources: list[dict] = []
    tokens_used: dict = {}
    retrieved_context: bool = False
    model: str = "claude-sonnet-4-6"


class TaskAnalysisRequest(BaseModel):
    """Request for structured task analysis."""
    title: str = Field(
        min_length=1,
        max_length=500,
        example="URGENT: Production database is down"
    )
    description: Optional[str] = None


class TaskAnalysisResponse(BaseModel):
    """Structured task analysis from Claude."""
    priority: str
    category: str
    estimated_hours: float
    tags: list[str]
    reason: str
    suggested_actions: list[str]
    urgency_score: int
    model: str = "claude-sonnet-4-6"
    tokens_used: int = 0