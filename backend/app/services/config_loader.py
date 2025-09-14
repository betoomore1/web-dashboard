# -*- coding: utf-8 -*-
"""
Надійний лоадер/сейвер конфігів для калькулятора та адмінки.

Зберігаємо все у backend/config.ini у такій структурі:
- [variables]         — технічні обмеження, extra_price
- [base]              — базові ставки (rounding, price_high, price_low)
- [group:<id>]        — групи категорій
    mode=<single|multi>
    title=<людська назва>
    item.1 = Назва|<mul|add|sub|div>|<число>

Приклади item.*:
    item.1 = базовий сірий колір|mul|0
    item.2 = базовий колір в масі +5%|mul|5    ← “%” допускаємо у файлі, але при читанні прибираємо
"""

from __future__ import annotations

from configparser import RawConfigParser
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple

# Шлях до backend/config.ini
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.ini"

# ---------------------------- Моделі ---------------------------- #

@dataclass
class VariableSettings:
    min_length: int = 500
    max_length: int = 1000
    min_width: int = 500
    min_height: int = 150
    extra_price: float = 22.0

@dataclass
class BaseSettings:
    rounding: str = "ceil10"       # napр.: ceil10 / ceil100 / round / floor …
    price_high: int = 21101
    price_low: int = 18257

@dataclass
class GroupItem:
    name: str
    op: str     # mul | add | sub | div
    value: float

@dataclass
class Group:
    id: str
    name: str
    mode: str              # single | multi
    items: List[GroupItem]

# Об'єкт, який очікує calc.py у get_config()
@dataclass
class SettingsDTO:
    min_length: int
    max_length: int
    min_width: int
    min_height: int
    extra_price: float
    rounding_mode: str
    price_per_meter_high: int
    price_per_meter_low: int
    positions: dict[str, float]  # список груп для фронта (dict)

# -------------------------- Utils --------------------------- #

def _new_cfg() -> RawConfigParser:
    # interpolation=None — щоб '%' не ламався
    return RawConfigParser(interpolation=None)

def _read_ini() -> RawConfigParser:
    cfg = RawConfigParser(interpolation=None)  # ВАЖЛИВО: щоб '%' у item.* не ламав парсер
    if CONFIG_PATH.exists():
        try:
            CONFIG_PATH.chmod(0o664)
        except Exception:
            pass
        cfg.read(CONFIG_PATH, encoding="utf-8")
    return cfg

def _write_ini(cfg: RawConfigParser) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        cfg.write(f)

def _ensure(cfg: RawConfigParser, sect: str) -> None:
    if not cfg.has_section(sect):
        cfg.add_section(sect)

def _get_int(cfg: RawConfigParser, sect: str, key: str, default: int) -> int:
    try:
        return cfg.getint(sect, key)
    except Exception:
        return default

def _get_float(cfg: RawConfigParser, sect: str, key: str, default: float) -> float:
    try:
        return cfg.getfloat(sect, key)
    except Exception:
        return default

def _get_str(cfg: RawConfigParser, sect: str, key: str, default: str) -> str:
    try:
        return cfg.get(sect, key)
    except Exception:
        return default

# --------------------------- Readers ---------------------------- #

def _read_variables(cfg: RawConfigParser) -> VariableSettings:
    s = "variables"
    _ensure(cfg, s)
    return VariableSettings(
        min_length=_get_int(cfg, s, "min_length", 500),
        max_length=_get_int(cfg, s, "max_length", 1000),
        min_width=_get_int(cfg, s, "min_width", 500),
        min_height=_get_int(cfg, s, "min_height", 150),
        extra_price=_get_float(cfg, s, "extra_price", 22.0),
    )

def _read_base(cfg: RawConfigParser) -> BaseSettings:
    s = "base"
    _ensure(cfg, s)
    return BaseSettings(
        rounding=_get_str(cfg, s, "rounding", "ceil10"),
        price_high=_get_int(cfg, s, "price_high", 21101),
        price_low=_get_int(cfg, s, "price_low", 18257),
    )

