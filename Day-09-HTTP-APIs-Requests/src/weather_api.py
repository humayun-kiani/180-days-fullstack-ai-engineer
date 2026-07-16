# ============================================================
# src/weather_api.py
# Handles all OpenWeatherMap API communication
# ============================================================

import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError, RequestException


# API Configuration
BASE_URL = "https://api.openweathermap.org/data/2.5"
GEOCODING_URL = "http://api.openweathermap.org/geo/1.0/direct"


class WeatherAPIError(Exception):
    """Custom exception for weather API errors."""
    pass


def fetch_current_weather(city, api_key, units="metric"):
    """
    Fetch current weather for a city.

    Args:
        city (str): City name (e.g. "Rawalpindi" or "London,GB").
        api_key (str): OpenWeatherMap API key.
        units (str): "metric" (Celsius), "imperial" (Fahrenheit), "standard" (Kelvin).

    Returns:
        dict: Weather data dictionary.

    Raises:
        WeatherAPIError: If the API call fails for any reason.
    """
    url = f"{BASE_URL}/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": units
    }

    try:
        response = requests.get(url, params=params, timeout=(5, 15))

        # Handle specific status codes with helpful messages
        if response.status_code == 401:
            raise WeatherAPIError(
                "Invalid API key. Check your OPENWEATHER_API_KEY in .env file.\n"
                "New keys can take 10-15 minutes to activate after signup."
            )

        if response.status_code == 404:
            raise WeatherAPIError(
                f"City '{city}' not found. Try adding country code: "
                f"'{city},PK' for Pakistan cities."
            )

        if response.status_code == 429:
            raise WeatherAPIError(
                "API rate limit exceeded. Wait 1 minute and try again."
            )

        response.raise_for_status()
        return response.json()

    except ConnectionError:
        raise WeatherAPIError(
            "No internet connection. Check your network and try again."
        )

    except Timeout:
        raise WeatherAPIError(
            "Request timed out. The weather server is slow. Try again."
        )

    except HTTPError as e:
        raise WeatherAPIError(f"HTTP error: {e}")

    except RequestException as e:
        raise WeatherAPIError(f"Request failed: {e}")


def fetch_forecast(city, api_key, units="metric"):
    """
    Fetch 5-day weather forecast (in 3-hour intervals).

    Args:
        city (str): City name.
        api_key (str): OpenWeatherMap API key.
        units (str): Temperature unit system.

    Returns:
        dict: Forecast data dictionary.
    """
    url = f"{BASE_URL}/forecast"
    params = {
        "q": city,
        "appid": api_key,
        "units": units,
        "cnt": 40    # 5 days x 8 readings per day (every 3 hours)
    }

    try:
        response = requests.get(url, params=params, timeout=(5, 15))
        response.raise_for_status()
        return response.json()

    except ConnectionError:
        raise WeatherAPIError("No internet connection.")
    except Timeout:
        raise WeatherAPIError("Forecast request timed out.")
    except HTTPError as e:
        if e.response.status_code == 404:
            raise WeatherAPIError(f"City '{city}' not found for forecast.")
        raise WeatherAPIError(f"Forecast HTTP error: {e}")
    except RequestException as e:
        raise WeatherAPIError(f"Forecast request failed: {e}")


def parse_current_weather(data, units="metric"):
    """
    Parse raw API response into a clean dictionary.

    Args:
        data (dict): Raw API response.
        units (str): Unit system to set correct symbols.

    Returns:
        dict: Clean parsed weather data.
    """
    temp_unit = "°C" if units == "metric" else "°F" if units == "imperial" else "K"
    speed_unit = "m/s" if units == "metric" else "mph"

    # Extract wind direction
    wind_deg = data.get("wind", {}).get("deg", 0)
    wind_direction = degrees_to_compass(wind_deg)

    # Convert Unix timestamps to readable time
    from datetime import datetime
    sunrise = datetime.fromtimestamp(
        data["sys"]["sunrise"]
    ).strftime("%I:%M %p")
    sunset = datetime.fromtimestamp(
        data["sys"]["sunset"]
    ).strftime("%I:%M %p")

    return {
        "city": data["name"],
        "country": data["sys"]["country"],
        "temperature": round(data["main"]["temp"], 1),
        "feels_like": round(data["main"]["feels_like"], 1),
        "temp_min": round(data["main"]["temp_min"], 1),
        "temp_max": round(data["main"]["temp_max"], 1),
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"],
        "description": data["weather"][0]["description"].title(),
        "main_condition": data["weather"][0]["main"],
        "wind_speed": round(data["wind"]["speed"], 1),
        "wind_direction": wind_direction,
        "wind_gust": round(data["wind"].get("gust", 0), 1),
        "visibility": data.get("visibility", 0) // 1000,  # meters to km
        "cloud_cover": data["clouds"]["all"],
        "sunrise": sunrise,
        "sunset": sunset,
        "temp_unit": temp_unit,
        "speed_unit": speed_unit
    }


