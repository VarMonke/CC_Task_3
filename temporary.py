import aiohttp
import asyncio
import random

BASE_URL = "http://127.0.0.1:8000/inventory"

brands = ["Nike", "Adidas", "Puma"]
items = ["T-shirt", "Jacket", "Shorts"]

ADMIN_CREDENTIALS = {
    "username": "shopkeeper",
    "password": "adminpass"
}

async def get_admin_token():
    """Login as admin and return the access token."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://127.0.0.1:8000/auth/admin/login",
            data=ADMIN_CREDENTIALS  # form-encoded, not JSON
        ) as resp:
            resp_json = await resp.json()
            if "access_token" not in resp_json:
                raise Exception(f"Login failed: {resp_json}")
            return resp_json["access_token"]

async def populate_inventory():
    ADMIN_TOKEN = await get_admin_token()
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

    async with aiohttp.ClientSession() as session:
        for brand in brands:
            for name in items:
                stock = random.randint(20, 50)
                price = random.randint(500, 2000)
                data = {
                    "name": name,
                    "brand": brand,
                    "description": f"{brand} {name}",
                    "category": "Clothing",
                    "quantity": str(stock),  # string is fine for Form
                    "price": str(price)
                }
                async with session.post(f"{BASE_URL}/new", data=data, headers=headers) as resp:
                    print(resp.status)
                    print(await resp.json())

if __name__ == "__main__":
    asyncio.run(populate_inventory())
