# ============================================================
# app/agent.py
# LangChain tool-calling agent — the core intelligence
# ============================================================

import os
from typing import Optional
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from tools.kb_tools import search_knowledge_base
from tools.task_tools import (
    list_tasks, get_overdue_tasks, get_task_summary,
    create_task, complete_task
)
from tools.analysis_tools import analyze_task_priority, generate_task_report

# ─── Mock Agent (no API key) ─────────────────────────────────

class MockAgentExecutor:
    """Realistic mock agent for development without API key."""

    MOCK_RESPONSES = {
        "overdue": """I checked the task database for overdue items.

**Overdue Tasks:**
1. **Fix login bug causing 500 errors** (1 day overdue) — HIGH priority
   - Status: In Progress
   - Owner: humayun
   - Recommended action: Escalate to urgent, ensure active work today

2. **URGENT: Production database slow** (2 hours overdue) — URGENT
   - Status: Pending (not yet started!)
   - Owner: humayun
   - Recommended action: Start immediately — production impact

**Summary:** 2 tasks are overdue. The database issue is most critical as it's marked URGENT and affecting production.""",

        "summary": """**Task Management Dashboard**

📊 **Current Status:**
- Total tasks: 6
- Pending: 4 | In Progress: 1 | Done: 1
- Overdue: 2 tasks ⚠️
- Urgent unresolved: 1

🔴 **Needs Immediate Attention:**
1. Production database slow (URGENT, overdue)
2. Fix login bug (HIGH, overdue)

✅ **Good Progress:**
- API documentation has been completed

📋 **Coming Up:**
- Redis caching implementation (due in 5 days)
- PR #42 review (due tomorrow)""",

        "create": """I've created a new task for you.

✅ Task created successfully!
- **ID:** 7
- **Title:** As specified
- **Priority:** Set as requested
- **Status:** Pending

The task has been added to the system and is ready to be assigned.""",

        "default": """I've analyzed your request and searched the available information.

Based on the knowledge base and current task data, here's what I found:

The issue you're describing is commonly related to configuration or authentication settings. I recommend:

1. Check the application logs for specific error messages
2. Verify environment variables are correctly set
3. Review the relevant documentation section for your specific error

Would you like me to search for more specific information or check the current task status?"""
    }

    def invoke(self, inputs: dict) -> dict:
        query = inputs.get("input", "").lower()
        history = inputs.get("chat_history", [])

        if any(w in query for w in ["overdue", "late", "missed", "past due"]):
            response = self.MOCK_RESPONSES["overdue"]
        elif any(w in query for w in ["summary", "overview", "dashboard", "status", "report"]):
            response = self.MOCK_RESPONSES["summary"]
        elif any(w in query for w in ["create", "add", "new task", "log"]):
            response = self.MOCK_RESPONSES["create"]
        else:
            response = self.MOCK_RESPONSES["default"]

        return {"output": response, "intermediate_steps": []}


# ─── Real Agent ───────────────────────────────────────────────

AGENT_SYSTEM_PROMPT = """You are an intelligent task management assistant for a software development team.

You have access to these tools:
- search_knowledge_base: Find documentation on debugging, auth, performance, database, Docker, etc.
- list_tasks: Get tasks filtered by status/priority/owner
- get_overdue_tasks: Find tasks past their deadline
- get_task_summary: Get a dashboard overview of all tasks
- create_task: Create a new task
- complete_task: Mark a task as done
- analyze_task_priority: Use AI to classify a task's priority
- generate_task_report: Create a status report for standup meetings

Guidelines:
- Always use tools to get real data before answering
- Be specific and actionable in your responses
- When tasks are overdue or urgent, clearly highlight this
- Format responses with markdown for readability
- If asked to create a task, confirm the details before creating"""


def build_agent() -> AgentExecutor:
    """Build the LangChain tool-calling agent."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    # Use mock if no real API key
    if not api_key or api_key == "your-api-key-here":
        print("  ⚠️  Using mock agent (add ANTHROPIC_API_KEY to .env for real agent)")
        return MockAgentExecutor()

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=0,
        anthropic_api_key=api_key,
        max_tokens=2048
    )

    tools = [
        search_knowledge_base,
        list_tasks,
        get_overdue_tasks,
        get_task_summary,
        create_task,
        complete_task,
        analyze_task_priority,
        generate_task_report,
    ]

    prompt = ChatPromptTemplate.from_messages([
        ("system", AGENT_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=6,
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )