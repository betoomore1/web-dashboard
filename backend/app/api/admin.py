from fastapi import APIRouter, Header, HTTPException
import os, configparser, csv
from pathlib import Path
from typing import Optional, Dict, Any
from ..services.config_loader import load_settings, save_base
from functools import lru_cache
from pydantic import BaseModel

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")  # встановиш змінну середовища

router = APIRouter(prefix="/api/admin", tags=["admin"])

def check_token(x_admin_token: Optional[str]):
    # Dev-режим: якщо токен не заданий у середовищі — не блокуємо.
    if not ADMIN_TOKEN:
        return
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(401, "Invalid admin token")

@router.post("/reload")
def reload_config(x_admin_token: Optional[str] = Header(None)):
    check_token(x_admin_token)
    # скидаємо кеш лоадера
    load_settings.cache_clear()  # type: ignore[attr-defined]
    return {"ok": True}

@router.put("/variables")
def update_variables(
    payload: Dict[str, Any],
    x_admin_token: Optional[str] = Header(None)
):
    """
    Приклад тіла:
    { "min_length": 500, "max_length": 5000, "min_width": 500,
      "min_height": 150, "extra_price": 22, "rounding": "ceil10" }
    """
    check_token(x_admin_token)
    ini_path = DATA_DIR / "config.ini"
    cfg = configparser.ConfigParser()
    cfg.read(ini_path, encoding="utf-8")
    if "variables" not in cfg:
        cfg["variables"] = {}

    # дозволені ключі
    allowed = {"min_length","max_length","min_width","min_height","extra_price","rounding"}
    for k,v in payload.items():
        if k not in allowed:
            raise HTTPException(400, f"Unknown key: {k}")
        if k == "rounding":
            vv = str(v).strip().lower()
            if vv not in {"nearest10","ceil10"}:
                raise HTTPException(400, "rounding must be nearest10|ceil10")
            cfg["variables"][k] = vv
        else:
            # цілі значення для *_length/width/height, float для extra_price
            try:
                if k == "extra_price":
                    float(v)
                else:
                    int(v)
            except Exception:
                raise HTTPException(400, f"Invalid value for {k}")
            cfg["variables"][k] = str(v)

    # атомічний запис
    tmp = ini_path.with_suffix(".ini.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        cfg.write(f)
    tmp.replace(ini_path)

    load_settings.cache_clear()  # type: ignore[attr-defined]
    s = load_settings()
    return {
        "ok": True,
        "variables": {
            "min_length": s.min_length,
            "max_length": s.max_length,
            "min_width":  s.min_width,
            "min_height": s.min_height,
            "extra_price": s.extra_price,
            "rounding": s.rounding_mode,
        }
    }

@router.put("/prices")
def update_prices(
    payload: Dict[str, Any],
    x_admin_token: Optional[str] = Header(None)
):
    """
    Тіло: { "high": 20097, "low": 17388 }
    """
    check_token(x_admin_token)
    try:
        high = float(payload["high"])
        low  = float(payload["low"])
    except Exception:
        raise HTTPException(400, "Body must contain numeric 'high' and 'low'")

    csv_path = DATA_DIR / "prices.csv"
    tmp = csv_path.with_suffix(".csv.tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([high])
        w.writerow([low])
    tmp.replace(csv_path)

    load_settings.cache_clear()  # type: ignore[attr-defined]
    s = load_settings()
    return {"ok": True, "price_per_meter": {"high": s.price_per_meter_high, "low": s.price_per_meter_low}}

class Position(BaseModel):
    name: str
    percent: float

# тимчасове сховище в пам’яті
DB: dict[str, float] = {}

@router.get("/positions")
def list_positions():
    # повертаємо як словник {name: percent}
    return DB

@router.post("/positions")
def upsert_position(p: Position):
    DB[p.name] = p.percent
    return {"ok": True}

@router.delete("/positions/{name}")
def delete_position(name: str):
    DB.pop(name, None)
    return {"ok": True}

class BaseSave(BaseModel):
    rounding: str
    price_high: int | float | str
    price_low:  int | float | str

@router.post("/base")
def save_base_route(body: BaseSave):
    try:
        ph = int(float(str(body.price_high).replace(',', '.')))
        pl = int(float(str(body.price_low).replace(',', '.')))
        s = save_base(body.rounding, ph, pl)
        return {"rounding": s.rounding, "price_high": s.price_high, "price_low": s.price_low}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))