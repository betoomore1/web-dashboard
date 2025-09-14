from math import ceil
from decimal import Decimal, ROUND_HALF_UP
from ..schemas.calc_io import CalcInput, CalcOutput
from ..services.config_loader import load_settings

def _interpolate_price_per_meter(length_mm: float) -> float:
    s = load_settings()
    if length_mm < s.min_length:
        return s.price_per_meter_high
    if length_mm <= s.max_length:
        delta = (s.price_per_meter_high - s.price_per_meter_low) / (s.max_length - s.min_length)
        return s.price_per_meter_high - (length_mm - s.min_length) * delta
    return s.price_per_meter_low

def _round_nearest_10(x: float) -> int:
    d = (Decimal(str(x)) / Decimal("10")).quantize(Decimal("0"), rounding=ROUND_HALF_UP)
    return int(d * Decimal("10"))

def _round_ceil_10(x: float) -> int:
    return int(ceil(x / 10.0) * 10)

def compute(payload):
    # нормалізація
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump()
    elif hasattr(payload, "dict"):
        payload = payload.dict()
    if isinstance(payload, list):
        raise ValueError("payload must be object, not list")

    s = load_settings()

    L = int(payload.get("L") or payload.get("l") or 0)
    W = int(payload.get("W") or payload.get("w") or 0)
    H = int(payload.get("H") or payload.get("h") or 0)

    ppm = _interpolate_price_per_meter(L)
    price_base = round(ppm * L / 1000)

    surcharge_width  = 0.0
    surcharge_height = 0.0
    if W > s.min_width:
        surcharge_width = s.extra_price * (W - s.min_width) * L / 1000
    if H > s.min_height:
        surcharge_height = s.extra_price * (H - s.min_height) * L / 1000

    subtotal = price_base + surcharge_width + surcharge_height

    # назва опції може приходити в різних ключах
    pos_key = (
        payload.get("position")
        or payload.get("color")
        or payload.get("colors")
        or ""
    )
    try:
        pos_name = str(pos_key).strip()
    except Exception:
        pos_name = ""

    percent = float(s.positions.get(pos_name, 0.0))
    surcharge_color_amount = subtotal * percent / 100.0

    raw_total = subtotal + surcharge_color_amount
    total = (
        _round_nearest_10(raw_total) if s.rounding_mode == "nearest10"
        else _round_ceil_10(raw_total)
    )

    return CalcOutput(
        price_per_meter=ppm,
        price_base=int(price_base),
        surcharge_width=round(surcharge_width, 2),
        surcharge_height=round(surcharge_height, 2),
        surcharge_color_percent=percent,
        surcharge_color_amount=round(surcharge_color_amount, 2),
        price_total=total,
    )
