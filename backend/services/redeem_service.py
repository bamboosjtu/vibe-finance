from datetime import date, timedelta
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, func
from models.transaction import Transaction, TransactionCategory
from models.product import Product


def calculate_pending_redeems(
    session: Session,
    product_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    计算在途赎回金额
    
    规则：在途金额 = Σ redeem_request.amount - Σ redeem_settle.amount
    注意：redeem_request 的 amount 为负数（表示资金流出产品）
    
    Args:
        session: 数据库会话
        product_id: 产品ID，为None时计算全局在途金额
        
    Returns:
        {
            "total_pending": float,  # 在途总额（正数表示金额）
            "items": [...]           # 明细列表
        }
    """
    # 查询 redeem_request 记录
    request_stmt = select(Transaction).where(
        Transaction.category == TransactionCategory.REDEEM_REQUEST
    )
    if product_id:
        request_stmt = request_stmt.where(Transaction.product_id == product_id)
    request_records = session.exec(request_stmt).all()
    
    # 查询 redeem_settle 记录
    settle_stmt = select(Transaction).where(
        Transaction.category == TransactionCategory.REDEEM_SETTLE
    )
    if product_id:
        settle_stmt = settle_stmt.where(Transaction.product_id == product_id)
    settle_records = session.exec(settle_stmt).all()
    
    # 计算在途金额
    # redeem_request 的 amount 是负数（资金流出产品）
    total_request = sum(abs(r.amount) for r in request_records)
    total_settle = sum(abs(s.amount) for s in settle_records)
    total_pending = max(0, total_request - total_settle)
    
    # 构建明细（按产品分组）
    pending_by_product: Dict[int, Dict[str, Any]] = {}
    
    for req in request_records:
        pid = req.product_id
        if pid not in pending_by_product:
            product = session.get(Product, pid)
            pending_by_product[pid] = {
                "product_id": pid,
                "product_name": product.name if product else "未知产品",
                "request_amount": 0.0,
                "settle_amount": 0.0,
                "pending_amount": 0.0,
                "requests": []
            }
        pending_by_product[pid]["request_amount"] += abs(req.amount)
        pending_by_product[pid]["requests"].append({
            "trade_date": req.trade_date.isoformat(),
            "amount": abs(req.amount),
            "settle_date": req.settle_date.isoformat() if req.settle_date else None
        })
    
    for settle in settle_records:
        pid = settle.product_id
        if pid in pending_by_product:
            pending_by_product[pid]["settle_amount"] += abs(settle.amount)
    
    # 计算每个产品的在途金额
    items = []
    for pid, data in pending_by_product.items():
        pending = max(0, data["request_amount"] - data["settle_amount"])
        if pending > 0:
            data["pending_amount"] = pending
            # 找到最晚的预计到账日
            latest_settle_date = None
            for req in data["requests"]:
                if req["settle_date"]:
                    req_date = date.fromisoformat(req["settle_date"])
                    if latest_settle_date is None or req_date > latest_settle_date:
                        latest_settle_date = req_date
            
            items.append({
                "product_id": data["product_id"],
                "product_name": data["product_name"],
                "pending_amount": pending,
                "latest_request_date": min(
                    (date.fromisoformat(r["trade_date"]) for r in data["requests"]),
                    default=None
                ).isoformat() if data["requests"] else None,
                "estimated_settle_date": latest_settle_date.isoformat() if latest_settle_date else None
            })
    
    return {
        "total_pending": total_pending,
        "items": items
    }


def get_product_pending_redeem(
    session: Session,
    product_id: int
) -> Dict[str, Any]:
    """
    获取单个产品的在途赎回信息
    
    Returns:
        {
            "product_id": int,
            "pending_amount": float,
            "latest_request_date": str,
            "estimated_settle_date": str
        }
    """
    result = calculate_pending_redeems(session, product_id)
    
    if result["items"]:
        item = result["items"][0]
        return {
            "product_id": product_id,
            "pending_amount": item["pending_amount"],
            "latest_request_date": item["latest_request_date"],
            "estimated_settle_date": item["estimated_settle_date"]
        }
    
    return {
        "product_id": product_id,
        "pending_amount": 0.0,
        "latest_request_date": None,
        "estimated_settle_date": None
    }


def calculate_future_cash_flow(
    session: Session,
    start_date: Optional[date] = None,
    days: int = 30
) -> List[Dict[str, Any]]:
    """
    计算未来可用现金流预测
    
    来源：
    1. 已发起赎回（redeem_request）- 根据 settle_date 或 T+N 规则推算
    2. 明确到期产品（如定期理财）- 基于买入日期 + term_days
    
    Args:
        session: 数据库会话
        start_date: 开始日期，默认为今天
        days: 预测天数
        
    Returns:
        按日期排序的现金流预测列表
    """
    if start_date is None:
        start_date = date.today()
    
    end_date = start_date + timedelta(days=days)
    
    cash_flows = []
    
    # 1. 查询所有在途赎回请求
    request_stmt = select(Transaction, Product).join(
        Product, Transaction.product_id == Product.id
    ).where(
        Transaction.category == TransactionCategory.REDEEM_REQUEST
    )
    request_records = session.exec(request_stmt).all()
    
    # 查询已到账的赎回（用于计算在途）
    settle_stmt = select(Transaction).where(
        Transaction.category == TransactionCategory.REDEEM_SETTLE
    )
    settle_records = session.exec(settle_stmt).all()
    
    # 按产品分组统计已到账金额
    settled_by_product: Dict[int, float] = {}
    for settle in settle_records:
        settled_by_product[settle.product_id] = settled_by_product.get(
            settle.product_id, 0.0
        ) + abs(settle.amount)
    
    # 处理每个赎回请求
    for transaction, product in request_records:
        request_amount = abs(transaction.amount)
        product_id = transaction.product_id
        
        # 扣除已到账部分
        settled = settled_by_product.get(product_id, 0.0)
        if settled >= request_amount:
            settled_by_product[product_id] = settled - request_amount
            continue  # 这笔请求已完全到账
        else:
            pending_amount = request_amount - settled
            settled_by_product[product_id] = 0.0
        
        # 确定预计到账日
        if transaction.settle_date:
            estimated_date = transaction.settle_date
        elif product:
            # 根据 T+N 规则推算
            estimated_date = transaction.trade_date + timedelta(days=product.settle_days)
        else:
            estimated_date = transaction.trade_date + timedelta(days=1)
        
        # 只保留在预测范围内的
        if start_date <= estimated_date <= end_date:
            cash_flows.append({
                "date": estimated_date.isoformat(),
                "amount": pending_amount,
                "source": "redeem",
                "description": f"{product.name if product else '未知产品'} 赎回到账",
                "product_id": product_id
            })
    
    # 2. 查询定期产品到期（简化处理：基于最近买入 + term_days）
    # Sprint 4 不做 Lot，使用规则性汇总：最近买入日期 + term_days 作为预计到期日
    # 仅针对有明确期限的定期产品（term_days > 0 且 liquidity_rule != open）
    maturity_stmt = select(Transaction, Product).join(
        Product, Transaction.product_id == Product.id
    ).where(
        Transaction.category == TransactionCategory.BUY
    ).where(
        Product.term_days > 0
    ).where(
        Product.liquidity_rule != 'open'  # 非开放式产品（定期存款、封闭式理财等）
    )
    maturity_records = session.exec(maturity_stmt).all()
    
    # 按产品分组，取最近一笔买入
    latest_buy_by_product: Dict[int, Dict[str, Any]] = {}
    for transaction, product in maturity_records:
        product_id = product.id
        if product_id not in latest_buy_by_product:
            latest_buy_by_product[product_id] = {
                "product": product,
                "latest_trade_date": transaction.trade_date,
                "total_amount": 0.0
            }
        # 累计买入金额（简化处理，不追踪具体批次）
        latest_buy_by_product[product_id]["total_amount"] += transaction.amount
        # 更新最近买入日期
        if transaction.trade_date > latest_buy_by_product[product_id]["latest_trade_date"]:
            latest_buy_by_product[product_id]["latest_trade_date"] = transaction.trade_date
    
    # 计算每个定期产品的预计到期日
    for product_id, data in latest_buy_by_product.items():
        product = data["product"]
        latest_buy_date = data["latest_trade_date"]
        total_amount = data["total_amount"]
        
        # 计算预计到期日：最近买入日期 + term_days
        estimated_maturity_date = latest_buy_date + timedelta(days=product.term_days)
        
        # 只保留在预测范围内的
        if start_date <= estimated_maturity_date <= end_date:
            cash_flows.append({
                "date": estimated_maturity_date.isoformat(),
                "amount": total_amount,
                "source": "maturity",
                "description": f"{product.name} 产品到期（基于最近买入+期限推算）",
                "product_id": product_id,
                "note": "规则推算，仅供参考"
            })
    
    # 按日期聚合
    cash_flows.sort(key=lambda x: x["date"])
    
    return cash_flows


def summarize_future_cash_flow(
    session: Session,
    days_7: int = 7,
    days_30: int = 30
) -> Dict[str, Any]:
    """
    汇总未来现金流（7天和30天）
    
    Returns:
        {
            "items": [...],  # 全部明细
            "total_7d": float,
            "total_30d": float,
            "by_date": {     # 按日期聚合
                "2024-01-15": [...],
                ...
            }
        }
    """
    cash_flows = calculate_future_cash_flow(session, days=days_30)
    
    today = date.today()
    date_7d = today + timedelta(days=days_7)
    
    total_7d = sum(
        item["amount"] for item in cash_flows 
        if date.fromisoformat(item["date"]) <= date_7d
    )
    total_30d = sum(item["amount"] for item in cash_flows)
    
    # 按日期分组
    by_date: Dict[str, List[Dict]] = {}
    for item in cash_flows:
        d = item["date"]
        if d not in by_date:
            by_date[d] = []
        by_date[d].append(item)
    
    return {
        "items": cash_flows,
        "total_7d": total_7d,
        "total_30d": total_30d,
        "by_date": by_date
    }
