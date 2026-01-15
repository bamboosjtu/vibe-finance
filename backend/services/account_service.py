from typing import List, Optional

from sqlmodel import Session, select

from models.account import Account, AccountType


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


def list_accounts(session: Session) -> List[Account]:
    statement = select(Account).order_by(Account.id)
    return list(session.exec(statement).all())


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
