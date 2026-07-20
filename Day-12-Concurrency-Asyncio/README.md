# Day 12 — Concurrency: Threading, Multiprocessing & Asyncio

> **Phase 1 — Foundations** | Week 2 | Day 12 of 180

---

## 📌 What I Learned Today

- Why sequential code is slow for I/O-bound tasks
- The GIL — what it is, why it exists, and when it matters
- I/O-bound vs CPU-bound tasks — the critical distinction
- Threading — multiple threads sharing memory, Lock for thread safety
- concurrent.futures — ThreadPoolExecutor and ProcessPoolExecutor
- Multiprocessing — true parallelism bypassing the GIL
- asyncio — single-threaded cooperative concurrency with event loop
- async def, await, asyncio.gather(), asyncio.create_task()
- aiohttp — async HTTP requests with session and connection pooling
- RateLimiter using asyncio.Semaphore — limit concurrent requests
- asyncio.gather(return_exceptions=True) — handle failures gracefully
- Benchmarking: sequential vs threading vs asyncio comparison
- When to use which: asyncio for I/O, multiprocessing for CPU

## 🔨 Project Built

**Async News Headline Fetcher** — Complete async application:

- Fetches from 7 sources simultaneously with asyncio + aiohttp
- Custom RateLimiter using asyncio.Semaphore
- Benchmarks sequential vs async fetch with real timing
- 5x speedup demonstrated and visualized in terminal
- Deduplicates headlines across sources
- Groups headlines by category
- Caches results for 15 minutes
- Exports all data to timestamped JSON files
- Full error handling per source (one failure doesn't stop others)
- Visual performance comparison with bar charts

## 🚀 How to Run

```bash
cd Day-12-Concurrency-Asyncio
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
python src/main.py
```

## 🧠 Key Concepts

| Concept                 | Use Case                    |
| ----------------------- | --------------------------- |
| `threading.Thread`      | Simple I/O concurrency      |
| `threading.Lock`        | Thread-safe shared state    |
| `ThreadPoolExecutor`    | Pool of threads for I/O     |
| `ProcessPoolExecutor`   | Pool of processes for CPU   |
| `async def`             | Define a coroutine          |
| `await`                 | Suspend until result ready  |
| `asyncio.gather()`      | Run coroutines concurrently |
| `aiohttp.ClientSession` | Async HTTP with pooling     |
| `asyncio.Semaphore`     | Limit concurrent coroutines |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
