from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from enum import Enum
from .base import BaseModel


class ProductType(str, Enum):
    """产品类型枚举"""
    BANK_WMP = "bank_wmp"      # 银行理财
    FUND = "fund"              # 基金
    INSURANCE = "insurance"    # 保险
    OTHER = "other"            # 其他


class RiskLevel(str, Enum):
    """风险等级枚举"""
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    R5 = "R5"


class LiquidityRule(str, Enum):
    """流动性规则枚举"""
    OPEN = "open"              # 开放
    CLOSED = "closed"          # 封闭
    SCHEDULED = "scheduled"    # 定开


class Product(BaseModel, table=True):
    """理财产品模型"""
    __tablename__ = "products"
    
    name: str = Field(description="产品名称")
    institution_id: int = Field(foreign_key="institutions.id", description="所属机构ID")
    product_type: ProductType = Field(description="产品类型")
    risk_level: RiskLevel = Field(description="风险等级")
    term_days: Optional[int] = Field(default=None, description="期限天数")
    liquidity_rule: LiquidityRule = Field(description="流动性规则")
    settle_days: int = Field(default=1, description="赎回到账天数")
    note: Optional[str] = Field(default=None, description="备注")
    
    # 关系
    institution: Optional["Institution"] = Relationship(back_populates="products")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 200,
                "name": "28D",
                "institution_id": 1,
                "product_type": "bank_wmp",
                "risk_level": "R2",
                "term_days": 28,
                "liquidity_rule": "closed",
                "settle_days": 1,
                "note": "到期赎回"
            }
        }
