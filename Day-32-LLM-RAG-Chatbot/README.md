# Day 32 — LLM Integration: Anthropic API, Prompt Engineering & RAG Chatbot

> **Phase 3 — AI & Machine Learning** | Week 6 | Day 32 of 180

---

## 📌 What I Learned Today

- Anthropic Messages API: client.messages.create() with model, max_tokens, messages
- Messages structure: role "user"/"assistant" + content string
- System prompts: set AI persona and constraints outside the messages list
- Temperature: 0.0 = deterministic, 1.0 = creative, 0.5 = balanced default
- max_tokens: cap output length, 1 token ≈ 4 chars in English
- stop_sequences: stop generation at specific strings
- Streaming: client.messages.stream() yields tokens as generated
- FastAPI StreamingResponse with text/event-stream for SSE
- Token counting: client.messages.count_tokens() before API call
- Cost calculation: input tokens × $0.003/1K + output tokens × $0.015/1K
- Structured outputs: temperature=0.1 + JSON schema in system prompt
- JSON extraction: handle markdown code blocks in LLM output
- Multi-turn conversation: accumulate messages list across turns
- History trimming: remove oldest messages when approaching token budget
- Retry logic: exponential backoff on RateLimitError and APIStatusError
- Mock client: realistic fake responses when no API key available
- RAG system prompt: how to ground Claude in retrieved documentation
- build_rag_prompt(): inject context between document blocks and question
- Session management: UUID session IDs, in-memory store
- Few-shot prompting: examples in system prompt improve classification
- Chain-of-thought: "think step by step" improves reasoning tasks
- Role prompting: "you are a senior engineer" improves domain answers

## 🔨 Project Built

**RAG Chatbot with Claude:**

- ClaudeClient: wraps Anthropic SDK with retry, token tracking, cost estimation
  - MockAnthropicClient for development without API key
- ConversationSession: accumulates message history with token budget trimming
- SessionStore: in-memory session management (replace with Redis in prod)
- RAGPipeline: retrieve from ChromaDB → build augmented prompt → generate with Claude
- TaskAnalyzer: structured JSON output from Claude (priority, category, hours, tags)
- FastAPI endpoints:
  - POST /chat: multi-turn RAG chat with session persistence
  - POST /chat/stream: SSE streaming response
  - POST /analyze/task: structured task analysis
  - GET /sessions, /sessions/{id}: conversation history
  - GET /usage: token usage + cost tracking
  - GET /demo: example queries without API key

## 🚀 How to Run

```bash
cd Day-32-LLM-RAG-Chatbot
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Add your API key (get at console.anthropic.com)
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# Build knowledge base (requires Day 31 setup first)
# OR it works without KB (direct Claude answers)

uvicorn app.main:app --reload

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I fix JWT expiration errors?", "session_id": "s1"}'
```

## 🧠 Key Patterns

| Pattern     | Code                                                                |
| ----------- | ------------------------------------------------------------------- |
| Basic call  | `client.messages.create(model=..., max_tokens=..., messages=[...])` |
| With system | Add `system="..."` parameter                                        |
| Streaming   | `with client.messages.stream(...) as s: for t in s.text_stream:`    |
| JSON output | temperature=0.1 + JSON schema in system prompt                      |
| Multi-turn  | Accumulate `messages` list, pass full history each call             |
| RAG         | Inject retrieved context into user message before LLM call          |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
