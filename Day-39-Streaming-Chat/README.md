# Day 39 — Streaming AI Responses & Real-Time UX

> **Phase 4 — Advanced AI Engineering** | Week 7 | Day 39 of 180

---

## 📌 What I Learned Today

- SSE vs WebSockets vs HTTP polling: when to use each
- SSE format: data: {json}\n\n — double newline ends each event
- FastAPI StreamingResponse: media_type="text/event-stream"
- Cache-Control: no-cache and X-Accel-Buffering: no headers
- AsyncGenerator[str, None]: yield chunks from async generator
- await req.is_disconnected(): stop streaming when client leaves
- Anthropic streaming: with client.messages.stream(...) as stream
- stream.text_stream: iterates one text chunk at a time
- stream.get_final_message(): metadata after stream completes
- fetch() with ReadableStream: supports POST (EventSource only does GET)
- reader.read(): returns {done, value} for streaming consumption
- TextDecoder with {stream: true}: handle partial UTF-8 sequences
- Buffer management: split on \n\n, keep incomplete last event
- Event types: start, stage, token, sources, done, error
- Stage streaming: yield status updates before generation starts
- Multi-step pipeline visibility: user sees retrieval stage
- requestAnimationFrame for smooth UI updates
- Auto-scroll threshold: only scroll if near the bottom (<150px)
- Minimal markdown renderer: bold, code blocks, lists in vanilla JS
- MockStreamer: simulate streaming with configurable word delay
- Disconnect detection: await req.is_disconnected() in generator

## 🔨 Project Built

**Real-Time AI Chat Interface:**

**ClaudeStreamer** (app/streamer.py):

- Real Claude streaming via anthropic SDK
- MockStreamer with per-word delay for demo
- Async generator yielding typed event dicts
- Error handling: RateLimitError, APIConnectionError, timeout
- SYSTEM_PROMPT for consistent assistant behavior

**StreamingPipeline** (app/pipeline.py):

- Stage 1: analyzing (immediate)
- Stage 2: KB retrieval (search_kb)
- Stage 3: generating (Claude stream)
- Sources appended after generation
- All stages yield SSE events to browser

**Web Chat UI** (static/index.html):

- Streaming fetch with ReadableStream
- Buffer management for partial SSE events
- Stage indicators with animated dots
- Cursor blink animation during generation
- Minimal markdown renderer (bold, code, lists)
- Example query buttons, clear chat, mode toggle
- Auto-scroll with 150px threshold
- Token counter and session stats

**FastAPI endpoints:**

- POST /stream/chat: direct Claude streaming
- POST /stream/pipeline: RAG pipeline with stages
- GET /stream/demo: fixed demo stream (no API needed)
- POST /stream/pipeline/steps: stages only (no generation)
- GET /api/kb/search: test KB search

## 🚀 How to Run

```bash
cd Day-39-Streaming-Chat
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your-key" > .env  # optional

uvicorn app.main:app --reload

# Open web chat UI
open http://localhost:8000

# Or test raw SSE
curl -X POST http://localhost:8000/stream/pipeline \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I fix JWT errors?", "history": []}' \
  --no-buffer
```

## 🧠 SSE Event Format

```
data: {"type": "stage", "message": "Searching KB..."}\n\n
data: {"type": "token", "content": "JWT "}\n\n
data: {"type": "done", "tokens_generated": 87}\n\n
data: [DONE]\n\n
```

Rules: one `data:` line per event, double `\n\n` ends each event.

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
