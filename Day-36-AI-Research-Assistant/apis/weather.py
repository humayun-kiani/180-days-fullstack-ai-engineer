# apis/weather.py
import httpx

CITY_COORDS = {
    "karachi": (24.8607, 67.0011, "Asia/Karachi"),
    "lahore": (31.5497, 74.3436, "Asia/Karachi"),
    "islamabad": (33.7294, 73.0931, "Asia/Karachi"),
    "london": (51.5074, -0.1278, "Europe/London"),
    "new york": (40.7128, -74.0060, "America/New_York"),
    "dubai": (25.2048, 55.2708, "Asia/Dubai"),
    "san francisco": (37.7749, -122.4194, "America/Los_Angeles"),
}

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    51: "Light drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    80: "Rain showers", 95: "Thunderstorm",
}


async def get_weather(city: str) -> dict:
    city_lower = city.lower().strip()
    coords = CITY_COORDS.get(city_lower)
    if not coords:
        return {"error": f"City '{city}' not in supported list", "city": city}
    lat, lon, tz = coords
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat, "longitude": lon,
                    "current": "temperature_2m,apparent_temperature,precipitation,wind_speed_10m,relative_humidity_2m,weathercode,is_day",
                    "timezone": tz, "forecast_days": 1
                }
            )
            r.raise_for_status()
            data = r.json()
        cur = data.get("current", {})
        code = cur.get("weathercode", 0)
        return {
            "city": city.title(), "temperature_c": cur.get("temperature_2m"),
            "feels_like_c": cur.get("apparent_temperature"),
            "precipitation_mm": cur.get("precipitation", 0),
            "wind_speed_kmh": cur.get("wind_speed_10m"),
            "humidity_pct": cur.get("relative_humidity_2m"),
            "condition": WMO_CODES.get(code, f"Code {code}"),
            "is_day": bool(cur.get("is_day", 1))
        }
    except Exception as e:
        return {"error": str(e), "city": city}