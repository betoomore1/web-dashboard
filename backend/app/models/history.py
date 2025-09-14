from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, func, JSON
from ..models.base import Base

class CalcHistory(Base):
    __tablename__ = "calc_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True),
        server_default=func.now())
    input_json: Mapped[dict] = mapped_column(JSON)
    output_json: Mapped[dict] = mapped_column(JSON)
    user_id: Mapped[str | None] = mapped_column(default=None)
