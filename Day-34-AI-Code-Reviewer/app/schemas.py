# ============================================================
# app/schemas.py
# Pydantic schemas for the code reviewer API
# ============================================================

from pydantic import BaseModel, Field
from typing import Optional


class CodeIssue(BaseModel):
    """A single code quality issue."""
    line: Optional[int] = None
    severity: str          # "error", "warning", "info"
    category: str          # "security", "style", "performance", "bug", "complexity"
    message: str
    suggestion: str


class CodeMetrics(BaseModel):
    """Quantitative code metrics."""
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    function_count: int
    class_count: int
    import_count: int
    avg_function_length: float
    max_function_length: int
    complexity_score: str    # "low", "medium", "high"


class CodeReview(BaseModel):
    """Complete code review result."""
    file_path: str
    language: str
    overall_score: int       # 0-10
    grade: str               # A, B, C, D, F
    summary: str
    metrics: CodeMetrics
    issues: list[CodeIssue]
    top_improvements: list[str]
    positive_aspects: list[str]
    review_time_ms: float


class ReviewRequest(BaseModel):
    """Request to review code."""
    file_path: str = Field(
        example="sample_code/bad_code.py",
        description="Path to the Python file to review"
    )
    focus_areas: list[str] = Field(
        default=["security", "style", "performance", "bugs"],
        description="Areas to focus the review on"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "sample_code/bad_code.py",
                "focus_areas": ["security", "style", "performance", "bugs"]
            }
        }


class InlineReviewRequest(BaseModel):
    """Request to review code provided inline."""
    code: str = Field(
        min_length=10,
        description="Python code to review"
    )
    filename: str = Field(
        default="code.py",
        description="Filename for context"
    )