from fastapi import FastAPI
from contextlib import asynccontextmanager

from database import init_db
from routes import auth, inventory, shop, orders, cart  


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)


app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(shop.router)
app.include_router(orders.router)
app.include_router(cart.router)