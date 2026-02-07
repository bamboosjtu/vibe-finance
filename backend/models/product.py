from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from enum import Enum
from .base import BaseModel


class ProductType(str, Enum):
    """产品类型枚举"""
    BANK_WMP = "bank_wmp"      # 银行理财
    MONEY_MARKET = "money_market"  # 货币基金/活期类
    TERM_DEPOSIT = "term_deposit"  # 定期存款
    FUND = "fund"              # 基金
    STOCK = "stock"            # 股票
    OTHER = "other"            # 其他


class LiquidityRule(str, Enum):
    """流动性规则枚举"""
    OPEN = "open"              # 开放
    CLOSED = "closed"          # 封闭
    PERIODIC_OPEN = "periodic_open"    # 定开


class ValuationMode(str, Enum):
    """估值模式枚举"""
    PRODUCT_VALUE = "product_value"    # 产品级别估值


class Product(BaseModel, table=True):
    """理财产品模型"""
    __tablename__ = "products"
    
    name: str = Field(description="产品名称")
    institution_id: Optional[int] = Field(default=None, foreign_key="institutions.id", description="所属机构ID")
    product_code: Optional[str] = Field(default=None, description="产品代码")
    product_type: ProductType = Field(description="产品类型")
    risk_level: Optional[str] = Field(default=None, description="风险等级")
    term_days: Optional[int] = Field(default=None, description="期限天数")
    liquidity_rule: LiquidityRule = Field(description="流动性规则")
    settle_days: int = Field(default=1, description="赎回到账天数")
    note: Optional[str] = Field(default=None, description="备注")
    valuation_mode: ValuationMode = Field(default=ValuationMode.PRODUCT_VALUE, description="估值模式")
    
    # 关系
    institution: Optional["Institution"] = Relationship(back_populates="products")
    valuations: List["ProductValuation"] = Relationship(back_populates="product")
    transactions: List["Transaction"] = Relationship(back_populates="product")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 200,
                "name": "28D",
                "institution_id": 1,
                "product_code": None,
                "product_type": "bank_wmp",
                "risk_level": "R2",
                "term_days": 28,
                "liquidity_rule": "closed",
                "settle_days": 1,
                "note": "到期赎回",
                "valuation_mode": "product_value"
            }
        }
