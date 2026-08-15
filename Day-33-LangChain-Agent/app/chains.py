# ============================================================
# app/chains.py
# LCEL chains for specific use cases
# ============================================================

import os
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough


def get_llm(temperature: float = 0.5) -> ChatAnthropic:
    """Get configured Claude LLM."""
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=temperature,
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", "mock"),
        max_tokens=1024
    )


def build_task_analysis_chain():
    """
    Chain: task description → parallel analysis (priority + category + actions).
    Uses RunnableParallel to run all three analyses simultaneously.
    """
    llm = get_llm(temperature=0.2)
    parser = StrOutputParser()

    priority_chain = (
        ChatPromptTemplate.from_template(
            "Task priority (respond with ONE word: urgent/high/medium/low):\n{task}"
        ) | llm | parser
    )

    category_chain = (
        ChatPromptTemplate.from_template(
            "Task category (ONE word: bug/feature/performance/maintenance/review/question/security):\n{task}"
        ) | llm | parser
    )

    actions_chain = (
        ChatPromptTemplate.from_template(
            "List 3 concrete next steps for this task (numbered list, concise):\n{task}"
        ) | llm | parser
    )

    return RunnableParallel(
        task=RunnablePassthrough(),
        priority=priority_chain,
        category=category_chain,
        next_actions=actions_chain
    )


def build_qa_chain():
    """Simple Q&A chain with system context."""
    llm = get_llm(temperature=0.5)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful assistant for a software development team
using the TaskManager system. Answer questions clearly and concisely.
If you don't know something specific about their system, say so."""),
        ("human", "{question}")
    ])
    return prompt | llm | StrOutputParser()


def build_summarize_chain():
    """Summarize long text into bullet points."""
    llm = get_llm(temperature=0.3)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Summarize the following in 3-5 bullet points. Be concise and technical."),
        ("human", "{text}")
    ])
    return prompt | llm | StrOutputParser()