def _parse_item(raw: str) -> GroupItem:
    """
    Очікуємо формат: "Назва|op|value".
    При читанні прибираємо пробіли, плюсики, відсотки; op валідуємо.
    Якщо формат зламаний — підставляємо mul|0.
    """
    raw = (raw or "").strip()
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 3:
        return GroupItem(name=raw or "item", op="mul", value=0.0)

    name, op, value = parts[0], parts[1].lower(), parts[2]
    # прибираємо “+” і “%”, коми → крапки
    value = value.replace("%", "").replace("+", "").replace(",", ".")
    try:
        val = float(value)
    except Exception:
        val = 0.0

    if op not in {"mul", "add", "sub", "div"}:
        op = "mul"

    return GroupItem(name=name, op=op, value=val)

def _read_group_from_section(cfg: RawConfigParser, sect: str) -> Group:
    # sect == "group:colors"
    gid = sect.split(":", 1)[1]
    mode = _get_str(cfg, sect, "mode", "single")
    title = _get_str(cfg, sect, "title", gid.capitalize())

    # Збираємо item.N у порядку N
    items: List[Tuple[int, GroupItem]] = []
    for k, v in cfg.items(sect):
        if k.startswith("item."):
            try:
                idx = int(k.split(".", 1)[1])
            except Exception:
                idx = 9999
            items.append((idx, _parse_item(v)))
    items.sort(key=lambda t: t[0])
    return Group(id=gid, name=title, mode=mode, items=[it for _, it in items])

def _read_groups(cfg: RawConfigParser) -> List[Group]:
    groups: List[Group] = []
    for sect in cfg.sections():
        if sect.startswith("group:"):
            groups.append(_read_group_from_section(cfg, sect))
    return groups

# --------------------------- Writers ---------------------------- #

def save_base(rounding: str | None, price_high: int | None, price_low: int | None) -> BaseSettings:
    """
    Оновлює секцію [base]. None — не змінюємо відповідне поле.
    """
    cfg = _read_ini()
    _ensure(cfg, "base")

    cur = _read_base(cfg)
    if isinstance(rounding, str) and rounding.strip():
        cfg.set("base", "rounding", rounding.strip())
    else:
        cfg.set("base", "rounding", cur.rounding)

    if price_high is not None:
        cfg.set("base", "price_high", str(int(price_high)))
    else:
        cfg.set("base", "price_high", str(cur.price_high))

    if price_low is not None:
        cfg.set("base", "price_low", str(int(price_low)))
    else:
        cfg.set("base", "price_low", str(cur.price_low))

    _write_ini(cfg)
    return _read_base(cfg)

def list_groups() -> List[Dict]:
    cfg = _read_ini()
    return [group_to_dict(g) for g in _read_groups(cfg)]

def get_group(gid: str) -> Dict | None:
    cfg = _read_ini()
    sect = f"group:{gid}"
    if not cfg.has_section(sect):
        return None
    return group_to_dict(_read_group_from_section(cfg, sect))

def save_group(payload: Dict) -> Dict:
    """
    payload:
      { "id": "colors", "name": "Колір", "mode": "single",
        "items": [ { "name": "...", "op": "mul", "value": 5 }, ... ] }
    """
    gid = (payload.get("id") or "").strip()
    if not gid:
        raise ValueError("group.id is required")

    cfg = _read_ini()
    sect = f"group:{gid}"
    _ensure(cfg, sect)

    name = (payload.get("name") or gid.capitalize()).strip()
    mode = (payload.get("mode") or "single").strip().lower()
    if mode not in {"single", "multi"}:
        mode = "single"

    cfg.set(sect, "title", name)
    cfg.set(sect, "mode", mode)

    # Спершу чистимо старі item.*
    for k in list(cfg[sect].keys()):
        if k.startswith("item."):
            cfg.remove_option(sect, k)

    items = payload.get("items") or []
    for i, it in enumerate(items, start=1):
        nm = str(it.get("name", "")).strip() or f"item {i}"
        op = str(it.get("op", "mul")).strip().lower()
        if op not in {"mul", "add", "sub", "div"}:
            op = "mul"
        try:
            val = float(str(it.get("value", 0)).replace("%", "").replace("+", ""))
        except Exception:
            val = 0.0
        cfg.set(sect, f"item.{i}", f"{nm}|{op}|{val}")

    _write_ini(cfg)
    return group_to_dict(_read_group_from_section(cfg, sect))

