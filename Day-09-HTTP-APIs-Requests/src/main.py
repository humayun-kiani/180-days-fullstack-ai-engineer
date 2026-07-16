# ============================================================
# src/main.py
# Weather CLI App — Main Entry Point
# Day 09 - 180 Days Full Stack AI Engineer Roadmap
# ============================================================

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.weather_api import (
    WeatherAPIError,
    fetch_current_weather,
    fetch_forecast,
    parse_current_weather,
    parse_forecast,
    get_recommendations
)
from src.cache import (
    get_cached_weather,
    set_cached_weather,
    add_to_history,
    get_history,
    clear_cache
)
from src.display import (
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
    display_current_weather,
    display_forecast,
    display_recommendations,
    display_history
)


def get_api_key():
    """Get API key from environment variables."""
    api_key = os.environ.get("OPENWEATHER_API_KEY", "").strip()
    if not api_key or api_key == "your_actual_api_key_here":
        print_error(
            "No API key found!\n"
            "  1. Get a free key at openweathermap.org\n"
            "  2. Add it to your .env file:\n"
            "     OPENWEATHER_API_KEY=your_key_here"
        )
        return None
    return api_key


def get_units():
    """Get units setting from environment."""
    units = os.environ.get("UNITS", "metric").lower()
    if units not in ["metric", "imperial", "standard"]:
        return "metric"
    return units


def get_cache_minutes():
    """Get cache duration from environment."""
    try:
        return int(os.environ.get("CACHE_DURATION_MINUTES", "10"))
    except ValueError:
        return 10


def fetch_and_display_weather(city, api_key, units, cache_minutes):
    """
    Fetch weather data for a city and display it.

    Args:
        city (str): City name to search.
        api_key (str): OpenWeatherMap API key.
        units (str): Unit system.
        cache_minutes (int): Cache duration in minutes.
    """
    city = city.strip()
    if not city:
        print_error("City name cannot be empty.")
        return

    # Check cache first
    cached = get_cached_weather(city, cache_minutes)
    from_cache = False

    if cached:
        print_info(f"Using cached data for {city} "
                   f"(cached within last {cache_minutes} minutes)")
        weather = cached["weather"]
        forecast = cached["forecast"]
        from_cache = True
    else:
        # Fetch from API
        print_info(f"Fetching live weather for '{city}'...")

        try:
            # Fetch current weather
            raw_weather = fetch_current_weather(city, api_key, units)
            weather = parse_current_weather(raw_weather, units)

            # Fetch forecast
            raw_forecast = fetch_forecast(city, api_key, units)
            forecast = parse_forecast(raw_forecast, units)

            # Cache the results
            set_cached_weather(city, weather, forecast)

            # Add to search history
            add_to_history(weather["city"], weather["country"])

            print_success(
                f"Data fetched for {weather['city']}, "
                f"{weather['country']}"
            )

        except WeatherAPIError as e:
            print_error(str(e))
            return

    # Display everything
    display_current_weather(weather, from_cache)
    display_forecast(forecast)

    # Show recommendations
    recommendations = get_recommendations(weather)
    display_recommendations(recommendations)


def main():
    """Main function — Weather CLI App."""

    print_header("WEATHER CLI APP — Day 09")
    print("  Live weather data from OpenWeatherMap API")
    print("  Type a city name to get its weather")

    # Validate setup
    api_key = get_api_key()
    if not api_key:
        print("\n  Running in DEMO MODE — showing sample output structure")
        print("  To get real data: add your API key to .env file")
        api_key = None

    units = get_units()
    cache_minutes = get_cache_minutes()

    unit_labels = {
        "metric": "Celsius (°C)",
        "imperial": "Fahrenheit (°F)",
        "standard": "Kelvin (K)"
    }
    print_info(f"Units: {unit_labels.get(units, units)}")
    print_info(f"Cache duration: {cache_minutes} minutes")

    while True:
        print("\n" + "─" * 58)
        print("  MENU")
        print("─" * 58)
        print("  1. Search city weather")
        print("  2. View search history")
        print("  3. Clear cache")
        print("  4. Exit")
        print("─" * 58)

        choice = input("  Choose option (1-4): ").strip()

        if choice == "1":
            if not api_key:
                print_error(
                    "Cannot fetch weather without API key.\n"
                    "  Add OPENWEATHER_API_KEY to your .env file."
                )
                continue

            city = input("\n  Enter city name: ").strip()
            if city:
                fetch_and_display_weather(
                    city, api_key, units, cache_minutes
                )

        elif choice == "2":
            history = get_history()
            display_history(history)

        elif choice == "3":
            clear_cache()
            print_success("Cache cleared. Next search will fetch fresh data.")

        elif choice == "4":
            print_header("GOODBYE!")
            print("  See you on Day 10! 💪")
            break

        else:
            print_error("Invalid option. Choose between 1 and 4.")


if __name__ == "__main__":
    main()