# Day 36 — Week 6 Revision: Full AI Pipeline Integration

> **Phase 3 — AI & Machine Learning** | Week 6 Capstone | Day 36 of 180

---

## 📌 What I Learned Today

- Pipeline orchestration: coordinate multiple AI components
- Query routing: rule-based intent classification without LLM overhead
- Parallel data fetching: asyncio.gather() across KB + 4 APIs simultaneously
- Context fusion: merge sources with priority ordering and token budget
- Source attribution: label each piece of context for Claude to cite
- Context truncation: hard limit at 8000 chars before token overflow
- FusedContext dataclass: typed container for all collected data
- QueryIntent dataclass: typed routing decision with extracted entities
- MockGenerator: contextual responses keyed on query keywords
- Debug endpoints: /debug/route and /debug/pipeline for transparency
- End-to-end: query → route → fetch → fuse → generate → response

## 🔨 Project Built

**AI Research Assistant** — Days 31-35 unified:

**Architecture (4 layers):**

- Router: keyword-based intent classifier, extracts cities/repos/currencies
- Pipeline: parallel asyncio.gather() of KB + all 4 external APIs
- ContextBuilder: priority-ordered fusion with truncation
- Generator: Claude with full context OR contextual mock

**Live APIs (all real, all free):**

- Open-Meteo: current weather by city
- GitHub: trending repos by language/period
- Open.er-api.com: USD exchange rates
- HackerNews Firebase: top 5 tech stories

**Endpoints:**

- POST /research: full pipeline → grounded answer
- GET /debug/route: see routing without fetching
- GET /debug/pipeline: see raw context without generation
- GET /demo: 7 example queries with routing preview

## 🚀 How to Run

```bash
cd Day-36-AI-Research-Assistant
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your-key" > .env  # optional

uvicorn app.main:app --reload

curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather in Karachi?"}'
```

## 🧠 Week 6 Components Map

| Day | Component             | Role in Pipeline               |
| --- | --------------------- | ------------------------------ |
| 31  | ChromaDB + Embeddings | Knowledge base semantic search |
| 32  | RAG + Claude          | Grounded generation            |
| 33  | LangChain Agent       | Tool orchestration pattern     |
| 34  | Raw Tool Calling      | Direct API control             |
| 35  | Async External APIs   | Live real-time data            |
| 36  | Integration           | Unified, routed, fused         |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
