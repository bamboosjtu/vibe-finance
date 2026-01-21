from typing import List, Optional

from sqlmodel import Session, select, delete
from models.product import Product, ProductType, LiquidityRule
from models.valuation import ProductValuation


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
    statement = select(Product).order_by(Product.id)
    return list(session.exec(statement).all())


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
        product.risk_level = risk_level
    if term_days is not None:
        product.term_days = term_days
    if liquidity_rule is not None:
        product.liquidity_rule = liquidity_rule
    if settle_days is not None:
        product.settle_days = settle_days
    if note is not None:
        product.note = note

    session.add(product)
    session.commit()
    session.refresh(product)
    return product
