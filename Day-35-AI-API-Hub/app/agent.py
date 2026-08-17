# ============================================================
# app/agent.py
# AI API Hub Agent using raw Anthropic tool calling
# ============================================================

import json
import os
import time
import asyncio
from typing import Optional

import anthropic
from dotenv import load_dotenv

from apis.weather import get_weather
from apis.github_api import get_repo_info, get_trending_repos, get_user_profile
from apis.exchange_rates import get_exchange_rates, convert_currency
from apis.hackernews import get_top_stories
from apis.countries import get_country_info

load_dotenv()


# ─── Tool Schemas ─────────────────────────────────────────────

TOOLS = [
    {
        "name": "get_weather",
        "description": """Get current weather for a city.

Use this when the user asks about:
- Current weather conditions
- Temperature, rain, wind in a city
- Whether to bring an umbrella, jacket
- Travel conditions in a city

Returns: temperature, feels-like, precipitation, wind speed, humidity, condition.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, e.g. 'Karachi', 'London', 'New York'"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "get_github_repo",
        "description": """Get information about a GitHub repository.

Use this when the user asks about:
- A specific GitHub project or library
- Stars, forks, issues for a repo
- Whether a library is actively maintained
- What language a project uses

Args: owner/repo format like 'fastapi/fastapi' or 'microsoft/vscode'.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner, e.g. 'fastapi', 'microsoft'"
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name, e.g. 'fastapi', 'vscode'"
                }
            },
            "required": ["owner", "repo"]
        }
    },
    {
        "name": "get_trending_github",
        "description": """Get trending GitHub repositories.

Use when the user asks about:
- What's popular on GitHub right now
- Trending Python/JavaScript/etc. repos
- New interesting projects this week
- What developers are excited about""",
        "input_schema": {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "description": "Programming language filter, e.g. 'python', 'javascript'. Leave empty for all."
                },
                "since": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly"],
                    "description": "Time period for trending"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_exchange_rate",
        "description": """Get current currency exchange rates.

Use when the user asks about:
- Currency conversion (e.g., 100 USD to PKR)
- Current exchange rate between currencies
- How much something costs in another currency
- Forex rates""",
        "input_schema": {
            "type": "object",
            "properties": {
                "base_currency": {
                    "type": "string",
                    "description": "Base currency code, e.g. 'USD', 'EUR', 'GBP', 'PKR'"
                },
                "convert_to": {
                    "type": "string",
                    "description": "Target currency code for conversion (optional)"
                },
                "amount": {
                    "type": "number",
                    "description": "Amount to convert (optional, for conversion)"
                }
            },
            "required": ["base_currency"]
        }
    },
    {
        "name": "get_hackernews_stories",
        "description": """Get top stories from Hacker News (tech community news).

Use when the user asks about:
- What's trending in tech today
- Top tech news
- What the developer community is discussing
- Latest tech stories""",
        "input_schema": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Number of stories to return (1-10)",
                    "default": 5
                },
                "story_type": {
                    "type": "string",
                    "enum": ["top", "new", "best", "ask", "show"],
                    "description": "Type of stories to fetch"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_country_info",
        "description": """Get information about a country.

Use when the user asks about:
- Population, capital, area of a country
- Languages spoken in a country
- Currency used in a country
- Country's region and neighboring countries""",
        "input_schema": {
            "type": "object",
            "properties": {
                "country": {
                    "type": "string",
                    "description": "Country name, e.g. 'Pakistan', 'Germany', 'Japan'"
                }
            },
            "required": ["country"]
        }
    }
]

SYSTEM_PROMPT = """You are a helpful AI assistant with access to real-time data from multiple APIs.

You can:
- Check current weather in cities around the world
- Look up GitHub repositories and trending projects
- Get live currency exchange rates and do conversions
- Fetch top stories from Hacker News (tech news)
- Get detailed country information

When you have the data, synthesize a clear, helpful response.
If multiple APIs are relevant, call them all (in parallel when possible).
Always cite where the data comes from (e.g., "According to Open-Meteo...")."""


# ─── Tool Execution ───────────────────────────────────────────

