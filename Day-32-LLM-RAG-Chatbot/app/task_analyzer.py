# ============================================================
# app/task_analyzer.py
# Structured task analysis using Claude
# ============================================================

from app.claude_client import ClaudeClient


TASK_ANALYSIS_SCHEMA = """{
  "priority": "urgent|high|medium|low",
  "category": "bug|feature|performance|maintenance|question|security",
  "estimated_hours": <number between 0.5 and 40>,
  "tags": ["tag1", "tag2", "tag3"],
  "reason": "<one sentence explaining the priority classification>",
  "suggested_actions": ["action1", "action2", "action3"],
  "urgency_score": <integer 1-10>
}"""

TASK_ANALYSIS_SYSTEM = """You are a technical project management assistant.
Analyze software development tasks and provide structured classification.

Guidelines:
- urgent: production impact, security breach, data loss risk
- high: blocks users or team, has hard deadline within 3 days
- medium: important but not blocking, deadline within 2 weeks
- low: nice-to-have, research, documentation, no hard deadline

Be realistic with time estimates. A 'fix login bug' is typically 2-4 hours,
not 30 minutes. A 'refactor authentication module' is typically 8-16 hours."""


class TaskAnalyzer:
    """Analyze tasks using Claude for structured classification."""

    def __init__(self, claude_client: ClaudeClient):
        self.claude = claude_client

    def analyze(self, title: str, description: str = "") -> tuple[dict, int]:
        """
        Analyze a task and return structured classification.

        Args:
            title: Task title.
            description: Optional detailed description.

        Returns:
            tuple: (analysis dict, total tokens used)
        """
        prompt_parts = [f"Analyze this software task:\nTitle: {title}"]
        if description:
            prompt_parts.append(f"Description: {description}")

        prompt = "\n".join(prompt_parts)

        result, usage = self.claude.complete_structured(
            prompt=prompt,
            schema=TASK_ANALYSIS_SCHEMA,
            system_prefix=TASK_ANALYSIS_SYSTEM,
            max_tokens=512
        )

        # Normalize and validate
        result.setdefault("priority", "medium")
        result.setdefault("category", "general")
        result.setdefault("estimated_hours", 4.0)
        result.setdefault("tags", [])
        result.setdefault("reason", "Based on task description analysis")
        result.setdefault("suggested_actions", ["Review requirements", "Implement fix", "Test"])
        result.setdefault("urgency_score", 5)

        tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        return result, tokens_used