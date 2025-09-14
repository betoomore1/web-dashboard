# backend/app/utils.py
from __future__ import annotations

from pathlib import Path
import configparser
from typing import Dict, Any, List

# Шлях до конфігу (backend/config.ini)
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.ini"


# ---------- Базові утиліти для INI ----------

def read_ini() -> configparser.ConfigParser:
    """
    Читаємо INI без інтерполяції (інакше відсотки в рядках ламатимуться).
    """
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(CONFIG_PATH, encoding="utf-8")
    return cfg


def write_ini(cfg: configparser.ConfigParser) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        cfg.write(f)


# ---------- Допоміжні: гарантуємо наявність секцій ----------

def ensure_base(cfg: configparser.ConfigParser) -> None:
    if "base" not in cfg:
        cfg["base"] = {
            "rounding": "ceil10",
            "price_high": "21101",
            "price_low": "18257",
        }


def _group_section(name: str) -> str:
    return f"group:{name}"


def ensure_group(cfg: configparser.ConfigParser, name: str) -> None:
    sec = _group_section(name)
    if sec not in cfg:
        cfg[sec] = {"mode": "single"}


# ---------- API «Базові ставки» (rounding, price_high/low) ----------

def get_base() -> Dict[str, Any]:
    """
    Повертає базовий блок конфігурації.
    """
    cfg = read_ini()
    ensure_base(cfg)
    base = cfg["base"]
    return {
        "rounding": base.get("rounding", "ceil10"),
        "price_high": int(base.get("price_high", "21101")),
        "price_low": int(base.get("price_low", "18257")),
    }


