from fastapi import APIRouter, HTTPException
from ..schemas.calc_io import CalcInput, CalcOutput, CalcConfig
from ..services.config_loader import load_settings
from ..services.calc_engine import compute

router = APIRouter(prefix="/api/calc", tags=["calc"])

@router.get("/config", response_model=CalcConfig)
def get_config():
    s = load_settings()

    # s.positions зараз — список груп. Шукаємо групу 'colors' і будуємо dict.
    positions_map = {}
    try:
        colors = next((g for g in s.positions if g.get("id") == "colors"), None)
        if colors:
            for it in colors.get("items", []):
                name = (it.get("name") or "").strip() or "item"
                # у схемі очікується float: беремо беззнакове число
                positions_map[name] = float(it.get("value", 0))
    except Exception:
        positions_map = {}

    return {
        "variables": {
            "min_length": s.min_length,
            "max_length": s.max_length,
            "min_width":  s.min_width,
            "min_height": s.min_height,
            "extra_price": s.extra_price,
            "rounding":   s.rounding_mode,
        },
        "price_per_meter": {
            "high": s.price_per_meter_high,
            "low":  s.price_per_meter_low,
        },
        "positions": positions_map,  # <-- тепер відповідає CalcConfig
    }

@router.post("/compute", response_model=CalcOutput)
def post_compute(payload: CalcInput):
    try:
        # було: return compute(payload)
        return compute(payload.model_dump())  # <-- передаємо dict
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

