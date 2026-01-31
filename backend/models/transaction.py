from datetime import date
from typing import Optional
from sqlmodel import Field, Relationship
from models.base import BaseModel


class TransactionCategory:
    """交易类型"""
    BUY = "buy"                    # 买入
    REDEEM_REQUEST = "redeem_request"  # 赎回申请
    REDEEM_SETTLE = "redeem_settle"    # 赎回到账
    FEE = "fee"                    # 费用


class Transaction(BaseModel, table=True):
    """
    交易流水表
    记录产品的所有资金流动事件
    """
    __tablename__ = "transactions"
    
    product_id: int = Field(foreign_key="products.id", description="关联产品")
    account_id: int = Field(foreign_key="accounts.id", description="关联账户")
    category: str = Field(description="交易类型: buy/redeem_request/redeem_settle/fee")
    trade_date: date = Field(description="交易日期")
    settle_date: Optional[date] = Field(default=None, description="到账/结算日期")
    amount: float = Field(description="金额（买入为正，卖出为负）")
    note: Optional[str] = Field(default=None, description="备注")
    
    # 关系
    product: Optional["Product"] = Relationship(back_populates="transactions")
    account: Optional["Account"] = Relationship(back_populates="transactions")
