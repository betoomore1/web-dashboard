# backend/app/routers/admin_base_routes.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
import os

from ..utils import get_base, set_base  # <- ці ф-ції вже є в твоєму utils.py

router = APIRouter(prefix="/api/admin", tags=["admin"])


def admin_token_required(request: Request):
    """
    Пропускаємо, якщо заголовок містить коректний токен.
    Підтримуємо і 'x-token', і 'x-admin-token'.
    """
    header_token = (
        request.headers.get("x-token")
        or request.headers.get("x-admin-token")
        or request.headers.get("X-Token")
        or request.headers.get("X-Admin-Token")
    )

    admin = os.getenv("ADMIN_TOKEN") or ""
    if not header_token or header_token != admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token",
        )


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