def parse_forecast(data, units="metric"):
    """
    Parse forecast data into daily summaries.

    Args:
        data (dict): Raw forecast API response.
        units (str): Unit system.

    Returns:
        list: List of daily forecast dictionaries.
    """
    from datetime import datetime
    from collections import defaultdict

    temp_unit = "°C" if units == "metric" else "°F"
    daily = defaultdict(list)

    # Group 3-hour intervals by date
    for item in data["list"]:
        date_str = datetime.fromtimestamp(
            item["dt"]
        ).strftime("%Y-%m-%d")
        daily[date_str].append(item)

    # Build daily summary
    forecast = []
    for date_str, readings in list(daily.items())[:5]:    # max 5 days
        temps = [r["main"]["temp"] for r in readings]
        conditions = [r["weather"][0]["main"] for r in readings]
        humidity_vals = [r["main"]["humidity"] for r in readings]

        # Most common condition for the day
        most_common = max(set(conditions), key=conditions.count)

        # Parse display date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = date_obj.strftime("%A")
        if date_str == datetime.now().strftime("%Y-%m-%d"):
            day_name = "Today"

        forecast.append({
            "date": date_str,
            "day": day_name,
            "temp_min": round(min(temps), 1),
            "temp_max": round(max(temps), 1),
            "condition": most_common,
            "avg_humidity": round(sum(humidity_vals) / len(humidity_vals)),
            "temp_unit": temp_unit,
            "icon": get_weather_icon(most_common)
        })

    return forecast


def degrees_to_compass(degrees):
    """Convert wind direction in degrees to compass direction."""
    directions = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW"
    ]
    index = round(degrees / 22.5) % 16
    return directions[index]


def get_weather_icon(condition):
    """Return an emoji icon for a weather condition."""
    icons = {
        "Clear": "☀️",
        "Clouds": "☁️",
        "Rain": "🌧️",
        "Drizzle": "🌦️",
        "Thunderstorm": "⛈️",
        "Snow": "❄️",
        "Mist": "🌫️",
        "Fog": "🌫️",
        "Haze": "🌫️",
        "Dust": "🌪️",
        "Sand": "🌪️",
        "Smoke": "💨",
        "Tornado": "🌪️"
    }
    return icons.get(condition, "🌡️")


def get_recommendations(weather):
    """
    Generate clothing and activity recommendations based on weather.

    Args:
        weather (dict): Parsed weather data from parse_current_weather().

    Returns:
        dict: Recommendations dictionary.
    """
    temp = weather["temperature"]
    condition = weather["main_condition"]
    humidity = weather["humidity"]
    wind_speed = weather["wind_speed"]

    clothing = []
    activities = []
    warnings = []

    # Temperature based clothing
    if temp >= 35:
        clothing.extend(["Light cotton clothes", "Hat/cap", "Sunglasses"])
        warnings.append("Extreme heat! Stay hydrated and avoid direct sun.")
    elif temp >= 25:
        clothing.extend(["Light clothing", "Sunglasses"])
        activities.extend(["Perfect for outdoor activities"])
    elif temp >= 15:
        clothing.extend(["Light jacket", "Long sleeves"])
        activities.extend(["Great for a walk or run"])
    elif temp >= 5:
        clothing.extend(["Warm jacket", "Sweater", "Scarf"])
    else:
        clothing.extend(["Heavy coat", "Gloves", "Warm hat", "Boots"])
        warnings.append("Very cold! Dress in layers.")

    # Condition based additions
    if condition in ["Rain", "Drizzle"]:
        clothing.append("Raincoat or umbrella")
        warnings.append("Carry an umbrella!")
        activities.append("Indoor activities recommended")
    elif condition == "Thunderstorm":
        warnings.append("Dangerous storm! Stay indoors.")
        activities.append("Stay indoors — thunderstorm warning")
    elif condition == "Snow":
        clothing.extend(["Waterproof boots", "Warm layers"])
        warnings.append("Slippery roads — drive carefully.")
    elif condition == "Clear" and temp >= 20:
        activities.extend(["Great for a picnic", "Good for cycling"])

    # Humidity
    if humidity >= 80:
        warnings.append(f"High humidity ({humidity}%) — feels muggy.")
    elif humidity <= 20:
        warnings.append("Very dry air — stay hydrated.")

    # Wind
    if wind_speed >= 10:
        warnings.append(
            f"Strong winds ({wind_speed} m/s) — secure loose objects."
        )

    return {
        "clothing": clothing if clothing else ["Comfortable everyday wear"],
        "activities": activities if activities else ["Enjoy the weather!"],
        "warnings": warnings
    }