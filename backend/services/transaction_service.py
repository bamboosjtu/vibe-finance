from datetime import date
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, delete

from models.transaction import Transaction


def create_transaction(
    session: Session,
    product_id: int,
    account_id: int,
    category: str,
    trade_date: date,
    amount: float,
    settle_date: Optional[date] = None,
    note: Optional[str] = None
) -> Transaction:
    """
    创建交易记录
    """
    # 如果 trade_date 是字符串，转换为 date
    if isinstance(trade_date, str):
        trade_date = date.fromisoformat(trade_date)
    if settle_date and isinstance(settle_date, str):
        settle_date = date.fromisoformat(settle_date)
    
    transaction = Transaction(
        product_id=product_id,
        account_id=account_id,
        category=category,
        trade_date=trade_date,
        settle_date=settle_date,
        amount=amount,
        note=note
    )
    
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    
    return transaction


def list_transactions(
    session: Session,
    product_id: Optional[int] = None,
    account_id: Optional[int] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    查询交易记录列表
    """
    statement = select(Transaction)
    
    # 应用过滤条件
    if product_id:
        statement = statement.where(Transaction.product_id == product_id)
    if account_id:
        statement = statement.where(Transaction.account_id == account_id)
    if category:
        statement = statement.where(Transaction.category == category)
    if start_date:
        statement = statement.where(Transaction.trade_date >= start_date)
    if end_date:
        statement = statement.where(Transaction.trade_date <= end_date)
    
    # 按交易日期倒序
    statement = statement.order_by(Transaction.trade_date.desc())
    
    # 获取总数
    total = len(session.exec(statement).all())
    
    # 分页
    offset = (page - 1) * page_size
    statement = statement.offset(offset).limit(page_size)
    
    items = session.exec(statement).all()
    
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


def delete_transaction(session: Session, transaction_id: int) -> bool:
    """
    删除交易记录
    """
    transaction = session.get(Transaction, transaction_id)
    if not transaction:
        return False
    
    session.delete(transaction)
    session.commit()
    
    return True


def get_product_transactions(
    session: Session,
    product_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Transaction]:
    """
    获取指定产品的交易记录
    """
    statement = select(Transaction).where(Transaction.product_id == product_id)
    
    if start_date:
        statement = statement.where(Transaction.trade_date >= start_date)
    if end_date:
        statement = statement.where(Transaction.trade_date <= end_date)
    
    # 按交易日期正序
    statement = statement.order_by(Transaction.trade_date.asc())
    
    return session.exec(statement).all()
