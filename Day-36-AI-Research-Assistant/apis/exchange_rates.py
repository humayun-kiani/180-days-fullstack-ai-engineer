# apis/exchange_rates.py
import httpx

COMMON = ["USD", "EUR", "GBP", "JPY", "PKR", "AED", "SAR", "CAD", "AUD", "INR"]


async def get_rates(base: str = "USD") -> dict:
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(f"https://open.er-api.com/v6/latest/{base.upper()}")
            r.raise_for_status()
            data = r.json()
        all_rates = data.get("rates", {})
        return {
            "base": base.upper(),
            "rates": {c: round(all_rates[c], 4) for c in COMMON if c in all_rates},
            "updated": data.get("time_last_update_utc", "")[:16]
        }
    except Exception as e:
        return {"error": str(e)}


async def convert_currency(amount: float, from_c: str, to_c: str) -> dict:
    data = await get_rates(from_c)
    if "error" in data:
        return data
    rate = data["rates"].get(to_c.upper())
    if rate is None:
        return {"error": f"Currency {to_c} not found"}
    return {
        "amount": amount, "from": from_c.upper(), "to": to_c.upper(),
        "result": round(amount * rate, 2), "rate": rate
    }