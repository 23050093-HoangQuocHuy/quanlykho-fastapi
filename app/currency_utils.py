import httpx

async def get_exchange_rate(base: str = "CAD", target: str = "USD"):
    url = f"https://api.frankfurter.app/latest?from={base}&to={target}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        return data["rates"][target]