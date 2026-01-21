from typing import List, Optional

from sqlmodel import Session, select, delete, func

from models.account import Account, AccountType
from models.snapshot import Snapshot


def _default_is_liquid(account_type: AccountType) -> bool:
    if account_type == AccountType.CREDIT:
        return False
    return True


def create_account(
    session: Session,
    name: str,
    account_type: AccountType,
    institution_id: Optional[int] = None,
    is_liquid: Optional[bool] = None,
    currency: str = "CNY",
) -> Account:
    if is_liquid is None:
        is_liquid = _default_is_liquid(account_type)

    account = Account(
        name=name,
        institution_id=institution_id,
        type=account_type,
        is_liquid=is_liquid,
        currency=currency,
    )
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def delete_account(session: Session, account_id: int) -> None:
    account = session.get(Account, account_id)
    if not account:
        raise ValueError("account not found")
    
    # 手动删除关联的快照，因为没有配置级联删除
    statement = delete(Snapshot).where(Snapshot.account_id == account_id)
    session.exec(statement)
    
    session.delete(account)
    session.commit()



def list_accounts(session: Session) -> List[dict]:
    """
    列出账户，并包含最近一次快照的余额
    """
    from models.institution import Institution
    
    # 查找每个账户最近的快照日期和余额
    # Subquery to find max date per account
    subquery = select(
        Snapshot.account_id, 
        func.max(Snapshot.date).label("max_date")
    ).group_by(
        Snapshot.account_id
    ).subquery()
    
    # Query accounts with latest balance
    statement = (
        select(Account, Snapshot.balance, Snapshot.date)
        .outerjoin(Institution, Account.institution_id == Institution.id)
        .outerjoin(subquery, Account.id == subquery.c.account_id)
        .outerjoin(Snapshot, (Snapshot.account_id == Account.id) & (Snapshot.date == subquery.c.max_date))
        .order_by(Account.type, Institution.name, Account.name)
    )
    
    results = session.exec(statement).all()
    
    items = []
    for account, balance, snap_date in results:
        item = account.model_dump()
        item['latest_balance'] = balance
        item['latest_date'] = snap_date.isoformat() if snap_date else None
        items.append(item)
        
    return items


def patch_account(
    session: Session,
    account_id: int,
    name: Optional[str] = None,
    institution_id: Optional[int] = None,
    account_type: Optional[AccountType] = None,
    is_liquid: Optional[bool] = None,
    currency: Optional[str] = None,
) -> Account:
    account = session.get(Account, account_id)
    if not account:
        raise ValueError("account not found")

    if name is not None:
        account.name = name
    if institution_id is not None:
        account.institution_id = institution_id
    if account_type is not None:
        account.type = account_type
        if is_liquid is None:
            account.is_liquid = _default_is_liquid(account_type)
    if is_liquid is not None:
        account.is_liquid = is_liquid
    if currency is not None:
        account.currency = currency

    session.add(account)
    session.commit()
    session.refresh(account)
    return account
