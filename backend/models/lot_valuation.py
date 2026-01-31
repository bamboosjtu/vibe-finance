from datetime import date as DateType
from typing import Optional
from sqlmodel import Field, Relationship, UniqueConstraint
from .base import BaseModel

class LotValuation(BaseModel, table=True):
    __tablename__ = "lot_valuations"
    __table_args__ = (UniqueConstraint("lot_id", "date", name="unique_lot_date_valuation"),)

    lot_id: int = Field(foreign_key="lots.id", description="批次ID")
    date: DateType = Field(description="估值日期")
    market_value: float = Field(description="持有市值")
    
    # Relationship
    lot: Optional["Lot"] = Relationship(back_populates="valuations")