def set_base(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Оновлює базовий блок у конфігу. Очікує ключі: rounding(str), price_high(int), price_low(int).
    """
    cfg = read_ini()
    ensure_base(cfg)
    base = cfg["base"]

    if "rounding" in payload and payload["rounding"]:
        base["rounding"] = str(payload["rounding"])

    if "price_high" in payload and payload["price_high"] is not None:
        base["price_high"] = str(int(payload["price_high"]))

    if "price_low" in payload and payload["price_low"] is not None:
        base["price_low"] = str(int(payload["price_low"]))

     # ---- синхронізуємо "variables" для калькулятора (бек-сов сумісність) ----
    if "variables" not in cfg:
        cfg["variables"] = {}
    v = cfg["variables"]
    # переносимо rounding
    if "rounding" in cfg["base"]:
        v["rounding"] = cfg["base"]["rounding"]
    # переносимо ціни
    if "price_per_meter" not in v:
        v["price_per_meter"] = {}
    vppm = v["price_per_meter"]
    if "price_high" in cfg["base"]:
        vppm["high"] = cfg["base"]["price_high"]
    if "price_low" in cfg["base"]:
        vppm["low"] = cfg["base"]["price_low"]

    write_ini(cfg)
    return get_base()


# ---------- API «Групи категорій» ----------

def list_groups() -> List[Dict[str, Any]]:
    """
    Повертає список усіх груп (розпаршених із секцій group:*).
    """
    cfg = read_ini()
    groups: List[Dict[str, Any]] = []

    for sec in cfg.sections():
        if sec.startswith("group:"):
            name = sec.split(":", 1)[1]
            mode = cfg[sec].get("mode", "single")

            # зібрати всі item.N
            items = []
            for k, v in cfg[sec].items():
                if not k.startswith("item."):
                    continue
                # формат: "назва|op|value"
                parts = [p.strip() for p in v.split("|")]
                # захист від кривих рядків
                label = parts[0] if len(parts) > 0 else ""
                op = parts[1] if len(parts) > 1 else "mul"
                try:
                    value = float(parts[2]) if len(parts) > 2 else 0.0
                except ValueError:
                    value = 0.0
                items.append({"name": label, "op": op, "value": value})

            groups.append({"name": name, "mode": mode, "items": items})

    # стабільність порядку (не обов’язково, але приємно)
    groups.sort(key=lambda g: g["name"])
    return groups


def get_group(name: str) -> Dict[str, Any]:
    """
    Повертає одну групу за назвою (id==name).
    """
    cfg = read_ini()
    sec = _group_section(name)
    if sec not in cfg:
        raise KeyError(name)

    mode = cfg[sec].get("mode", "single")
    items = []
    for k, v in cfg[sec].items():
        if not k.startswith("item."):
            continue
        parts = [p.strip() for p in v.split("|")]
        label = parts[0] if len(parts) > 0 else ""
        op = parts[1] if len(parts) > 1 else "mul"
        try:
            value = float(parts[2]) if len(parts) > 2 else 0.0
        except ValueError:
            value = 0.0
        items.append({"name": label, "op": op, "value": value})

    items.sort(key=lambda it: it["name"])
    return {"name": name, "mode": mode, "items": items}


def save_group(name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Створює/оновлює групу (ім’я секції == group:{name}).
    data очікується у форматі: { name, mode, items:[{name, op, value}, ...] }
    """
    cfg = read_ini()
    sec = _group_section(name)
    ensure_group(cfg, name)

    mode = (data.get("mode") or "single").strip()
    cfg[sec]["mode"] = mode

    # Готуємо чисті item.* — спершу видалимо старі
    for k in list(cfg[sec].keys()):
        if k.startswith("item."):
            del cfg[sec][k]

    items = data.get("items") or []
    for i, it in enumerate(items, start=1):
        label = str(it.get("name", "")).strip()
        op = str(it.get("op", "mul")).strip()
        try:
            value = float(it.get("value", 0))
        except (TypeError, ValueError):
            value = 0.0
        cfg[sec][f"item.{i}"] = f"{label}|{op}|{value}"

    write_ini(cfg)
    # віддаємо вже уніфікований вигляд
    return get_group(name)


def delete_group(name: str) -> None:
    """
    Видаляє секцію групи.
    """
    cfg = read_ini()
    sec = _group_section(name)
    if sec in cfg:
        cfg.remove_section(sec)
        write_ini(cfg)


# ---------- Сумісність для калькулятора (/api/calc/config) ----------

def as_json(cfg: configparser.ConfigParser) -> Dict[str, Any]:
    """
    Повертає структуру, з якою вже працює фронт калькулятора.
    Ми залишаємо старі поля, щоб нічого не падало:
      variables, price_per_meter {high, low}, positions (якщо є) або збираємо
      з групи colors як % (op=="mul" => беремо value; інакше 0).
    """
    # variables (старий блок)
    variables = {
        "min_length": int(cfg.get("variables", "min_length", fallback="500")),
        "max_length": int(cfg.get("variables", "max_length", fallback="1000")),
        "min_width": int(cfg.get("variables", "min_width", fallback="500")),
        "min_height": int(cfg.get("variables", "min_height", fallback="150")),
        "extra_price": float(cfg.get("variables", "extra_price", fallback="22")),
        "rounding": cfg.get("base", "rounding", fallback="ceil10"),
    }

    # базові ціни
    price_per_meter = {
        "high": float(cfg.get("base", "price_high", fallback="21101")),
        "low": float(cfg.get("base", "price_low", fallback="18257")),
    }

    # positions: якщо є стара секція — беремо її; інакше пробуємо зібрати з group:colors
    positions: Dict[str, float] = {}
    if "positions" in cfg:
        for k, v in cfg["positions"].items():
            try:
                positions[k] = float(v)
            except ValueError:
                continue
    else:
        colors_sec = _group_section("colors")
        if colors_sec in cfg:
            for k, v in cfg[colors_sec].items():
                if not k.startswith("item."):
                    continue
                label, op, value_str = (p.strip() for p in v.split("|")) if "|" in v else (v, "mul", "0")
                try:
                    value = float(value_str)
                except ValueError:
                    value = 0.0
                # лише mul інтерпретуємо як % (щоб не ламати поточний калькулятор)
                positions[label] = value if op == "mul" else 0.0

    return {
        "variables": variables,
        "price_per_meter": price_per_meter,
        "positions": positions,
    }
