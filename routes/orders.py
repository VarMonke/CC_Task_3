
import datetime
from fastapi import APIRouter, Depends, HTTPException, Form

from database import APIDatabase, get_db
from routes.auth import sessions


router = APIRouter(prefix="/orders", tags=["orders"])

@router.get("/past")
async def past_orders(token: str = Form(...), db: APIDatabase = Depends(get_db)):
    """Gets all the past orders of the logged in user."""
    session = sessions.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = session["user_id"]

    all_orders = await db.get_orders()
    user_orders = [o for o in all_orders if o["user_id"] == user_id]
    return {"orders": user_orders}

@router.post("/new")
async def make_order(
    token: str = Form(...),
    item_id: int = Form(...),
    quantity: int = Form(...),
    db: APIDatabase = Depends(get_db)
):
    """Generates a new order with the item being purchased."""
    session = sessions.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = session["user_id"]

    item = await db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item["quantity"] < quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

    total_price = item["price"] * quantity
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    await db.conn.execute(
        "INSERT INTO orders (user_id, item_id, quantity, total_price, date_ordered) VALUES (?, ?, ?, ?, ?)",
        (user_id, item_id, quantity, total_price, now)
    )
    await db.conn.execute(
        "UPDATE items SET quantity = quantity - ? WHERE id = ?",
        (quantity, item_id)
    )
    await db.conn.commit()

    cur = await db.conn.execute("SELECT last_insert_rowid() AS order_id")
    row = await cur.fetchone()
    return {"order_id": row["order_id"]}
