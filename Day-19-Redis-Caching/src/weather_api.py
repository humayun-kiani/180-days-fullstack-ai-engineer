# ============================================================
# src/weather_api.py
# Weather data fetching — real API or simulated fallback
# ============================================================

import os
import random
import requests
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5"

# Pakistani cities with realistic weather data for simulation
PAKISTAN_CITIES = {
    "rawalpindi": {
        "name": "Rawalpindi",
        "country": "PK",
        "lat": 33.6007,
        "lon": 73.0679,
        "temp_range": (15, 42),
        "humidity_range": (30, 80),
        "conditions": ["Clear", "Partly Cloudy", "Haze", "Thunderstorm"]
    },
    "lahore": {
        "name": "Lahore",
        "country": "PK",
        "lat": 31.5497,
        "lon": 74.3436,
        "temp_range": (12, 45),
        "humidity_range": (35, 85),
        "conditions": ["Clear", "Smoke", "Partly Cloudy", "Thunderstorm"]
    },
    "karachi": {
        "name": "Karachi",
        "country": "PK",
        "lat": 24.8607,
        "lon": 67.0011,
        "temp_range": (20, 42),
        "humidity_range": (55, 90),
        "conditions": ["Clear", "Partly Cloudy", "Humid", "Drizzle"]
    },
    "islamabad": {
        "name": "Islamabad",
        "country": "PK",
        "lat": 33.7294,
        "lon": 73.0931,
        "temp_range": (10, 38),
        "humidity_range": (35, 75),
        "conditions": ["Clear", "Partly Cloudy", "Rain", "Fog"]
    },
    "peshawar": {
        "name": "Peshawar",
        "country": "PK",
        "lat": 34.0151,
        "lon": 71.5249,
        "temp_range": (8, 44),
        "humidity_range": (25, 70),
        "conditions": ["Clear", "Dust", "Partly Cloudy", "Rain"]
    },
    "multan": {
        "name": "Multan",
        "country": "PK",
        "lat": 30.1575,
        "lon": 71.5249,
        "temp_range": (10, 50),
        "humidity_range": (20, 65),
        "conditions": ["Clear", "Haze", "Dust", "Partly Cloudy"]
    },
    "quetta": {
        "name": "Quetta",
        "country": "PK",
        "lat": 30.1798,
        "lon": 66.975,
        "temp_range": (-2, 36),
        "humidity_range": (20, 60),
        "conditions": ["Clear", "Snow", "Partly Cloudy", "Windy"]
    },
    "faisalabad": {
        "name": "Faisalabad",
        "country": "PK",
        "lat": 31.4504,
        "lon": 73.135,
        "temp_range": (8, 46),
        "humidity_range": (30, 80),
        "conditions": ["Clear", "Haze", "Partly Cloudy", "Thunderstorm"]
    },
}


def simulate_current_weather(city_key: str) -> dict:
    """
    Generate realistic simulated weather data.

    Used when no API key is provided or API fails.
    """
    city = PAKISTAN_CITIES.get(city_key.lower())
    if not city:
        # Generic simulation for unknown cities
        city = {
            "name": city_key.title(),
            "country": "PK",
            "temp_range": (15, 40),
            "humidity_range": (30, 70),
            "conditions": ["Clear", "Partly Cloudy"]
        }

    temp_min, temp_max = city["temp_range"]
    hum_min, hum_max = city["humidity_range"]
    temp = round(random.uniform(temp_min, temp_max), 1)
    humidity = random.randint(hum_min, hum_max)
    condition = random.choice(city["conditions"])
    wind_speed = round(random.uniform(2, 20), 1)
    feels_like = round(temp + random.uniform(-3, 3), 1)

    return {
        "city": city["name"],
        "country": city.get("country", "PK"),
        "temperature": temp,
        "feels_like": feels_like,
        "humidity": humidity,
        "condition": condition,
        "wind_speed": wind_speed,
        "wind_direction": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
        "visibility_km": round(random.uniform(3, 15), 1),
        "pressure_hpa": random.randint(1005, 1025),
        "uv_index": round(random.uniform(1, 11), 1),
        "sunrise": "06:15",
        "sunset": "19:45",
        "fetched_at": datetime.utcnow().isoformat(),
        "source": "simulated"
    }


def simulate_forecast(city_key: str, days: int = 5) -> dict:
    """Generate simulated 5-day forecast."""
    city = PAKISTAN_CITIES.get(city_key.lower(), {
        "name": city_key.title(),
        "temp_range": (15, 40),
        "conditions": ["Clear", "Partly Cloudy"]
    })

    temp_min_base, temp_max_base = city["temp_range"]
    forecast_days = []

    for i in range(days):
        date = datetime.utcnow() + timedelta(days=i)
        high = round(random.uniform(temp_max_base - 5, temp_max_base), 1)
        low = round(random.uniform(temp_min_base, temp_min_base + 8), 1)
        condition = random.choice(city["conditions"])
        rain_chance = random.randint(0, 80) if "rain" in condition.lower() else random.randint(0, 20)

        forecast_days.append({
            "date": date.strftime("%Y-%m-%d"),
            "day": date.strftime("%A"),
            "high": high,
            "low": low,
            "condition": condition,
            "humidity": random.randint(30, 80),
            "rain_chance_pct": rain_chance,
            "wind_speed": round(random.uniform(3, 15), 1)
        })

    return {
        "city": city["name"],
        "days": forecast_days,
        "fetched_at": datetime.utcnow().isoformat(),
        "source": "simulated"
    }


def fetch_current_weather_from_api(city: str) -> Optional[dict]:
    """Fetch real weather from OpenWeatherMap API."""
    if not API_KEY or API_KEY == "your_api_key_here":
        return None

    try:
        response = requests.get(
            f"{BASE_URL}/weather",
            params={
                "q": city,
                "appid": API_KEY,
                "units": "metric"
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        return {
            "city": data["name"],
            "country": data["sys"]["country"],
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "condition": data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "wind_speed": data["wind"].get("speed", 0),
            "wind_direction": data["wind"].get("deg", 0),
            "visibility_km": data.get("visibility", 0) / 1000,
            "pressure_hpa": data["main"]["pressure"],
            "fetched_at": datetime.utcnow().isoformat(),
            "source": "openweathermap"
        }
    except requests.exceptions.RequestException:
        return None


def get_current_weather(city: str) -> dict:
    """
    Get current weather — tries real API first, falls back to simulation.

    Args:
        city: City name.

    Returns:
        dict: Weather data.
    """
    real_data = fetch_current_weather_from_api(city)
    if real_data:
        return real_data
    return simulate_current_weather(city)


def get_forecast(city: str, days: int = 5) -> dict:
    """Get weather forecast for the next N days."""
    return simulate_forecast(city, days)