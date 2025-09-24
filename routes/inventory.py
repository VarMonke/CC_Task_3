import csv
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from routes.auth import sessions
from database import APIDatabase, get_db

router = APIRouter(prefix="/inventory", tags=["inventory"])


def require_admin(token: str = Form(...)):
    if token not in sessions or sessions[token]["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return sessions[token]


@router.get("/list")
async def list_items(admin=Depends(require_admin), db: APIDatabase = Depends(get_db)):
    try:
        return await db.list_items()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list items: {str(e)}")


@router.post("/new")
async def create_item(
    name: str = Form(...),
    brand: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    quantity: int = Form(...),
    price: float = Form(...),
    admin=Depends(require_admin),
    db: APIDatabase = Depends(get_db)
):
    """
    Adds new item to the inventory.
    """
    if quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative")
    if price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative")

    try:
        await db.create_item(name, brand, description, category, quantity, price)
        return {"msg": "Item created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create item: {str(e)}")


@router.post("/bulk_new")
async def bulk_create_items(file: UploadFile, admin=Depends(require_admin), db: APIDatabase = Depends(get_db)):
    """
    This bulk adds new items from a CSV file, with the format `name, brand, description, category, quantity, price` in the CSV file
    """
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Add the CSV file with the new item data.")
    

    if not file.filename.endswith(".csv"): 
        raise HTTPException(status_code=400, detail="File must be CSV")

    content = await file.read()
    decoded = content.decode("utf-8").splitlines()
    reader = csv.DictReader(decoded)

    created_count = 0
    for row in reader:
        try:
            name = row["name"]
            brand = row.get("brand", "")
            description = row.get("description", "")
            category = row.get("category", "")
            quantity = int(row["quantity"])
            price = float(row["price"])

            if quantity < 0 or price < 0:
                continue  # skip invalid rows

            await db.create_item(name, brand, description, category, quantity, price)
            created_count += 1
        except Exception:
            continue  # skip malformed rows

    return {"msg": f"Bulk create complete. {created_count} items added."}


@router.post("/update")
async def update_item(
    item_id: int = Form(...),
    name: str | None = Form(None),
    brand: str | None = Form(None),
    description: str | None = Form(None),
    category: str | None = Form(None),
    quantity: int | None = Form(None),
    price: float | None = Form(None),
    admin=Depends(require_admin),
    db: APIDatabase = Depends(get_db)
):
    """Updates an item in the inventory."""
    item = await db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    kwargs = {k: v for k, v in [
        ("name", name), ("brand", brand), ("description", description),
        ("category", category), ("quantity", quantity), ("price", price)
    ] if v is not None}

    if "quantity" in kwargs and kwargs["quantity"] < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative")
    if "price" in kwargs and kwargs["price"] < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative")
    if not kwargs:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        await db.update_item(item_id, **kwargs)
        return {"msg": "Item updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update item: {str(e)}")


@router.post("/restock")
async def restock_item(
    item_id: int = Form(...),
    quantity: int = Form(...),
    admin=Depends(require_admin),
    db: APIDatabase = Depends(get_db)
):
    "Restocks an item in the inventory."
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    item = await db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    try:
        await db.restock_item(item_id, quantity)
        return {"msg": f"Restocked {quantity} units of '{item['name']}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restock item: {str(e)}")


@router.post("/bulk_restock")
async def bulk_restock_items(file: UploadFile, admin=Depends(require_admin), db: APIDatabase = Depends(get_db)):
    """
    Bulk restocks the items in the inventory from a CSV file, with the format `item_id,quantity` in the CSV file.
    """
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Add the CSV file with the new item data.")


    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be CSV")

    content = await file.read()
    decoded = content.decode("utf-8").splitlines()
    reader = csv.DictReader(decoded)

    restocked_count = 0
    skipped = 0
    for row in reader:
        try:
            item_id = int(row["item_id"])
            quantity = int(row["quantity"])

            if quantity <= 0:
                skipped += 1
                continue

            item = await db.get_item(item_id)
            if not item:
                skipped += 1
                continue

            await db.restock_item(item_id, quantity)
            restocked_count += 1
        except Exception:
            skipped += 1

    return {"msg": f"Bulk restock complete. {restocked_count} items restocked, {skipped} skipped."}


@router.get("/orders")
async def view_orders(admin=Depends(require_admin), db: APIDatabase = Depends(get_db)):
    """Returns all the orders that have been placed."""
    try:
        return await db.get_orders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")


@router.get("/revenue")
async def total_revenue(admin=Depends(require_admin), db: APIDatabase = Depends(get_db)):
    """Returns the total revenue generated."""
    try:
        revenue = await db.get_revenue()
        return {"total_revenue": revenue}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate revenue: {str(e)}")
    

