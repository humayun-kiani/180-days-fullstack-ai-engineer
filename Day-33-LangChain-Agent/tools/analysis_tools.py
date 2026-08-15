# ============================================================
# tools/analysis_tools.py
# Task analysis tools using LangChain chains
# ============================================================

import json
import os
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Lazy import to avoid circular dependencies
_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        from langchain_anthropic import ChatAnthropic
        _llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            temperature=0.2,
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", "mock")
        )
    return _llm


@tool
def analyze_task_priority(task_description: str) -> str:
    """
    Analyze a task description and determine its priority using AI.

    Use this when you need to classify or assess the urgency and
    importance of a task based on its description.

    Args:
        task_description: Full description of the task to analyze

    Returns:
        JSON with priority, category, urgency_score, and reasoning
    """
    llm = _get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a task prioritization expert.
Analyze the task and respond with ONLY valid JSON (no markdown):
{
  "priority": "urgent|high|medium|low",
  "category": "bug|feature|performance|maintenance|review|question",
  "urgency_score": 1-10,
  "reason": "one sentence explanation",
  "suggested_action": "immediate next step"
}"""),
        ("human", "Analyze this task: {task}")
    ])

    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"task": task_description})

    # Try to parse and pretty-print
    try:
        parsed = json.loads(result.strip())
        return json.dumps(parsed, indent=2)
    except Exception:
        return result


@tool
def generate_task_report(timeframe: str = "today") -> str:
    """
    Generate a natural language summary report of tasks.

    Use this when the user asks for a report, briefing, or summary
    of task status. Useful for standup meetings or end-of-day reviews.

    Args:
        timeframe: Report timeframe: today, week, or all

    Returns:
        Natural language task status report
    """
    from tools.task_tools import _TASKS, _is_overdue
    from datetime import datetime, timedelta

    now = datetime.utcnow()

    if timeframe == "today":
        cutoff = now - timedelta(days=1)
    elif timeframe == "week":
        cutoff = now - timedelta(days=7)
    else:
        cutoff = now - timedelta(days=365)

    recent = [
        t for t in _TASKS
        if datetime.fromisoformat(t["created_at"]) > cutoff
    ]

    pending = [t for t in _TASKS if t["status"] == "pending"]
    in_progress = [t for t in _TASKS if t["status"] == "in_progress"]
    done = [t for t in _TASKS if t["status"] == "done"]
    overdue = [t for t in _TASKS if _is_overdue(t)]
    urgent = [t for t in _TASKS if t["priority"] == "urgent" and t["status"] != "done"]

    report_data = {
        "timeframe": timeframe,
        "total_tasks": len(_TASKS),
        "pending": len(pending),
        "in_progress": len(in_progress),
        "completed": len(done),
        "overdue": len(overdue),
        "urgent_unresolved": len(urgent),
        "recent_tasks": [t["title"] for t in recent[:3]],
        "overdue_titles": [t["title"] for t in overdue],
        "urgent_titles": [t["title"] for t in urgent]
    }

    llm = _get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a project manager writing a concise status report. Be professional and action-oriented."),
        ("human", """Write a {timeframe} task status report based on this data:
{data}

Include: key metrics, what needs immediate attention, what's going well.
Keep it under 200 words. Use markdown formatting.""")
    ])
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"timeframe": timeframe, "data": json.dumps(report_data, indent=2)})