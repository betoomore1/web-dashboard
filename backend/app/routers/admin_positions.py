# app/routers/admin_positions.py
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field, validator
from configparser import ConfigParser
from pathlib import Path
from ..utils import read_ini, write_ini

CONFIG_PATH = Path("config.ini")

def verify_admin(x_admin_token: str = Header(..., alias="X-Admin-Token")):
    # TODO: підстав свій реальний спосіб перевірки (env/конфіг тощо)
    # простий варіант: брати токен з ENV ADMIN_TOKEN
    import os
    expected = os.getenv("ADMIN_TOKEN", "")
    if not expected or x_admin_token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

class PositionItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    percent: float

    @validator("percent")
    def clamp_percent(cls, v):
        if v < -100 or v > 1000:
            raise ValueError("percent out of range")
        return v

router = APIRouter(prefix="/api/admin/positions", tags=["admin-positions"])

def _load_positions() -> dict[str, float]:
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH, encoding="utf-8")
    if not cfg.has_section("positions"):
        return {}
    return {k: cfg.getfloat("positions", k) for k in cfg["positions"]}

def _save_positions(data: dict[str, float]):
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH, encoding="utf-8")
    if not cfg.has_section("positions"):
        cfg.add_section("positions")
    # атомарний перезапис секції
    for k in list(cfg["positions"].keys()):
        cfg.remove_option("positions", k)
    for k, v in data.items():
        cfg.set("positions", k, str(v))
    tmp = CONFIG_PATH.with_suffix(".ini.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        cfg.write(f)
    tmp.replace(CONFIG_PATH)

@router.get("", dependencies=[Depends(verify_admin)])
def list_positions():
    return _load_positions()

@router.put("", dependencies=[Depends(verify_admin)])
def replace_positions(payload: dict[str, float]):
    # повна заміна словника
    # валідація
    data = {}
    for k, v in payload.items():
        item = PositionItem(name=k, percent=v)
        data[item.name] = item.percent
    _save_positions(data)
    return {"ok": True, "count": len(data)}

@router.post("", dependencies=[Depends(verify_admin)])
def upsert_position(item: PositionItem):
    data = _load_positions()
    data[item.name] = item.percent
    _save_positions(data)
    return {"ok": True}

@router.delete("/{name}", dependencies=[Depends(verify_admin)])
def delete_position(name: str):
    data = _load_positions()
    if name not in data:
        raise HTTPException(404, "not found")
    del data[name]
    _save_positions(data)
    return {"ok": True}
