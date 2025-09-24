import asyncio
import random
import aiohttp

BASE_URL = "http://127.0.0.1:8000/inventory"

brands = ["Nike", "Adidas", "Puma"]
items = ["T-shirt", "Jacket", "Shorts"]


async def clear_inventory():
    """Delete all items in the inventory."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/items") as resp:
            data = await resp.json()
            for item in data:
                item_id = item["item_id"]
                async with session.delete(f"{BASE_URL}/items/{item_id}") as r:
                    print(await r.json())


async def populate_inventory():
    """Insert all brand × item combos with random stock."""
    async with aiohttp.ClientSession() as session:
        for brand in brands:
            for name in items:
                stock = random.randint(20, 50)
                async with session.post(f"{BASE_URL}/items", json={
                    "brand": brand,
                    "name": name,
                    "stock": stock
                }) as resp:
                    print(await resp.json())


async def list_inventory():
    """Print the final inventory."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/items") as resp:
            data = await resp.json()
            print("\nFinal Inventory:")
            for item in data:
                print(item)


async def main():
    await clear_inventory()
    await populate_inventory()
    await list_inventory()


if __name__ == "__main__":
    asyncio.run(main())
