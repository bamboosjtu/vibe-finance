from flask import jsonify, request

from database import get_session
from models.product import ProductType, LiquidityRule
from services.product_service import create_product, list_products, patch_product
from utils.response import ok, err

from . import bp


@bp.route('/products', methods=['GET'])
def get_products():
    session = get_session()
    try:
        items = list_products(session)
        return jsonify(ok({"items": items}))
    finally:
        session.close()


@bp.route('/products', methods=['POST'])
def post_products():
    payload = request.get_json(silent=True) or {}

    name = payload.get('name')
    if not name:
        return jsonify(err('name is required', code=400)), 400

    product_type_raw = payload.get('product_type')
    if not product_type_raw:
        return jsonify(err('product_type is required', code=400)), 400

    liquidity_rule_raw = payload.get('liquidity_rule')
    if not liquidity_rule_raw:
        return jsonify(err('liquidity_rule is required', code=400)), 400

    try:
        product_type = ProductType(product_type_raw)
    except Exception:
        return jsonify(err('invalid product_type', code=400)), 400

    try:
        liquidity_rule = LiquidityRule(liquidity_rule_raw)
    except Exception:
        return jsonify(err('invalid liquidity_rule', code=400)), 400

    institution_id = payload.get('institution_id')
    product_code = payload.get('product_code')
    risk_level = payload.get('risk_level')
    term_days = payload.get('term_days')
    settle_days = payload.get('settle_days', 1)
    note = payload.get('note')

    session = get_session()
    try:
        product = create_product(
            session,
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
        return jsonify(ok(product))
    finally:
        session.close()


@bp.route('/products/<int:product_id>', methods=['PATCH'])
def patch_products(product_id: int):
    payload = request.get_json(silent=True) or {}

    product_type = None
    if 'product_type' in payload:
        try:
            product_type = ProductType(payload.get('product_type'))
        except Exception:
            return jsonify(err('invalid product_type', code=400)), 400

    liquidity_rule = None
    if 'liquidity_rule' in payload:
        try:
            liquidity_rule = LiquidityRule(payload.get('liquidity_rule'))
        except Exception:
            return jsonify(err('invalid liquidity_rule', code=400)), 400

    session = get_session()
    try:
        try:
            updated = patch_product(
                session,
                product_id=product_id,
                name=payload.get('name'),
                institution_id=payload.get('institution_id'),
                product_code=payload.get('product_code'),
                product_type=product_type,
                risk_level=payload.get('risk_level'),
                term_days=payload.get('term_days'),
                liquidity_rule=liquidity_rule,
                settle_days=payload.get('settle_days'),
                note=payload.get('note'),
            )
        except ValueError as e:
            return jsonify(err(str(e), code=404)), 404

        return jsonify(ok(updated))
    finally:
        session.close()