def delete_group(gid: str) -> bool:
    cfg = _read_ini()
    sect = f"group:{gid}"
    if not cfg.has_section(sect):
        return False
    cfg.remove_section(sect)
    _write_ini(cfg)
    return True

# ---------------------- Допоміжні конвертори ------------------- #

def group_to_dict(g: Group) -> Dict:
    return {
        "id": g.id,
        "name": g.name,
        "mode": g.mode,
        "items": [asdict(it) for it in g.items],
    }

# --------------------- Defaults / Міграції --------------------- #

def _ensure_defaults(cfg: RawConfigParser) -> None:
    """Якщо чогось немає — створюємо адекватні значення за умовчанням."""
    _ensure(cfg, "variables")
    _ensure(cfg, "base")

    if not cfg.has_option("variables", "min_length"):
        cfg.set("variables", "min_length", "500")
    if not cfg.has_option("variables", "max_length"):
        cfg.set("variables", "max_length", "1000")
    if not cfg.has_option("variables", "min_width"):
        cfg.set("variables", "min_width", "500")
    if not cfg.has_option("variables", "min_height"):
        cfg.set("variables", "min_height", "150")
    if not cfg.has_option("variables", "extra_price"):
        cfg.set("variables", "extra_price", "22")

    if not cfg.has_option("base", "rounding"):
        cfg.set("base", "rounding", "ceil10")
    if not cfg.has_option("base", "price_high"):
        cfg.set("base", "price_high", "21101")
    if not cfg.has_option("base", "price_low"):
        cfg.set("base", "price_low", "18257")

    # дефолтна група “Колір”, якщо її не існує
    gsect = "group:colors"
    if not cfg.has_section(gsect):
        cfg.add_section(gsect)
        cfg.set(gsect, "title", "Колір")
        cfg.set(gsect, "mode", "single")
        cfg.set(gsect, "item.1", "базовий сірий колір|mul|0")
        cfg.set(gsect, "item.2", "базовий колір в масі +5%|mul|5")
        cfg.set(gsect, "item.3", "чорний колір +20%|mul|20")
        cfg.set(gsect, "item.4", "індивідуальний поверхнево +20%|mul|20")
        cfg.set(gsect, "item.5", "індивідуальний в масі +25%|mul|25")

def _migrate_percent_items(cfg: RawConfigParser) -> None:
    """Прибираємо ‘%’ і ‘+’ у всіх item.N, якщо вони там є."""
    changed = False
    for sect in cfg.sections():
        if not sect.startswith("group:"):
            continue
        for k, v in list(cfg.items(sect)):
            if not k.startswith("item."):
                continue
            raw = (v or "")
            if "%" in raw or "+" in raw or "," in raw:
                it = _parse_item(raw)  # перепарсимо і запишемо числом
                cfg.set(sect, k, f"{it.name}|{it.op}|{it.value}")
                changed = True
    if changed:
        _write_ini(cfg)

# ----------------------- Публічне API --------------------------- #

def load_settings() -> SettingsDTO:
    """
    Повертає об'єкт, який безпосередньо використовує backend/app/api/calc.py:
      s.min_length, s.rounding_mode, s.price_per_meter_high/low, s.positions
    """
    cfg = _read_ini()
    _ensure_defaults(cfg)
    _migrate_percent_items(cfg)

    vars_ = _read_variables(cfg)
    base_ = _read_base(cfg)
    groups_ = _read_groups(cfg)

    # serializable групи для фронту (dict)
    positions_map: dict[str, float] = {}
    for g in groups_:
        if g.id == "colors":
            for it in g.items:
                positions_map[it.name] = float(it.value)
    # і повертати positions=positions_map

    return SettingsDTO(
        min_length=vars_.min_length,
        max_length=vars_.max_length,
        min_width=vars_.min_width,
        min_height=vars_.min_height,
        extra_price=vars_.extra_price,
        rounding_mode=base_.rounding,
        price_per_meter_high=base_.price_high,
        price_per_meter_low=base_.price_low,
        positions=positions_map,
    )
