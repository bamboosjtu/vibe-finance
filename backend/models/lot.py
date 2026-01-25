from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from enum import Enum
from datetime import date
from .base import BaseModel


class LotStatus(str, Enum):
    """批次状态枚举"""
    HOLDING = "holding"          # 持有中
    REDEEMING = "redeeming"      # 赎回中
    SETTLED = "settled"          # 已到账


class Lot(BaseModel, table=True):
    """持仓批次模型"""
    __tablename__ = "lots"
    
    product_id: int = Field(foreign_key="products.id", description="产品ID")
    open_date: date = Field(description="买入日期")
    principal: float = Field(gt=0, description="本金")
    status: LotStatus = Field(default=LotStatus.HOLDING, description="状态")
    note: Optional[str] = Field(default=None, description="备注")
    
    # 关系
    product: Optional["Product"] = Relationship(back_populates="lots")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 9001,
                "product_id": 200,
                "open_date": "2025-01-10",
                "principal": 100000,
                "status": "holding",
                "note": "第1次买入"
            }
        }
