# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# ---------- 1) Створюємо FastAPI ----------
app = FastAPI(title="BETOOMORE Dashboard API")

# ---------- 2) CORS (можна лишити дефолт у DEV) ----------
ALLOW_ORIGIN_REGEX = os.getenv("ALLOW_ORIGIN_REGEX", r"https?://.*")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=ALLOW_ORIGIN_REGEX,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

FRONT_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")  # на проді постав точний домен фронта
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONT_ORIGIN] if FRONT_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------- 3) Health ----------
@app.get("/healthz")
def healthz():
    return {"ok": True}

# ---------- 4) Імпорти роутерів ПІСЛЯ створення app ----------
# УВАГА: тільки відносні імпорти з поточного пакета 'app'
from .routers.admin_positions import router as admin_positions_router
from .routers.admin_groups import router as admin_groups_router
from .routers.admin_base_routes import router as admin_base_router
from .api.calc import router as calc_router
from .api.admin import router as admin_router

# ---------- 5) Підключаємо роутери (порядок важливий, щоб не ловити циклічні імпорти) ----------
app.include_router(admin_positions_router)
app.include_router(calc_router)
app.include_router(admin_router)          # /api/admin (логін/токен)
app.include_router(admin_base_router)     # /api/admin/base (базові ставки)
app.include_router(admin_groups_router)   # /api/admin/groups (групи/категорії)
