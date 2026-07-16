# ============================================================
# src/display.py
# Handles all terminal display/formatting
# ============================================================

from colorama import init, Fore, Back, Style

# Initialize colorama (required for Windows color support)
init(autoreset=True)


def print_header(text):
    """Print a colored section header."""
    print(f"\n{Fore.CYAN}{'=' * 58}")
    print(f"{Fore.CYAN}  {text}")
    print(f"{Fore.CYAN}{'=' * 58}{Style.RESET_ALL}")


def print_success(text):
    """Print green success message."""
    print(f"{Fore.GREEN}  ✅ {text}{Style.RESET_ALL}")


def print_error(text):
    """Print red error message."""
    print(f"{Fore.RED}  ❌ {text}{Style.RESET_ALL}")


def print_warning(text):
    """Print yellow warning message."""
    print(f"{Fore.YELLOW}  ⚠️  {text}{Style.RESET_ALL}")


def print_info(text):
    """Print blue info message."""
    print(f"{Fore.BLUE}  ℹ️  {text}{Style.RESET_ALL}")


def display_current_weather(weather, from_cache=False):
    """
    Display current weather in a formatted layout.

    Args:
        weather (dict): Parsed weather data.
        from_cache (bool): Whether data came from cache.
    """
    icon = get_weather_icon_display(weather["main_condition"])
    cache_label = f"{Fore.YELLOW}[CACHED]{Style.RESET_ALL}" if from_cache else ""

    print_header(
        f"CURRENT WEATHER — {weather['city']}, "
        f"{weather['country']} {cache_label}"
    )

    # Main temperature display
    print(f"\n  {icon}  {Fore.YELLOW}{weather['temperature']}"
          f"{weather['temp_unit']}{Style.RESET_ALL}  "
          f"— {weather['description']}")
    print(f"       Feels like {weather['feels_like']}{weather['temp_unit']}")
    print(f"       Min: {weather['temp_min']}{weather['temp_unit']}  "
          f"Max: {weather['temp_max']}{weather['temp_unit']}")

    # Details grid
    print(f"\n  {Fore.CYAN}{'─' * 54}{Style.RESET_ALL}")
    print(f"  {'💧 Humidity':<22} {weather['humidity']}%")
    print(f"  {'💨 Wind':<22} {weather['wind_speed']} {weather['speed_unit']} "
          f"{weather['wind_direction']}"
          + (f" (gusts {weather['wind_gust']} {weather['speed_unit']})"
             if weather['wind_gust'] > 0 else ""))
    print(f"  {'👁️  Visibility':<22} {weather['visibility']} km")
    print(f"  {'☁️  Cloud Cover':<22} {weather['cloud_cover']}%")
    print(f"  {'📊 Pressure':<22} {weather['pressure']} hPa")
    print(f"  {'🌅 Sunrise':<22} {weather['sunrise']}")
    print(f"  {'🌇 Sunset':<22} {weather['sunset']}")
    print(f"  {Fore.CYAN}{'─' * 54}{Style.RESET_ALL}")


def display_forecast(forecast):
    """
    Display 5-day weather forecast.

    Args:
        forecast (list): List of daily forecast dictionaries.
    """
    print_header("5-DAY FORECAST")

    print(f"\n  {'Day':<12} {'Icon':<6} {'Condition':<16} "
          f"{'Min':>5} {'Max':>5} {'Humidity':>9}")
    print(f"  {'─' * 54}")

    for day in forecast:
        unit = day['temp_unit']
        print(
            f"  {day['day']:<12} "
            f"{day['icon']:<6} "
            f"{day['condition']:<16} "
            f"{day['temp_min']:>4}{unit} "
            f"{day['temp_max']:>4}{unit} "
            f"{day['avg_humidity']:>8}%"
        )

    print(f"  {'─' * 54}")


def display_recommendations(recommendations):
    """
    Display clothing and activity recommendations.

    Args:
        recommendations (dict): Recommendations dictionary.
    """
    print_header("RECOMMENDATIONS")

    # Warnings first (most important)
    if recommendations["warnings"]:
        print(f"\n  {Fore.RED}WARNINGS:{Style.RESET_ALL}")
        for warning in recommendations["warnings"]:
            print_warning(warning)

    # Clothing
    print(f"\n  {Fore.CYAN}👗 What to wear:{Style.RESET_ALL}")
    for item in recommendations["clothing"]:
        print(f"     • {item}")

    # Activities
    print(f"\n  {Fore.GREEN}🎯 Activities:{Style.RESET_ALL}")
    for activity in recommendations["activities"]:
        print(f"     • {activity}")


def display_history(history):
    """Display recent search history."""
    print_header("RECENT SEARCHES")

    if not history:
        print_info("No search history yet.")
        return

    for i, entry in enumerate(history, 1):
        print(f"  {i:>2}. {entry['city']}, {entry['country']}"
              f"  {Fore.YELLOW}({entry['searched_at']}){Style.RESET_ALL}")


def get_weather_icon_display(condition):
    """Return display icon for weather condition."""
    icons = {
        "Clear": "☀️ ",
        "Clouds": "☁️ ",
        "Rain": "🌧️ ",
        "Drizzle": "🌦️ ",
        "Thunderstorm": "⛈️ ",
        "Snow": "❄️ ",
        "Mist": "🌫️",
        "Fog": "🌫️",
        "Haze": "🌫️",
        "Dust": "🌪️",
        "Tornado": "🌪️"
    }
    return icons.get(condition, "🌡️")