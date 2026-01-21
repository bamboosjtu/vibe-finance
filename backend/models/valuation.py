from datetime import date as DateType
from typing import Optional
from sqlmodel import Field, Relationship, UniqueConstraint
from .base import BaseModel

class ProductValuation(BaseModel, table=True):
    __tablename__ = "product_valuations"
    __table_args__ = (UniqueConstraint("product_id", "date", name="unique_product_date_valuation"),)

    product_id: int = Field(foreign_key="products.id", description="产品ID")
    date: DateType = Field(description="估值日期")
    market_value: float = Field(description="单位净值或持有市值")
    
    # Relationship
    product: Optional["Product"] = Relationship(back_populates="valuations")
