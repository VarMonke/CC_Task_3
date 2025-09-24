from typing import (
    Dict,
    Union
)

import secrets
from fastapi import APIRouter, Depends, HTTPException, Form, Request

from database import APIDatabase, get_db, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


#I thought abbout using stuff like JWT and all, but then I realised that these are not expiring logins so that seemed useless.
sessions: Dict[str, Dict[str, Union[int, str]]]= {}


@router.post("/user/signup")
async def user_signup(
    username: str = Form(...),
    password: str = Form(...),
    db: APIDatabase = Depends(get_db)
):
    """
    This sign-in function makes sure the user DOES NOT exist before we add them to our database.

    It returns the user_id of the user.
    """
    existing = await db.get_user(username)

    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    await db.create_user(username, password)
    user = await db.get_user(username)

    return {"user_id": user["id"], "msg": "User created successfully"} #type: ignore tbh this is because we can't assure if the user exists but the user is just created so lol


@router.post("/user/login")
async def user_login(
    username: str = Form(...),
    password: str = Form(...),
    db: APIDatabase = Depends(get_db)
):
    """
    This verifies the user and returns an access token, since this API is stateful.
    The API uses `bcrypt` to generate random salts and encrypts the password.
    """
    user = await db.get_user(username)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_hex(16)
    sessions[token] = {"user_id": user["id"], "username": username, "role": "user"}
    return {"access_token": token, "token_type": "bearer"}


@router.post("/admin/login")
async def admin_login(
    username: str = Form(...),
    password: str = Form(...),
    db: APIDatabase = Depends(get_db)
):
    """
    This verifies the user and returns an access token, since this API is stateful.
    The API uses `bcrypt` to generate random salts and encrypts the password.
    """
    admin = await db.get_admin(username)
    if not admin or not verify_password(password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_hex(16)
    sessions[token] = {"user_id": admin["id"], "username": username, "role": "admin"}
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
async def logout(token: str = Form(...)):
    """
    Simple logout function. Removes the user's token from the volatile dict of user tokens.
    """
    if token in sessions:
        sessions.pop(token)
    return {"msg": "Logged out"}
