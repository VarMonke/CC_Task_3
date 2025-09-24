from fastapi import APIRouter, Query, Depends, HTTPException, Path

from database import APIDatabase, get_db

router = APIRouter(prefix="/shop", tags=["shop"])


@router.get("/list")
async def list_items(
    db: APIDatabase = Depends(get_db),
    category: str | None = Query(None, description="Filter by category"),
    price: str | None = Query(None, description="Price range: min-max"),
    search: str | None = Query(None, description="Search in name or description"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort_by: str = Query("name", regex="^(name|price)$", description="Sort by 'name' or 'price'"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order")
):
    """
    List all items in the shop catalog with optional filters:
    - category: filter by item category
    - price: filter by range "min-max"
    - search: keyword search in name or description
    - pagination: limit and offset
    - sorting: sort_by ('name' or 'price') and sort_order ('asc' or 'desc')
    """
    query = "SELECT id, name, brand, description, category, price, quantity FROM items WHERE quantity > 0"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if price:
        try:
            min_price, max_price = map(float, price.split("-"))
            query += " AND price BETWEEN ? AND ?"
            params.extend([min_price, max_price])
        except Exception:
            raise HTTPException(status_code=400, detail="Price range format should be min-max")

    if search:
        search_term = f"%{search}%"
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([search_term, search_term])

    query += f" ORDER BY {sort_by} {sort_order.upper()}"

    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    try:
        cur = await db.conn.execute(query, tuple(params))
        rows = await cur.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch items: {str(e)}")



@router.get("/item/{item_id}")
async def get_item(item_id: int = Path(..., ge=1), db: APIDatabase = Depends(get_db)):
    """
    Get detailed information for a single item by its ID.
    """
    item = await db.get_item(item_id)
    if not item or item["quantity"] <= 0:
        raise HTTPException(status_code=404, detail="Item not found or out of stock")
    return {
        "id": item["id"],
        "name": item["name"],
        "brand": item["brand"],
        "description": item["description"],
        "category": item["category"],
        "price": item["price"],
        "quantity": item["quantity"],
        "date_created": item["date_created"],
        "date_restocked": item["date_restocked"]
    }


@router.get("/categories")
async def get_categories(db: APIDatabase = Depends(get_db)):
    """
    Get a list of all unique categories in the shop.
    """
    try:
        cur = await db.conn.execute("SELECT DISTINCT category FROM items WHERE quantity > 0")
        rows = await cur.fetchall()
        categories = [row["category"] for row in rows if row["category"]]
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch categories: {str(e)}")