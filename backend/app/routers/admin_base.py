# backend/app/routers/admin_base.py
from fastapi import Depends, Header, HTTPException
import os
from typing import Optional

# Отримуємо токен з середовища
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

def admin_token_required(x_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    if not ADMIN_TOKEN:   # dev: без токена
        return True
    if x_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")
    return True