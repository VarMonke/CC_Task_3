# 🛍️ Clothes API: An API to serve an E-Commerce platform

A simple online shop API for managing a clothing store inventory, built with **FastAPI** and **SQLite (asqlite)**.  

Supports:
- Adding new items (brand, name, stock)
- Listing all items
- Updating items
- Restocking items
- Deleting items
- Dealing with temporry cart states of users and checkouts
---

## 🚀 Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/VarMonke/CC_Task_3.git
cd CC_Task_3
pip install -r requirements.txt
```

After doing this, there is **no data** in our database per se. There is a `temporary.py` that allows you to populate the database with temporary data for preliminary testing.

### 2. Run the API
```bash
uvicorn main:app --reload
```

### 3. The server will start at: **http://127.0.0.1:8000**


# 📄 Postman Collection

This API is also documented with Postman. The docs are available **[here](https://f20250622-2480640.postman.co/workspace/VARSHITH-S-REDDY's-Workspace~4caffb80-d20e-4a21-8387-e089c078ba2e/collection/48674337-e06533ff-4554-458c-8b28-972eb8220b9a?action=share&creator=48674337ble)**.
