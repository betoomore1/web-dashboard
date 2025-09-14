from fastapi import APIRouter, HTTPException
from ..schemas.calc_io import CalcInput, CalcOutput, CalcConfig
from ..services.config_loader import load_settings
from ..services.calc_engine import compute

router = APIRouter(prefix="/api/calc", tags=["calc"])

@router.get("/config", response_model=CalcConfig)
def get_config():
    s = load_settings()
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
        "positions": s.positions,  # <-- уже dict з лоадера
    }

@router.post("/compute", response_model=CalcOutput)
def post_compute(payload: CalcInput):
    try:
        body = payload.model_dump() if hasattr(payload, "model_dump") else (
            payload.dict() if hasattr(payload, "dict") else payload
        )
        return compute(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    