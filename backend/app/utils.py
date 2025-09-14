# backend/app/utils.py
from __future__ import annotations
from pathlib import Path
import configparser
from configparser import RawConfigParser
from typing import Dict, Any, List
from pathlib import Path

# Шлях до конфігу (backend/config.ini)
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.ini"


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


def _read_cfg() -> RawConfigParser:
    cfg = RawConfigParser(interpolation=None)
    if CONFIG_PATH.exists():
        cfg.read(CONFIG_PATH, encoding="utf-8")
    return cfg

def _write_cfg(cfg: RawConfigParser) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        cfg.write(f)

def set_base(payload: dict) -> dict:
    """
    Очікуємо payload на кшталт:
      { "rounding": "ceil10", "price_per_meter": {"high": 21101, "low": 18257} }
    або:
      { "rounding": "ceil10", "price_high": 21101, "price_low": 18257 }
    Пишемо все у [base] ТІЛЬКИ як рядки.
    """
    cfg = _read_cfg()
    if not cfg.has_section("base"):
        cfg.add_section("base")

    rounding = str(payload.get("rounding") or payload.get("rounding_mode") or "ceil10")

    # приймаємо обидва варіанти ключів
    ppm = payload.get("price_per_meter") or {}
    high = payload.get("price_high", ppm.get("high", 21101))
    low  = payload.get("price_low",  ppm.get("low",  18257))

    # конвертації у числа і ДАЛІ У РЯДКИ
    try:
        high = str(int(float(high)))
    except Exception:
        high = "21101"
    try:
        low = str(int(float(low)))
    except Exception:
        low = "18257"

    cfg.set("base", "rounding", rounding)
    cfg.set("base", "price_high", high)
    cfg.set("base", "price_low", low)

    _write_cfg(cfg)

    # вертаємо те, що очікує фронт
    return {
        "rounding": rounding,
        "price_per_meter": {"high": int(high), "low": int(low)},
    }


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
