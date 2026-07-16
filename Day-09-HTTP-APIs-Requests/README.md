# Day 09 — HTTP Basics, REST APIs & the Requests Library

> **Phase 1 — Foundations** | Week 2 | Day 9 of 180

---

## 📌 What I Learned Today

- How HTTP works — request/response cycle explained
- HTTP methods: GET, POST, PUT, PATCH, DELETE
- HTTP status codes: 200, 201, 400, 401, 404, 429, 500
- Request structure: URL, headers, body, query parameters
- What APIs are and why they exist
- REST API design principles
- The requests library — Python's most popular HTTP library
- requests.get(), requests.post() with params and json
- response.status_code, response.json(), response.raise_for_status()
- Complete error handling: ConnectionError, Timeout, HTTPError
- Setting timeouts — never wait forever for a response
- API keys — what they are and how to use them safely in .env
- Caching API responses — avoid repeated calls for same data
- Multi-module project structure from Day 8 applied to real project

## 🔨 Project Built

**Weather CLI App** — Live weather data from OpenWeatherMap API:

- Searches any city worldwide for current weather
- Shows: temperature, feels like, min/max, humidity, wind, visibility, pressure
- Shows sunrise and sunset times
- 5-day forecast with daily min/max temperatures
- Clothing and activity recommendations based on conditions
- Weather warnings for extreme conditions
- Caches results for 10 minutes to avoid redundant API calls
- Keeps history of last 10 searched cities
- Colored terminal output with colorama
- Full error handling for every possible failure mode

## 🚀 How to Run

```bash
cd Day-09-HTTP-APIs-Requests

python -m venv venv
source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your OpenWeatherMap API key
# Get free key at openweathermap.org

python src/main.py
```

## 🌐 API Used

OpenWeatherMap API (free tier)

- Current Weather: api.openweathermap.org/data/2.5/weather
- 5-Day Forecast: api.openweathermap.org/data/2.5/forecast
- Free tier: 60 calls/minute, 1,000,000 calls/month

## 🧠 Key Concepts

| Concept                       | What It Does                 |
| ----------------------------- | ---------------------------- |
| `requests.get(url)`           | Make HTTP GET request        |
| `response.json()`             | Parse JSON response body     |
| `response.raise_for_status()` | Raise error for 4xx/5xx      |
| `params={}`                   | Add query string parameters  |
| `headers={}`                  | Add request headers          |
| `timeout=(5, 15)`             | Set connect and read timeout |
| `json={}`                     | Send JSON in POST body       |
| `.env`                        | Store API keys safely        |
| Cache                         | Avoid repeated API calls     |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
