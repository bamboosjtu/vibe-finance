from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class BaseModel(SQLModel):
    """基础模型类"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
