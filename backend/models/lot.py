from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from enum import Enum
from datetime import date
from .base import BaseModel
from .lot_valuation import LotValuation


class LotStatus(str, Enum):
    """批次状态枚举"""
    HOLDING = "holding"          # 持有中
    CLOSED = "closed"            # 已关闭/已卖出


class Lot(BaseModel, table=True):
    """持仓批次模型"""
    __tablename__ = "lots"
    
    product_id: int = Field(foreign_key="products.id", description="产品ID")
    open_date: date = Field(description="买入日期")
    principal: float = Field(gt=0, description="本金")
    status: LotStatus = Field(default=LotStatus.HOLDING, description="状态")
    close_date: Optional[date] = Field(default=None, description="关闭/卖出日期")
    note: Optional[str] = Field(default=None, description="备注")
    
    # 关系
    product: Optional["Product"] = Relationship(back_populates="lots")
    valuations: List["LotValuation"] = Relationship(back_populates="lot")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 9001,
                "product_id": 200,
                "open_date": "2025-01-10",
                "principal": 100000,
                "status": "holding",
                "close_date": None,
                "note": "第1次买入"
            }
        }
