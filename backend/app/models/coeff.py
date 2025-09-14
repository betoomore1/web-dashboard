from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, func
from ..models.base import Base

class Coeff(Base):
    __tablename__ = "coeff"
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    value: Mapped[float] = mapped_column(Float)
    updated_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True),
        server_default=func.now(), onupdate=func.now())
