from typing import (
    Dict,
    List,
)

import datetime
from fastapi import APIRouter, Depends, Form, HTTPException

from database import APIDatabase, get_db
from routes.auth import sessions

router = APIRouter(prefix="/cart", tags=["cart"])
carts: Dict[str, List[Dict[str, int]]]= {} 


@router.post("/add")
async def add_to_cart(token: str = Form(...), item_id: int = Form(...), quantity: int = Form(...)):
    """
    Adds the given item to the cart assosiated to the current access token.
    """
    session = sessions.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    if token not in carts:
        carts[token] = []


    for entry in carts[token]:
        if entry["item_id"] == item_id:
            entry["quantity"] += quantity
            break
    else:
        carts[token].append({"item_id": item_id, "quantity": quantity})

    return {"msg": f"Added {quantity} units of item {item_id} to cart"}

@router.get("/info")
async def cart_info(token: str = Form(...), db: APIDatabase = Depends(get_db)):
    """
    Returns complete data about the cart assosiated to the current access token.
    """
    session = sessions.get(token)
    if not session or token not in carts:
        return {"items": [], "total_price": 0}

    cart_items = []
    total = 0
    for entry in carts[token]:
        item = await db.get_item(entry["item_id"])
        if not item:
            continue
        subtotal = item["price"] * entry["quantity"]
        cart_items.append({
            "item_id": item["id"],
            "name": item["name"],
            "quantity": entry["quantity"],
            "price": item["price"],
            "subtotal": subtotal
        })
        total += subtotal

    return {"items": cart_items, "total_price": total}

@router.post("/remove")
async def remove_from_cart(token: str = Form(...), item_id: int = Form(...)):
    """
    Removes items from the cart assosiated to the current access token.
    """
    if token not in carts:
        return {"msg": "Cart empty"}

    carts[token] = [e for e in carts[token] if e["item_id"] != item_id]
    return {"msg": f"Item {item_id} removed from cart"}

@router.post("/checkout")
async def checkout_cart(
    token: str = Form(...),
    db: APIDatabase = Depends(get_db)
):
    """
    Creates an order for every item in the cart and empties the cart assosiated to the current access token.
    """
    session = sessions.get(token)
    if not session or token not in carts or not carts[token]:
        raise HTTPException(status_code=400, detail="Cart is empty")
    user_id = session["user_id"]

    order_ids = []
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for entry in carts[token]:
        item = await db.get_item(entry["item_id"])
        if not item or item["quantity"] < entry["quantity"]:
            continue

        total_price = item["price"] * entry["quantity"]
        await db.conn.execute(
            "INSERT INTO orders (user_id, item_id, quantity, total_price, date_ordered) VALUES (?, ?, ?, ?, ?)",
            (user_id, item["id"], entry["quantity"], total_price, now)
        )
        await db.conn.execute(
            "UPDATE items SET quantity = quantity - ? WHERE id = ?",
            (entry["quantity"], item["id"])
        )
        cur = await db.conn.execute("SELECT last_insert_rowid() AS order_id")
        row = await cur.fetchone()
        order_ids.append(row["order_id"])

    await db.conn.commit()
    carts[token] = []  # I'm assuming no one wants to keep the old cart after buying the stuff

    return {"msg": f"Checkout complete, orders placed", "order_ids": order_ids}
