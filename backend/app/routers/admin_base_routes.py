# backend/app/routers/admin_base_routes.py
from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
import os
from typing import Optional
from ..utils import get_base, set_base  # <- ці ф-ції вже є в твоєму utils.py

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

def admin_token_required(x_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    if not ADMIN_TOKEN:   # dev: без токена
        return True
    if x_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")
    return True


@router.get("/base", dependencies=[Depends(admin_token_required)])
def read_base():
    """Отримати базові ставки (price_high, price_low, rounding)."""
    return get_base()


@router.put("/base", dependencies=[Depends(admin_token_required)])
def update_base(payload: dict):
    """
    Оновити базові ставки.
    Очікуємо будь-яку підмножину ключів: rounding(str), price_high(int), price_low(int).
    """
    return set_base(payload)
