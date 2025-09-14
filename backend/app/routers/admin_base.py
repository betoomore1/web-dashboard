# backend/app/routers/admin_base.py
from fastapi import Depends, Header, HTTPException
import os

# Отримуємо токен з середовища
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

def admin_token_required(x_token: str = Header(...)):
    """
    Перевірка токена адміністратора.
    Викликається як Depends у всіх адмінських роутерах.
    """
    if not ADMIN_TOKEN:
        raise HTTPException(status_code=500, detail="ADMIN_TOKEN not configured on server")

    if x_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")

    return True
