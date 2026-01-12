from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from enum import Enum
from .base import BaseModel


class AccountType(str, Enum):
    """账户类型枚举"""
    CASH = "cash"          # 现金
    DEBIT = "debit"        # 借记卡
    CREDIT = "credit"      # 信用卡
    INVESTMENT = "investment"  # 投资账户


class Account(BaseModel, table=True):
    """账户模型"""
    __tablename__ = "accounts"
    
    name: str = Field(description="账户名称")
    institution_id: int = Field(foreign_key="institutions.id", description="所属机构ID")
    type: AccountType = Field(description="账户类型")
    is_liquid: bool = Field(default=True, description="是否计入可用现金")
    
    # 关系
    institution: Optional["Institution"] = Relationship(back_populates="accounts")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 10,
                "name": "长沙银行-借记卡",
                "institution_id": 1,
                "type": "debit",
                "is_liquid": True
            }
        }
