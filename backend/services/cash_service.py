from datetime import date, timedelta
from typing import Dict, Any, Optional, List
from sqlmodel import Session, select
from models.snapshot import Snapshot
from models.account import Account
from models.product import Product
from models.transaction import Transaction, TransactionCategory
from services.redeem_service import calculate_pending_redeems, summarize_future_cash_flow, calculate_future_cash_flow


def calculate_locked_in_products(session: Session) -> Dict[str, Any]:
    """
    计算锁定在产品中的资金总额
    
    Sprint 5：用于时间轴视图，展示"被锁定的资金"
    计算逻辑：所有产品的最新市值总和（简化处理，不精确到 Lot）
    
    Returns:
        {
            "total_locked": float,
            "by_product": [...]
        }
    """
    from models.valuation import ProductValuation
    
    # 查询每个产品的最新估值
    stmt = (
        select(Product, ProductValuation.market_value)
        .join(
            ProductValuation,
            Product.id == ProductValuation.product_id
        )
        .where(
            ProductValuation.date == (
                select(ProductValuation.date)
                .where(ProductValuation.product_id == Product.id)
                .order_by(ProductValuation.date.desc())
                .limit(1)
            )
        )
    )
    
    # 简化处理：查询所有产品和最新估值
    products = session.exec(select(Product)).all()
    
    total_locked = 0.0
    by_product = []
    
    for product in products:
        # 获取产品最新估值
        latest_valuation = session.exec(
            select(ProductValuation)
            .where(ProductValuation.product_id == product.id)
            .order_by(ProductValuation.date.desc())
            .limit(1)
        ).first()
        
        if latest_valuation and latest_valuation.market_value:
            total_locked += latest_valuation.market_value
            by_product.append({
                "product_id": product.id,
                "product_name": product.name,
                "market_value": latest_valuation.market_value,
                "liquidity_rule": product.liquidity_rule.value,
                "term_days": product.term_days
            })
    
    return {
        "total_locked": total_locked,
        "by_product": by_product
    }


def calculate_cash_timeline(
    session: Session,
    milestones: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    计算资金时间轴视图（Sprint 5 核心功能）
    
    展示从当前时间点开始的资金流动性变化：
    - 当前：可用现金、在途赎回、锁定资金
    - 未来里程碑：+7d、+30d、+90d 的预计可用现金
    
    Args:
        session: 数据库会话
        milestones: 里程碑天数列表，默认 [7, 30, 90]
        
    Returns:
        {
            "current": {
                "available_cash": float,
                "pending_redeems": float,
                "locked_in_products": float
            },
            "milestones": [...]
        }
    """
    if milestones is None:
        milestones = [7, 30, 90]
    
    today = date.today()
    
    # 1. 计算当前状态
    cash_summary = get_cash_summary(session)
    locked = calculate_locked_in_products(session)
    
    current = {
        "date": today.isoformat(),
        "available_cash": cash_summary["real_available"],
        "pending_redeems": cash_summary["pending_redeems"],
        "locked_in_products": locked["total_locked"]
    }
    
    # 2. 计算未来现金流（最长到最大里程碑）
    max_days = max(milestones)
    future_flows = calculate_future_cash_flow(session, start_date=today, days=max_days)
    
    # 3. 构建里程碑视图
    milestone_list = []
    
    for days in milestones:
        milestone_date = today + timedelta(days=days)
        
        # 统计到这个里程碑日期为止的预计到账
        accumulated = sum(
            flow["amount"] 
            for flow in future_flows 
            if date.fromisoformat(flow["date"]) <= milestone_date
        )
        
        # 预计可用现金 = 当前可用 + 累计到账
        projected_available = cash_summary["real_available"] + accumulated
        
        # 这个里程碑期间的变化
        changes = [
            flow for flow in future_flows
            if today < date.fromisoformat(flow["date"]) <= milestone_date
        ]
        
        milestone_list.append({
            "date": milestone_date.isoformat(),
            "label": f"+{days}天",
            "days_from_now": days,
            "projected_available_cash": projected_available,
            "accumulated_inflow": accumulated,
            "changes": changes
        })
    
    return {
        "current": current,
        "milestones": milestone_list
    }


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
            "future_90d": float,          # 未来90天预计到账（Sprint 5 新增）
        }
    """
    # 计算可用现金
    available_cash = calculate_available_cash(session, target_date)
    
    # 计算未来现金流（统一计算 7/30/90 天）
    today = date.today()
    future_flows_90d = calculate_future_cash_flow(session, start_date=today, days=90)
    
    date_7d = today + timedelta(days=7)
    date_30d = today + timedelta(days=30)
    
    total_7d = sum(
        flow["amount"] for flow in future_flows_90d 
        if date.fromisoformat(flow["date"]) <= date_7d
    )
    total_30d = sum(
        flow["amount"] for flow in future_flows_90d 
        if date.fromisoformat(flow["date"]) <= date_30d
    )
    total_90d = sum(flow["amount"] for flow in future_flows_90d)
    
    return {
        "date": available_cash["date"],
        "base_available": available_cash["base_available"],
        "pending_redeems": available_cash["pending_redeems"],
        "real_available": available_cash["real_available"],
        "future_7d": total_7d,
        "future_30d": total_30d,
        "future_90d": total_90d,
    }
