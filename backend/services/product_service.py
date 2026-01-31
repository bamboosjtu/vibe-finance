from typing import List, Optional, Dict, Any

from sqlmodel import Session, select, delete, func, asc
from models.product import Product, ProductType, LiquidityRule, ValuationMode
from models.institution import Institution
from models.valuation import ProductValuation
from models.lot import Lot, LotStatus
from datetime import date as DateType


def create_product(
    session: Session,
    name: str,
    product_type: ProductType,
    liquidity_rule: LiquidityRule,
    institution_id: Optional[int] = None,
    product_code: Optional[str] = None,
    risk_level: Optional[str] = None,
    term_days: Optional[int] = None,
    settle_days: int = 1,
    note: Optional[str] = None,
) -> Product:
    product = Product(
        name=name,
        institution_id=institution_id,
        product_code=product_code,
        product_type=product_type,
        risk_level=risk_level,
        term_days=term_days,
        liquidity_rule=liquidity_rule,
        settle_days=settle_days,
        note=note,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def delete_product(session: Session, product_id: int) -> None:
    product = session.get(Product, product_id)
    if not product:
        raise ValueError("product not found")
    
    # 手动删除关联的估值记录
    statement = delete(ProductValuation).where(ProductValuation.product_id == product_id)
    session.exec(statement)
    
    session.delete(product)
    session.commit()



def list_products(session: Session) -> List[Product]:
    # 按机构名称排序，相同机构按期限排序
    statement = (
        select(Product)
        .order_by(Product.institution_id.asc(), Product.term_days.desc())
    )
    return list(session.exec(statement).all())

def calculate_product_holding_amounts(session: Session) -> Dict[int, float]:
    """
    计算每个产品的持有中批次金额总和
    """
    statement = (
        select(Lot.product_id, func.sum(Lot.principal))
        .where(Lot.status == LotStatus.HOLDING)
        .group_by(Lot.product_id)
    )
    results = session.exec(statement).all()
    return {product_id: amount or 0.0 for product_id, amount in results}


def get_latest_valuations(session: Session) -> Dict[int, float]:
    """
    获取每个产品的最新估值（manual点）
    """
    from models.valuation import ProductValuation
    
    # 子查询：获取每个产品的最新估值日期
    latest_dates = (
        select(
            ProductValuation.product_id,
            func.max(ProductValuation.date).label('max_date')
        )
        .group_by(ProductValuation.product_id)
        .subquery()
    )
    
    # 主查询：获取最新日期的估值
    statement = (
        select(ProductValuation.product_id, ProductValuation.market_value)
        .join(
            latest_dates,
            (ProductValuation.product_id == latest_dates.c.product_id) &
            (ProductValuation.date == latest_dates.c.max_date)
        )
    )
    results = session.exec(statement).all()
    return {product_id: market_value or 0.0 for product_id, market_value in results}


def list_products_with_holdings(session: Session) -> List[Dict[str, Any]]:
    """
    获取所有产品及其最新估值
    """
    products = list_products(session)
    latest_valuations = get_latest_valuations(session)
    
    result = []
    for product in products:
        product_dict = product.model_dump()
        product_dict['total_holding_amount'] = latest_valuations.get(product.id, None)
        result.append(product_dict)
    
    return result


def patch_product(
    session: Session,
    product_id: int,
    name: Optional[str] = None,
    institution_id: Optional[int] = None,
    product_code: Optional[str] = None,
    product_type: Optional[ProductType] = None,
    risk_level: Optional[str] = None,
    term_days: Optional[int] = None,
    liquidity_rule: Optional[LiquidityRule] = None,
    settle_days: Optional[int] = None,
    note: Optional[str] = None,
    valuation_mode: Optional[ValuationMode] = None,
) -> Product:
    product = session.get(Product, product_id)
    if not product:
        raise ValueError("product not found")

    if name is not None:
        product.name = name
    if institution_id is not None:
        product.institution_id = institution_id
    if product_code is not None:
        product.product_code = product_code
    if product_type is not None:
        product.product_type = product_type
    if risk_level is not None:
        product.risk_level = risk_level if risk_level != '' else None
    if term_days is not None:
        product.term_days = term_days
    if liquidity_rule is not None:
        product.liquidity_rule = liquidity_rule
    if settle_days is not None:
        product.settle_days = settle_days
    if note is not None:
        product.note = note
    if valuation_mode is not None:
        product.valuation_mode = valuation_mode

    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def close_lot(
    session: Session,
    lot_id: int,
    close_date: DateType,
    note: Optional[str] = None,
) -> Lot:
    """
    关闭/卖出批次
    """
    lot = session.get(Lot, lot_id)
    if not lot:
        raise ValueError("lot not found")
    
    if lot.status == LotStatus.CLOSED:
        raise ValueError("lot already closed")
    
    if close_date < lot.open_date:
        raise ValueError("close_date cannot be earlier than open_date")
    
    lot.status = LotStatus.CLOSED
    lot.close_date = close_date
    if note is not None:
        lot.note = note
    
    session.add(lot)
    session.commit()
    session.refresh(lot)
    return lot
