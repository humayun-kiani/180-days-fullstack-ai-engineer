# ============================================================
# apis/exchange_rates.py
# Open Exchange Rates API (free tier)
# ============================================================

import httpx
from app.rate_limiter import RATE_LIMITERS

BASE_URL = "https://open.er-api.com/v6"


async def get_exchange_rates(base_currency: str = "USD") -> dict:
    """
    Get current exchange rates for a base currency.

    Args:
        base_currency: Base currency code (e.g., USD, EUR, GBP)

    Returns:
        dict: Exchange rates against common currencies
    """
    await RATE_LIMITERS["exchange_rate"].acquire()

    currency = base_currency.upper().strip()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/latest/{currency}")

            if response.status_code == 404:
                return {"error": f"Currency '{currency}' not supported"}
            response.raise_for_status()
            data = response.json()

        if data.get("result") == "error":
            return {"error": data.get("error-type", "Unknown error")}

        all_rates = data.get("rates", {})

        # Return only the most commonly used currencies
        common_currencies = [
            "USD", "EUR", "GBP", "JPY", "PKR", "AED", "SAR", "CAD",
            "AUD", "CHF", "CNY", "INR", "SGD", "HKD", "NOK", "SEK"
        ]

        filtered_rates = {
            currency: round(all_rates[currency], 4)
            for currency in common_currencies
            if currency in all_rates
        }

        return {
            "base_currency": currency,
            "rates": filtered_rates,
            "last_updated": data.get("time_last_update_utc", "")[:16],
            "next_update": data.get("time_next_update_utc", "")[:16]
        }

    except httpx.TimeoutException:
        return {"error": "Exchange rate API timed out"}
    except Exception as e:
        return {"error": str(e)}


async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str
) -> dict:
    """
    Convert an amount from one currency to another.

    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code

    Returns:
        dict: Conversion result
    """
    rates_data = await get_exchange_rates(from_currency.upper())

    if "error" in rates_data:
        return rates_data

    rates = rates_data.get("rates", {})
    to_curr = to_currency.upper()

    if to_curr not in rates:
        return {
            "error": f"Target currency '{to_curr}' not found",
            "available": list(rates.keys())[:20]
        }

    converted = amount * rates[to_curr]

    return {
        "original_amount": amount,
        "from_currency": from_currency.upper(),
        "to_currency": to_curr,
        "converted_amount": round(converted, 2),
        "exchange_rate": rates[to_curr],
        "last_updated": rates_data.get("last_updated", "")
    }