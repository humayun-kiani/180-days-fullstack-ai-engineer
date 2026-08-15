# Day 33 — LangChain: Agents, Tools, Memory & Document Chains

> **Phase 3 — AI & Machine Learning** | Week 6 | Day 33 of 180

---

## 📌 What I Learned Today

- LangChain architecture: Models, Prompts, Parsers, Retrievers, Chains, Agents
- LCEL pipe syntax: prompt | llm | parser (left-to-right composition)
- ChatPromptTemplate.from_messages(): structured prompt with roles
- MessagesPlaceholder: inject conversation history into prompts
- StrOutputParser: extract text from AIMessage response
- JsonOutputParser: extract structured data with Pydantic schema
- RunnableParallel: run multiple chains simultaneously
- RunnablePassthrough: pass input unchanged through the pipeline
- RunnableLambda: wrap any Python function as a LangChain runnable
- @tool decorator: turn any Python function into a LangChain tool
- Tool docstrings: how the agent decides which tool to call
- create_tool_calling_agent: modern agent using Claude's tool_use API
- AgentExecutor: manages the thought-action-observation loop
- max_iterations: prevent infinite agent loops
- handle_parsing_errors=True: graceful recovery from LLM format errors
- return_intermediate_steps=True: see which tools were called
- ConversationBufferWindowMemory: keep last k exchanges
- memory.chat_memory.messages: access raw message history
- chat_history MessagesPlaceholder in agent prompt
- HumanMessage/AIMessage: LangChain message types
- Document: LangChain's document wrapper with page_content + metadata
- RecursiveCharacterTextSplitter: smart chunking with separator hierarchy
- Chroma.from_documents(): build vector store from Document list
- vs.similarity_search(query, k=3): semantic search in LangChain
- vectorstore.as_retriever(): convert to LangChain retriever interface
- MockAgentExecutor: realistic fallback for development without API key
- ReAct pattern: Reason → Act → Observe → Reason → Act...

## 🔨 Project Built

**Task Management AI Agent** — Full LangChain system:

**Chains (LCEL):**

- Task analysis: RunnableParallel runs priority + category + actions simultaneously
- Q&A chain: system prompt | llm | StrOutputParser
- Summarization: prompt | llm | StrOutputParser

**Tools (8 total):**

- search_knowledge_base: ChromaDB semantic search with keyword fallback
- list_tasks: filter by status/priority/owner
- get_overdue_tasks: find tasks past deadline
- get_task_summary: dashboard overview
- create_task: add new task to system
- complete_task: mark task done
- analyze_task_priority: AI classification via chain
- generate_task_report: LLM-written status report

**Agent:**

- create_tool_calling_agent with Claude and all 8 tools
- ConversationBufferWindowMemory (last 10 exchanges)
- MockAgentExecutor with contextual responses (no API key needed)
- AgentSession + AgentMemoryStore for session management

**FastAPI:**

- POST /agent/chat — multi-turn agent with memory
- POST /chains/analyze-task — parallel chain demo
- POST /chains/qa — simple Q&A chain
- POST /chains/summarize — text summarization
- GET /tasks, /tasks/overdue, /tasks/summary — direct tool access
- GET /sessions — conversation history management

## 🚀 How to Run

```bash
cd Day-33-LangChain-Agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your-key" > .env  # optional

uvicorn app.main:app --reload

# Test agent
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What tasks are overdue?", "session_id": "s1"}'
```

## 🧠 LCEL vs Manual (Day 32)

|           | Day 32 Manual     | Day 33 LCEL                      |
| --------- | ----------------- | -------------------------------- |
| Chain     | Custom Python     | `prompt \| llm \| parser`        |
| Parallel  | Sequential Python | `RunnableParallel(...)`          |
| Agent     | Manual loop       | `create_tool_calling_agent`      |
| Tools     | Python functions  | `@tool` decorated functions      |
| Memory    | Custom class      | `ConversationBufferWindowMemory` |
| Retrieval | Direct ChromaDB   | `vectorstore.as_retriever()`     |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
