from typing import List, Dict, Any, Tuple
from datetime import date
from sqlmodel import Session, select
from models.snapshot import Snapshot
from models.account import Account


def batch_upsert_snapshots(
    session: Session,
    snapshots_data: List[Dict[str, Any]]
) -> Tuple[int, int, List[str]]:
    """
    批量更新/插入快照
    
    Args:
        session: 数据库会话
        snapshots_data: 快照数据列表，每项包含 date, account_id, balance
        
    Returns:
        (inserted_count, updated_count, warnings)
    """
    inserted = 0
    updated = 0
    warnings = []
    
    # 预处理数据：按 (date, account_id) 分组，确保无重复
    # 这里的业务逻辑是：如果有重复，后面的覆盖前面的
    
    for item in snapshots_data:
        snapshot_date = item.get("date")
        # 处理日期字符串转换 (如果输入是字符串)
        if isinstance(snapshot_date, str):
            try:
                snapshot_date = date.fromisoformat(snapshot_date)
            except ValueError:
                warnings.append(f"Invalid date format: {item.get('date')}")
                continue
                
        account_id = item.get("account_id")
        balance = item.get("balance")
        
        if not account_id or balance is None:
            warnings.append(f"Missing account_id or balance for date {snapshot_date}")
            continue
            
        # 检查账户是否存在
        account = session.get(Account, account_id)
        if not account:
            warnings.append(f"Account {account_id} not found")
            continue
            
        # 查找现有快照
        statement = select(Snapshot).where(
            Snapshot.date == snapshot_date,
            Snapshot.account_id == account_id
        )
        existing_snapshot = session.exec(statement).first()
        
        if existing_snapshot:
            # 更新
            if existing_snapshot.balance != balance:
                existing_snapshot.balance = balance
                session.add(existing_snapshot)
                updated += 1
        else:
            # 插入
            new_snapshot = Snapshot(
                date=snapshot_date,
                account_id=account_id,
                balance=balance
            )
            session.add(new_snapshot)
            inserted += 1
            
    session.commit()
    
    return inserted, updated, warnings


from sqlmodel import Session, select, func

def list_snapshots(
    session: Session,
    snapshot_date: date,
    fill_previous: bool = False
) -> List[Snapshot]:
    """
    获取快照列表
    
    Args:
        session: 数据库会话
        snapshot_date: 查询日期
        fill_previous: 是否回溯最近的快照（如果当天没有，则取该日期之前最近的一条）
    """
    if not fill_previous:
        statement = select(Snapshot).where(Snapshot.date == snapshot_date)
        return session.exec(statement).all()
    
    # 回溯逻辑：查找每个账户在 snapshot_date 之前的最近一条记录
    # SQL: 
    # SELECT * FROM snapshot s
    # JOIN (
    #   SELECT account_id, MAX(date) as max_date
    #   FROM snapshot
    #   WHERE date <= :date
    #   GROUP BY account_id
    # ) max_s ON s.account_id = max_s.account_id AND s.date = max_s.max_date
    
    subquery = select(
        Snapshot.account_id, 
        func.max(Snapshot.date).label("max_date")
    ).where(
        Snapshot.date <= snapshot_date
    ).group_by(
        Snapshot.account_id
    ).subquery()
    
    statement = select(Snapshot).join(
        subquery,
        (Snapshot.account_id == subquery.c.account_id) & 
        (Snapshot.date == subquery.c.max_date)
    )
    
    return session.exec(statement).all()
