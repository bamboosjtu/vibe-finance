"""
对账警告状态模型 - Sprint 6 (S6-5)
用于管理警告的 acknowledged/muted 状态
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class WarningStatus(str):
    """警告状态枚举"""
    OPEN = "open"           # 未处理
    ACKNOWLEDGED = "acknowledged"  # 已确认
    MUTED = "muted"         # 已静音（已知差异）


class ReconciliationWarningRecord(SQLModel, table=True):
    """
    对账警告记录表
    
    用于持久化警告的状态管理，不影响计算，只影响展示
    """
    __tablename__ = "reconciliation_warnings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 警告唯一标识（由后端生成规则决定）
    warning_id: str = Field(index=True, unique=True, description="警告唯一标识")
    
    # 警告类型
    warning_type: str = Field(description="警告类型: account_diff/redeem_anomaly/valuation_gap")
    
    # 关联对象
    object_type: str = Field(description="对象类型: account/product")
    object_id: int = Field(description="对象ID")
    
    # 状态管理
    status: str = Field(default=WarningStatus.OPEN, description="状态: open/acknowledged/muted")
    
    # muted 原因（可选）
    mute_reason: Optional[str] = Field(default=None, description="静音原因")
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    
    class Config:
        arbitrary_types_allowed = True
