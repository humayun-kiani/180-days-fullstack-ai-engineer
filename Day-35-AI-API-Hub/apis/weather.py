# ============================================================
# apis/weather.py
# Open-Meteo weather API (free, no key required)
# ============================================================

import httpx
from dataclasses import dataclass
from typing import Optional
from app.rate_limiter import RATE_LIMITERS

BASE_URL = "https://api.open-meteo.com/v1"

# WMO weather code descriptions
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Heavy drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Heavy rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Heavy thunderstorm with hail",
}

# Coordinates for common cities
CITY_COORDS = {
    "karachi": (24.8607, 67.0011, "Asia/Karachi"),
    "lahore": (31.5497, 74.3436, "Asia/Karachi"),
    "islamabad": (33.7294, 73.0931, "Asia/Karachi"),
    "london": (51.5074, -0.1278, "Europe/London"),
    "new york": (40.7128, -74.0060, "America/New_York"),
    "dubai": (25.2048, 55.2708, "Asia/Dubai"),
    "san francisco": (37.7749, -122.4194, "America/Los_Angeles"),
    "tokyo": (35.6762, 139.6503, "Asia/Tokyo"),
    "paris": (48.8566, 2.3522, "Europe/Paris"),
    "sydney": (-33.8688, 151.2093, "Australia/Sydney"),
}


@dataclass
class WeatherData:
    """Transformed weather data."""
    city: str
    temperature_c: float
    feels_like_c: Optional[float]
    precipitation_mm: float
    wind_speed_kmh: float
    humidity_pct: Optional[float]
    condition: str
    uv_index: Optional[float]
    is_day: bool


async def get_weather(city: str) -> dict:
    """
    Get current weather for a city.

    Args:
        city: City name (case-insensitive)

    Returns:
        dict: Weather data or error
    """
    await RATE_LIMITERS["open_meteo"].acquire()

    city_lower = city.lower().strip()
    coords = CITY_COORDS.get(city_lower)

    if not coords:
        # Try a geocoding fallback for unknown cities
        # For demo, return error for unknown cities
        return {
            "error": f"City '{city}' not found. Known cities: {', '.join(CITY_COORDS.keys())}",
            "city": city
        }

    lat, lon, timezone = coords

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BASE_URL}/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": ",".join([
                        "temperature_2m",
                        "apparent_temperature",
                        "precipitation",
                        "wind_speed_10m",
                        "relative_humidity_2m",
                        "weathercode",
                        "uv_index",
                        "is_day"
                    ]),
                    "timezone": timezone,
                    "forecast_days": 1
                }
            )
            response.raise_for_status()
            data = response.json()

        current = data.get("current", {})
        weather_code = current.get("weathercode", 0)

        return {
            "city": city.title(),
            "temperature_c": current.get("temperature_2m"),
            "feels_like_c": current.get("apparent_temperature"),
            "precipitation_mm": current.get("precipitation", 0),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "humidity_pct": current.get("relative_humidity_2m"),
            "condition": WMO_CODES.get(weather_code, f"Code {weather_code}"),
            "uv_index": current.get("uv_index"),
            "is_day": bool(current.get("is_day", 1)),
            "latitude": lat,
            "longitude": lon,
            "timezone": timezone
        }

    except httpx.TimeoutException:
        return {"error": "Weather API timed out", "city": city}
    except Exception as e:
        return {"error": str(e), "city": city}