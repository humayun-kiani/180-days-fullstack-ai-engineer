# ============================================================
# apis/countries.py
# REST Countries API (free, no key required)
# ============================================================

import httpx
from app.rate_limiter import RATE_LIMITERS

BASE_URL = "https://restcountries.com/v3.1"


async def get_country_info(country_name: str) -> dict:
    """
    Get information about a country.

    Args:
        country_name: Country name (e.g., "Pakistan", "France")

    Returns:
        dict: Country information
    """
    await RATE_LIMITERS["restcountries"].acquire()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BASE_URL}/name/{country_name}",
                params={"fields": "name,capital,population,area,currencies,languages,region,subregion,flags,timezones,borders"}
            )

            if response.status_code == 404:
                return {"error": f"Country '{country_name}' not found"}
            response.raise_for_status()
            data = response.json()

        if not data:
            return {"error": f"No data for '{country_name}'"}

        # Take the first result (most relevant)
        country = data[0]

        # Transform currencies
        currencies = {}
        for code, info in country.get("currencies", {}).items():
            currencies[code] = {
                "name": info.get("name"),
                "symbol": info.get("symbol")
            }

        # Transform languages
        languages = list(country.get("languages", {}).values())

        # Common name
        names = country.get("name", {})
        common_name = names.get("common", country_name)
        official_name = names.get("official", common_name)

        return {
            "name": common_name,
            "official_name": official_name,
            "capital": country.get("capital", ["N/A"])[0] if country.get("capital") else "N/A",
            "population": country.get("population", 0),
            "area_km2": country.get("area", 0),
            "region": country.get("region"),
            "subregion": country.get("subregion"),
            "languages": languages[:5],
            "currencies": currencies,
            "timezones": country.get("timezones", [])[:3],
            "borders": country.get("borders", [])[:8],
            "flag_emoji": country.get("flags", {}).get("alt", ""),
        }

    except httpx.TimeoutException:
        return {"error": "REST Countries API timed out"}
    except Exception as e:
        return {"error": str(e)}