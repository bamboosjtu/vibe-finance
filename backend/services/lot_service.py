from sqlmodel import Session, select
from models.lot import Lot, LotStatus
from models.product import Product
from typing import List, Optional
from datetime import date


def create_lot(
    session: Session,
    product_id: int,
    open_date: date,
    principal: float,
    note: Optional[str] = None,
) -> Lot:
    """创建持仓批次"""
    lot = Lot(
        product_id=product_id,
        open_date=open_date,
        principal=principal,
        status=LotStatus.HOLDING,
        note=note,
    )
    session.add(lot)
    session.commit()
    session.refresh(lot)
    return lot


def list_lots_by_product(session: Session, product_id: int) -> List[Lot]:
    """获取指定产品的所有批次"""
    statement = select(Lot).where(Lot.product_id == product_id).order_by(Lot.open_date.desc())
    results = session.exec(statement)
    return results.all()


def get_lot(session: Session, lot_id: int) -> Optional[Lot]:
    """获取单个批次"""
    statement = select(Lot).where(Lot.id == lot_id)
    results = session.exec(statement)
    return results.first()


def patch_lot(
    session: Session,
    lot_id: int,
    principal: Optional[float] = None,
    note: Optional[str] = None,
) -> Lot:
    """更新批次"""
    lot = get_lot(session, lot_id)
    if not lot:
        raise ValueError(f"Lot {lot_id} not found")
    
    if principal is not None:
        if principal <= 0:
            raise ValueError("principal must be greater than 0")
        lot.principal = principal
    if note is not None:
        lot.note = note
    
    session.add(lot)
    session.commit()
    session.refresh(lot)
    return lot


def delete_lot(session: Session, lot_id: int) -> bool:
    """删除批次"""
    lot = get_lot(session, lot_id)
    if not lot:
        raise ValueError(f"Lot {lot_id} not found")
    
    session.delete(lot)
    session.commit()
    return True