async def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name and return JSON string result."""
    try:
        if tool_name == "get_weather":
            result = await get_weather(tool_input["city"])

        elif tool_name == "get_github_repo":
            result = await get_repo_info(tool_input["owner"], tool_input["repo"])

        elif tool_name == "get_trending_github":
            result = await get_trending_repos(
                language=tool_input.get("language", ""),
                since=tool_input.get("since", "daily")
            )

        elif tool_name == "get_exchange_rate":
            base = tool_input["base_currency"]
            convert_to = tool_input.get("convert_to")
            amount = tool_input.get("amount")

            if convert_to and amount is not None:
                result = await convert_currency(amount, base, convert_to)
            else:
                result = await get_exchange_rates(base)

        elif tool_name == "get_hackernews_stories":
            result = await get_top_stories(
                count=tool_input.get("count", 5),
                story_type=tool_input.get("story_type", "top")
            )

        elif tool_name == "get_country_info":
            result = await get_country_info(tool_input["country"])

        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e), "tool": tool_name})


# ─── Mock Agent ───────────────────────────────────────────────

class MockAPIHubAgent:
    """Mock agent that uses real API calls but simulates LLM routing."""

    async def run(self, user_message: str) -> dict:
        """Route to correct API based on keywords, return real data."""
        message_lower = user_message.lower()
        tool_calls = []
        results = {}

        # Determine which tools to call
        if any(w in message_lower for w in ["weather", "temperature", "rain", "hot", "cold"]):
            city = "Karachi"  # default
            for known_city in ["karachi", "lahore", "london", "new york", "dubai", "tokyo"]:
                if known_city in message_lower:
                    city = known_city.title()
                    break
            tool_calls.append(("get_weather", {"city": city}))

        if any(w in message_lower for w in ["github", "repo", "repository", "stars", "trending"]):
            if "trending" in message_lower:
                lang = ""
                for l in ["python", "javascript", "typescript", "go", "rust"]:
                    if l in message_lower:
                        lang = l
                        break
                tool_calls.append(("get_trending_github", {"language": lang, "since": "weekly"}))
            elif "/" in user_message:
                # Looks like owner/repo
                parts = [p.strip() for p in user_message.split("/") if p.strip()]
                if len(parts) >= 2:
                    tool_calls.append(("get_github_repo", {"owner": parts[-2], "repo": parts[-1]}))
            else:
                tool_calls.append(("get_github_repo", {"owner": "tiangolo", "repo": "fastapi"}))

        if any(w in message_lower for w in ["exchange", "currency", "usd", "pkr", "eur", "convert", "rate"]):
            tool_calls.append(("get_exchange_rate", {"base_currency": "USD"}))

        if any(w in message_lower for w in ["news", "hacker", "tech", "trending", "story", "stories"]):
            tool_calls.append(("get_hackernews_stories", {"count": 5, "story_type": "top"}))

        if any(w in message_lower for w in ["country", "pakistan", "population", "capital", "language"]):
            country = "Pakistan"
            for c in ["pakistan", "india", "germany", "france", "japan", "china", "usa", "uk"]:
                if c in message_lower:
                    country = c.title()
                    break
            tool_calls.append(("get_country_info", {"country": country}))

        if not tool_calls:
            tool_calls.append(("get_hackernews_stories", {"count": 5, "story_type": "top"}))

        # Execute tools in parallel
        print(f"  🔧 Calling {len(tool_calls)} API(s) in parallel...")
        tasks = [execute_tool(name, inputs) for name, inputs in tool_calls]
        raw_results = await asyncio.gather(*tasks)

        for (name, _), result_str in zip(tool_calls, raw_results):
            results[name] = json.loads(result_str)
            print(f"  ✅ {name}: data received")

        # Format answer
        answer_parts = [f"Here's the real-time information you requested:\n"]

        for tool_name, data in results.items():
            if "error" in data:
                answer_parts.append(f"**{tool_name}**: Error - {data['error']}")
            elif tool_name == "get_weather":
                answer_parts.append(
                    f"**Weather in {data.get('city')}** (Open-Meteo):\n"
                    f"  🌡️ {data.get('temperature_c')}°C (feels like {data.get('feels_like_c')}°C)\n"
                    f"  ☁️ {data.get('condition')}\n"
                    f"  💧 Humidity: {data.get('humidity_pct')}% | Wind: {data.get('wind_speed_kmh')} km/h"
                )
            elif tool_name == "get_exchange_rate":
                rates = data.get("rates", {})
                selected = {k: rates[k] for k in ["PKR", "EUR", "GBP", "AED"] if k in rates}
                answer_parts.append(
                    f"**Exchange Rates** (1 {data.get('base_currency')}) | Open Exchange Rates:\n"
                    + "\n".join(f"  {k}: {v}" for k, v in selected.items())
                )
            elif tool_name == "get_hackernews_stories":
                stories = data.get("stories", [])[:3]
                answer_parts.append(
                    "**Top Tech Stories** (Hacker News):\n"
                    + "\n".join(
                        f"  {i+1}. {s['title']} ⬆{s['score']}"
                        for i, s in enumerate(stories)
                    )
                )
            elif tool_name == "get_github_repo":
                answer_parts.append(
                    f"**{data.get('full_name')}** (GitHub):\n"
                    f"  ⭐ {data.get('stars'):,} stars | 🍴 {data.get('forks')} forks\n"
                    f"  {data.get('description', 'No description')}\n"
                    f"  Language: {data.get('language')} | Issues: {data.get('open_issues')}"
                )
            elif tool_name == "get_trending_github":
                repos = data.get("trending_repos", [])[:3]
                answer_parts.append(
                    f"**Trending on GitHub** ({data.get('period')}):\n"
                    + "\n".join(
                        f"  {i+1}. {r['name']} ⭐{r['stars']} [{r['language']}]"
                        for i, r in enumerate(repos)
                    )
                )
            elif tool_name == "get_country_info":
                answer_parts.append(
                    f"**{data.get('name')}** (REST Countries):\n"
                    f"  🏛️ Capital: {data.get('capital')}\n"
                    f"  👥 Population: {data.get('population', 0):,}\n"
                    f"  🗣️ Languages: {', '.join(data.get('languages', []))[:50]}\n"
                    f"  💱 Currency: {', '.join(data.get('currencies', {}).keys())}"
                )

        return {
            "answer": "\n\n".join(answer_parts),
            "tools_called": [name for name, _ in tool_calls],
            "data": results
        }


# ─── Real Agent (with Claude) ─────────────────────────────────

class APIHubAgent:
    """Full agent using Claude for intelligent routing."""

    MAX_ITERATIONS = 8

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key and api_key != "your-api-key-here":
            self.client = anthropic.Anthropic(api_key=api_key)
            self.mock = False
        else:
            self.client = None
            self.mock = True
            self._mock_agent = MockAPIHubAgent()

    async def run(self, user_message: str) -> dict:
        """
        Run the agent with the given message.

        Returns dict with answer, tools_called, data.
        """
        if self.mock:
            return await self._mock_agent.run(user_message)

        return await self._run_with_claude(user_message)

    async def _run_with_claude(self, user_message: str) -> dict:
        """Full Claude-powered agent loop with tool calling."""
        messages = [{"role": "user", "content": user_message}]
        tools_called = []
        all_data = {}

        for iteration in range(self.MAX_ITERATIONS):
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages
            )

            messages.append({
                "role": "assistant",
                "content": response.content
            })

            if response.stop_reason == "end_turn":
                final_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_text = block.text
                        break
                return {
                    "answer": final_text,
                    "tools_called": tools_called,
                    "data": all_data
                }

            if response.stop_reason == "tool_use":
                tool_blocks = [b for b in response.content if b.type == "tool_use"]
                print(f"  🔧 Claude calls {len(tool_blocks)} tool(s) simultaneously")

                # Execute ALL tool calls in parallel
                tasks = [
                    execute_tool(block.name, block.input)
                    for block in tool_blocks
                ]
                results = await asyncio.gather(*tasks)

                tool_results = []
                for block, result_str in zip(tool_blocks, results):
                    tools_called.append(block.name)
                    result_data = json.loads(result_str)
                    all_data[block.name] = result_data

                    print(f"  ✅ {block.name}: done")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str
                    })

                messages.append({"role": "user", "content": tool_results})

        return {
            "answer": "I reached the maximum number of iterations.",
            "tools_called": tools_called,
            "data": all_data
        }