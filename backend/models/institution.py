from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from .base import BaseModel


class Institution(BaseModel, table=True):
    """机构模型（银行/平台）"""
    __tablename__ = "institutions"
    
    name: str = Field(index=True, unique=True, description="机构名称")
    
    # 关系
    accounts: List["Account"] = Relationship(back_populates="institution")
    products: List["Product"] = Relationship(back_populates="institution")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "长沙银行"
            }
        }
