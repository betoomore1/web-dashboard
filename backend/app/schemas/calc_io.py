from pydantic import BaseModel, Field, PositiveInt
from typing import Dict, Optional

class CalcInput(BaseModel):
    L: Optional[int] = None
    W: Optional[int] = None
    H: Optional[int] = None
    length: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    position: Optional[str] = None  # назва вибраної опції кольору

class CalcOutput(BaseModel):
    price_per_meter: float
    price_base: int
    surcharge_width: float
    surcharge_height: float
    surcharge_color_percent: float
    surcharge_color_amount: float
    price_total: int

class CalcConfig(BaseModel):
    variables: Dict[str, float | int | str]   # тут буде і 'rounding'
    price_per_meter: Dict[str, float]         # {"high":..., "low":...}
    positions: Dict[str, float]
