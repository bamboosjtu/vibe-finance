from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from typing import Optional
from datetime import date as DateType
from .base import BaseModel


class Snapshot(BaseModel, table=True):
    """资产快照模型（权威资产数据）"""
    __tablename__ = "snapshots"
    __table_args__ = (
        UniqueConstraint("date", "account_id", name="uix_snapshot_date_account"),
    )
    
    date: DateType = Field(description="快照日期", index=True)
    account_id: int = Field(foreign_key="accounts.id", description="账户ID", index=True)
    balance: float = Field(description="账户余额")
    
    # 关系
    account: Optional["Account"] = Relationship()
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-01-05",
                "account_id": 10,
                "balance": 6156.16
            }
        }
