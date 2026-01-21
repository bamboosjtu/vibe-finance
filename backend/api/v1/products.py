from flask import jsonify, request

from database import get_session
from models.product import ProductType, LiquidityRule
from services.product_service import create_product, list_products, patch_product, delete_product
from services.valuation_service import get_valuation_series
from services.analytics_service import calculate_metrics
from utils.response import ok, err
from datetime import date, timedelta

from . import bp


@bp.route('/products', methods=['GET'])
def get_products():
    include_metrics = request.args.get('include_metrics') == 'true'
    window = request.args.get('window', '8w')
    
    session = get_session()
    try:
        items = list_products(session)
        result = []
        
        # Prepare date range for metrics if needed
        today = date.today()
        start_date = today - timedelta(weeks=8) # Default 8w
        if window == '4w': start_date = today - timedelta(weeks=4)
        elif window == '12w': start_date = today - timedelta(weeks=12)
        elif window == '24w': start_date = today - timedelta(weeks=24)
        elif window == '1y': start_date = today - timedelta(days=365)
        elif window == 'ytd': start_date = date(today.year, 1, 1)

        for p in items:
            p_dict = p.model_dump()
            if include_metrics:
                # Calculate metrics
                series = get_valuation_series(session, p.id, start_date, today, interpolate=True)
                metrics = None
                if series and len(series) >= 14:
                    metrics = calculate_metrics(series)
                p_dict['metrics'] = metrics
            result.append(p_dict)
            
        return jsonify(ok({"items": result}))
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


@bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_products(product_id: int):
    session = get_session()
    try:
        try:
            delete_product(session, product_id)
        except ValueError as e:
            return jsonify(err(str(e), code=404)), 404
        return jsonify(ok({'message': 'deleted'}))
    finally:
        session.close()


@bp.route('/products/<int:product_id>/metrics', methods=['GET'])
def get_product_metrics(product_id: int):
    window = request.args.get('window', '8w')
    
    # 解析窗口
    today = date.today()
    start_date = today
    
    if window == '4w':
        start_date = today - timedelta(weeks=4)
    elif window == '8w':
        start_date = today - timedelta(weeks=8)
    elif window == '12w':
        start_date = today - timedelta(weeks=12)
    elif window == '24w':
        start_date = today - timedelta(weeks=24)
    elif window == '1y':
        start_date = today - timedelta(days=365)
    elif window == 'ytd':
        start_date = date(today.year, 1, 1)
    else:
        # 默认 8w
        start_date = today - timedelta(weeks=8)
        
    session = get_session()
    try:
        # 获取插值后的序列
        series = get_valuation_series(session, product_id, start_date, today, interpolate=True)
        
        # 检查数据是否足够 (至少2周数据)
        if not series or len(series) < 14:
             return jsonify(ok({
                "product_id": product_id,
                "window": window,
                "status": "insufficient_data",
                "metrics": None
            }))
            
        metrics = calculate_metrics(series)
        
        if not metrics:
             return jsonify(ok({
                "product_id": product_id,
                "window": window,
                "status": "insufficient_data",
                "metrics": None
            }))
            
        return jsonify(ok({
            "product_id": product_id,
            "window": window,
            "status": "ok",
            "metrics": metrics
        }))
    finally:
        session.close()
