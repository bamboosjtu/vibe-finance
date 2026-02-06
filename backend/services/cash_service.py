from datetime import date
from typing import Dict, Any, Optional
from sqlmodel import Session, select
from models.snapshot import Snapshot
from models.account import Account
from services.redeem_service import calculate_pending_redeems, summarize_future_cash_flow


def calculate_available_cash(
    session: Session,
    target_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    计算实际可用现金
    
    定义：
    可用现金 = Σ 账户余额（is_liquid = true） - 在途赎回金额
    
    规则：
    - 不包含赎回在途资金
    - 不包含尚未到账的收入
    - Snapshot 仍是账户余额的权威来源
    
    Args:
        session: 数据库会话
        target_date: 目标日期，默认为最新快照日期
        
    Returns:
        {
            "base_available": float,      # 基础可用现金（账户余额）
            "pending_redeems": float,     # 在途赎回金额
            "real_available": float,      # 实际可用现金
            "details": {
                "liquid_accounts": [...], # 流动账户明细
            }
        }
    """
    if target_date is None:
        # 获取最新快照日期
        latest_stmt = select(Snapshot.date).order_by(Snapshot.date.desc()).limit(1)
        latest_date = session.exec(latest_stmt).first()
        target_date = latest_date or date.today()
    
    # 1. 获取所有流动账户的最新余额
    stmt = (
        select(Snapshot, Account)
        .join(Account, Snapshot.account_id == Account.id)
        .where(Snapshot.date == target_date)
        .where(Account.is_liquid == True)
    )
    
    results = session.exec(stmt).all()
    
    liquid_accounts = []
    base_available = 0.0
    
    for snapshot, account in results:
        balance = snapshot.balance if snapshot.balance is not None else 0.0
        base_available += balance
        
        liquid_accounts.append({
            "account_id": account.id,
            "account_name": account.name,
            "account_type": account.type,
            "balance": balance
        })
    
    # 2. 计算在途赎回金额
    pending_result = calculate_pending_redeems(session)
    pending_redeems = pending_result["total_pending"]
    
    # 3. 计算实际可用现金
    # 注意：在途赎回是资金从产品中流出但未到账，所以要从可用现金中扣除
    real_available = base_available - pending_redeems
    
    return {
        "date": target_date.isoformat(),
        "base_available": base_available,
        "pending_redeems": pending_redeems,
        "real_available": real_available,
        "details": {
            "liquid_accounts": liquid_accounts,
            "pending_details": pending_result["items"]
        }
    }


def get_cash_summary(
    session: Session,
    target_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    获取现金汇总信息（用于 Dashboard）
    
    Returns:
        {
            "date": str,
            "base_available": float,      # 基础可用现金
            "pending_redeems": float,     # 在途赎回
            "real_available": float,      # 实际可用现金
            "future_7d": float,           # 未来7天预计到账
            "future_30d": float,          # 未来30天预计到账
        }
    """
    # 计算可用现金
    available_cash = calculate_available_cash(session, target_date)
    
    # 计算未来现金流
    future_cash = summarize_future_cash_flow(session)
    
    return {
        "date": available_cash["date"],
        "base_available": available_cash["base_available"],
        "pending_redeems": available_cash["pending_redeems"],
        "real_available": available_cash["real_available"],
        "future_7d": future_cash["total_7d"],
        "future_30d": future_cash["total_30d"],
    }
