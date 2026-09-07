# backend/app/services/ai_service.py
import json
import os
from typing import Optional

import anthropic

from app.schemas.ai import (
    AnalyzeResponse, ExpandResponse, BreakdownResponse, SubTask,
    WeeklySummaryResponse
)

_client: Optional[anthropic.Anthropic] = None
_mock = True


def _get_client() -> Optional[anthropic.Anthropic]:
    global _client, _mock
    if _client is None:
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if key and key != "your-api-key-here":
            _client = anthropic.Anthropic(api_key=key)
            _mock = False
    return _client


def _mock_analyze(title: str, description: str = None) -> AnalyzeResponse:
    """Realistic mock for when no API key is set."""
    t = title.lower()
    if any(w in t for w in ["urgent", "critical", "down", "outage", "breach"]):
        priority, conf = "urgent", "high"
    elif any(w in t for w in ["fix", "bug", "error", "before", "security"]):
        priority, conf = "high", "high"
    elif any(w in t for w in ["add", "implement", "create", "build"]):
        priority, conf = "medium", "medium"
    else:
        priority, conf = "low", "medium"

    return AnalyzeResponse(
        suggested_priority=priority,
        confidence=conf,
        reasoning=f"Title contains keywords indicating {priority} priority.",
        suggested_tags=["backend", "api"],
        summary=f"Task: {title[:80]}",
        estimated_hours={"urgent": 2.0, "high": 4.0, "medium": 6.0, "low": 2.0}[priority]
    )


async def analyze_task(title: str, description: str = None) -> AnalyzeResponse:
    """Analyze a task and return AI suggestions."""
    client = _get_client()

    if not client:
        return _mock_analyze(title, description)

    prompt = f"""Analyze this task and return a JSON response.

Task Title: {title}
Description: {description or "Not provided"}

Return ONLY valid JSON with these fields:
{{
  "suggested_priority": "urgent|high|medium|low",
  "confidence": "high|medium|low",
  "reasoning": "One sentence why",
  "suggested_tags": ["tag1", "tag2"],
  "summary": "Brief one-sentence summary",
  "estimated_hours": 4.0
}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        return AnalyzeResponse(**data)
    except Exception as e:
        return _mock_analyze(title, description)


async def expand_task(title: str) -> ExpandResponse:
    """Expand a brief task title into a full description."""
    client = _get_client()

    if not client:
        return ExpandResponse(
            description=f"Implement and test '{title}'. Ensure proper error handling and documentation.",
            suggested_priority="medium",
            suggested_tags=["backend"]
        )

    prompt = f"""Expand this task title into a detailed description for a software engineering team.

Task: {title}

Return ONLY JSON:
{{
  "description": "2-3 sentence detailed description",
  "suggested_priority": "urgent|high|medium|low",
  "suggested_tags": ["tag1", "tag2"]
}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        return ExpandResponse(**data)
    except Exception:
        return ExpandResponse(
            description=f"Implement and test: {title}",
            suggested_priority="medium",
            suggested_tags=["engineering"]
        )


async def breakdown_task(title: str, description: str = None) -> BreakdownResponse:
    """Break a task into smaller subtasks."""
    client = _get_client()

    if not client:
        return BreakdownResponse(
            subtasks=[
                SubTask(title=f"Research and plan: {title}", estimated_hours=1.0, priority="medium"),
                SubTask(title=f"Implement: {title}", estimated_hours=4.0, priority="medium"),
                SubTask(title=f"Test: {title}", estimated_hours=2.0, priority="medium"),
                SubTask(title=f"Document: {title}", estimated_hours=1.0, priority="low"),
            ],
            total_estimated_hours=8.0
        )

    prompt = f"""Break this task into 3-6 subtasks for a development team.

Task: {title}
Description: {description or "Not provided"}

Return ONLY JSON:
{{
  "subtasks": [
    {{"title": "Subtask name", "estimated_hours": 2.0, "priority": "medium"}}
  ],
  "total_estimated_hours": 8.0
}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        subtasks = [SubTask(**s) for s in data.get("subtasks", [])]
        total = data.get("total_estimated_hours", sum(s.estimated_hours for s in subtasks))
        return BreakdownResponse(subtasks=subtasks, total_estimated_hours=total)
    except Exception:
        return BreakdownResponse(
            subtasks=[
                SubTask(title=f"Implement: {title}", estimated_hours=4.0, priority="medium")
            ],
            total_estimated_hours=4.0
        )


async def weekly_summary(tasks: list[dict]) -> WeeklySummaryResponse:
    """Generate a weekly summary from task data."""
    total = len(tasks)
    done = sum(1 for t in tasks if t.get("status") == "done")
    urgent = sum(1 for t in tasks if t.get("priority") == "urgent")
    pending = sum(1 for t in tasks if t.get("status") == "pending")

    stats = {
        "total_tasks": total,
        "completed": done,
        "pending": pending,
        "urgent": urgent,
        "completion_rate": f"{done/total*100:.0f}%" if total > 0 else "0%"
    }

    highlights = []
    if done > 0:
        highlights.append(f"{done} tasks completed this week")
    if urgent > 0:
        highlights.append(f"{urgent} urgent tasks require attention")
    if pending > done:
        highlights.append(f"Backlog growing — {pending} tasks pending")

    client = _get_client()

    if not client:
        return WeeklySummaryResponse(
            summary=f"This week: {done}/{total} tasks completed ({stats['completion_rate']} completion rate). "
                    f"{urgent} urgent tasks {'resolved' if done > 0 else 'pending'}.",
            stats=stats,
            highlights=highlights,
            recommendations=["Focus on urgent tasks first", "Review pending backlog"]
        )

    task_list = "\n".join([f"- [{t['status']}] [{t['priority']}] {t['title']}" for t in tasks[:20]])
    prompt = f"""Summarize this week's tasks for a software team.

Tasks:
{task_list}

Stats: {json.dumps(stats)}

Return ONLY JSON:
{{
  "summary": "2-3 sentence executive summary",
  "highlights": ["key point 1", "key point 2"],
  "recommendations": ["action 1", "action 2"]
}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        return WeeklySummaryResponse(
            summary=data.get("summary", ""),
            stats=stats,
            highlights=data.get("highlights", highlights),
            recommendations=data.get("recommendations", [])
        )
    except Exception:
        return WeeklySummaryResponse(
            summary=f"{done}/{total} tasks completed this week.",
            stats=stats,
            highlights=highlights,
            recommendations=["Review urgent tasks", "Update task priorities"]
        )