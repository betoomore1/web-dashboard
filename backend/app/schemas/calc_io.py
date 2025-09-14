from pydantic import BaseModel, Field, PositiveInt
from typing import Dict

class CalcInput(BaseModel):
    length_mm: PositiveInt = Field(..., description="Довжина виробу, мм")
    width_mm:  PositiveInt = Field(..., description="Ширина виробу, мм")
    height_mm: PositiveInt = Field(..., description="Висота виробу, мм")
    position:  str          = Field(..., description="Назва позиції/кольору з конфігу")

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
