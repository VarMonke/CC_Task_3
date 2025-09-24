from typing import (
    List,
    Any,
    Dict,
)

import os

import datetime
import asqlite
import bcrypt

from logger import Logger


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


import os
import datetime
import asqlite
from typing import List, Dict, Any
from pathlib import Path
from logger import Logger

DB_PATH = "api_data.db"


class APIDatabase:
    def __init__(self, logger: Logger):
        self.db_name = os.getenv("DATABASE_NAME", DB_PATH)
        self.logger = logger
        self.conn: asqlite.Connection

    async def __aenter__(self):
        self.conn = await asqlite.connect(self.db_name)
        self.logger.info("Database connection opened")
        return self

    async def __aexit__(self, *args, **kwargs):
        if self.conn:
            await self.conn.close()
        self.logger.info("Database connection closed")


    async def create_user(self, username: str, password_hash: str):
        cur = await self.conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        await self.conn.commit()


    async def get_user(self, username: str) -> Dict[str, Any] | None:
        cur = await self.conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,)
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def get_admin(self, username: str) -> Dict[str, Any] | None:
        cur = await self.conn.execute(
            "SELECT id, username, password_hash FROM admins WHERE username = ?",
            (username,)
        )
        row = await cur.fetchone()
        return dict(row) if row else None


    async def list_items(self) -> List[Dict[str, Any]]:
        cur = await self.conn.execute(
            "SELECT id, name, brand, date_created, date_restocked FROM items"
        )
        rows = await cur.fetchall()
        return [dict(row) for row in rows]

    async def create_item(self, name, brand, description, category, quantity, price):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        await self.conn.execute(
            "INSERT INTO items (name, brand, description, category, quantity, price, date_created, date_restocked) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, brand, description, category, quantity, price, now, now)
        )
        await self.conn.commit()

    async def get_item(self, item_id: int) -> Dict[str, Any] | None:
        cur = await self.conn.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

    async def update_item(self, item_id: int, **kwargs):
        if not kwargs:
            return
        fields = []
        values = []
        for k, v in kwargs.items():
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(item_id)
        query = f"UPDATE items SET {', '.join(fields)} WHERE id = ?"
        await self.conn.execute(query, tuple(values))
        await self.conn.commit()

    async def restock_item(self, item_id: int, quantity: int):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        await self.conn.execute(
            "UPDATE items SET quantity = quantity + ?, date_restocked = ? WHERE id = ?",
            (quantity, now, item_id)
        )
        await self.conn.commit()


    async def get_orders(self) -> List[Dict[str, Any]]:
        cur = await self.conn.execute("""
            SELECT orders.id AS order_id, orders.item_id, items.name AS item_name,
                   users.id AS user_id, users.username,
                   orders.quantity, orders.total_price, orders.date_ordered
            FROM orders
            JOIN users ON orders.user_id = users.id
            JOIN items ON orders.item_id = items.id
        """)
        rows = await cur.fetchall()
        return [dict(row) for row in rows]

    async def get_revenue(self) -> float:
        cur = await self.conn.execute("SELECT SUM(total_price) AS revenue FROM orders")
        row = await cur.fetchone()
        return row["revenue"] or 0



async def init_db():
    logger = Logger("api.log")
    async with APIDatabase(logger) as db:
        # Users table
        await db.conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """)
        # Admins table
        await db.conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """)
        # Items table
        await db.conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT,
            description TEXT,
            category TEXT,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            date_created TEXT,
            date_restocked TEXT
        )
        """)
        # Orders table
        await db.conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            date_ordered TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
        """)
        await db.conn.commit()

        # This is for temporary testing since an admin doesn't exist when there is no DB
        cur = await db.conn.execute("SELECT COUNT(*) as count FROM admins")
        row = await cur.fetchone()
        if row["count"] == 0:
            pw_hash = hash_password("adminpass")
            await db.conn.execute(
                "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
                ("shopkeeper", pw_hash)
            )
            await db.conn.commit()
            logger.info("Preloaded default admin: shopkeeper/adminpass")

    logger.info("Database initialized successfully.")


logger = Logger("api.log", True)


# This is a pretty cool feature of FastAPI, you can have a Depends() thing and it executes code on it's own
# to prevent the passing of connections and trying to maintain database connection throughout multiple files.
async def get_db():
    async with APIDatabase(logger=logger) as db:
        yield db


