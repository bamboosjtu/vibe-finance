from flask import jsonify, request
from sqlmodel import select

from database import get_session
from models.product import ProductType, LiquidityRule, ValuationMode
from models.transaction import Transaction
from services.product_service import create_product, list_products, list_products_with_holdings, patch_product, delete_product
from services.valuation_service import get_valuation_series
from services.analytics_service import calculate_metrics
from services.redeem_service import get_product_pending_redeem
from utils.response import ok, err, ErrorCode
from utils.logger import log_error
from datetime import date, timedelta

from . import bp


@bp.route('/products', methods=['GET'])
def get_products():
    """获取产品列表"""
    include_metrics = request.args.get('include_metrics') == 'true'
    
    session = get_session()
    try:
        items = list_products_with_holdings(session)
        result = []
        
        today = date.today()
        
        # 定义所有窗口
        windows = ['4w', '8w', '12w', '24w', '1y']
        
        for p in items:
            if include_metrics:
                # 为每个窗口计算指标
                p['metrics_by_window'] = {}
                for w in windows:
                    # 计算窗口开始日期
                    if w == '4w':
                        start_date = today - timedelta(weeks=4)
                    elif w == '8w':
                        start_date = today - timedelta(weeks=8)
                    elif w == '12w':
                        start_date = today - timedelta(weeks=12)
                    elif w == '24w':
                        start_date = today - timedelta(weeks=24)
                    elif w == '1y':
                        start_date = today - timedelta(days=365)
                    else:
                        start_date = today - timedelta(weeks=8)
                    
                    series = get_valuation_series(session, p['id'], start_date, today, interpolate=True)
                    metrics = None
                    if series and len(series) >= 14:
                        metrics = calculate_metrics(series)
                    p['metrics_by_window'][w] = metrics
                
                # 保留默认metrics（兼容旧代码）
                p['metrics'] = p['metrics_by_window'].get('8w')
            result.append(p)
            
        return jsonify(ok({"items": result}))
    finally:
        session.close()


@bp.route('/products', methods=['POST'])
def post_products():
    """创建产品"""
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
    valuation_mode_raw = payload.get('valuation_mode', 'product_value')

    try:
        valuation_mode = ValuationMode(valuation_mode_raw)
    except Exception:
        valuation_mode = ValuationMode.PRODUCT_VALUE

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
            valuation_mode=valuation_mode,
        )
        return jsonify(ok(product))
    finally:
        session.close()


@bp.route('/products/<int:product_id>', methods=['PATCH'])
def patch_products(product_id: int):
    """更新产品"""
    payload = request.get_json(silent=True) or {}

    product_type = None
    if 'product_type' in payload:
        try:
            product_type = ProductType(payload.get('product_type'))
        except Exception:
            return jsonify(err(error_code=ErrorCode.BAD_REQUEST)), 400

    liquidity_rule = None
    if 'liquidity_rule' in payload:
        try:
            liquidity_rule = LiquidityRule(payload.get('liquidity_rule'))
        except Exception:
            return jsonify(err(error_code=ErrorCode.BAD_REQUEST)), 400

    valuation_mode = None
    if 'valuation_mode' in payload:
        try:
            valuation_mode = ValuationMode(payload.get('valuation_mode'))
        except Exception:
            return jsonify(err(error_code=ErrorCode.BAD_REQUEST)), 400

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
                valuation_mode=valuation_mode,
            )
        except ValueError as e:
            log_error(
                "更新产品失败",
                error=e,
                extra={
                    "endpoint": f"PATCH /products/{product_id}",
                    "product_id": product_id,
                    "payload": payload
                }
            )
            return jsonify(err(error_code=ErrorCode.NOT_FOUND)), 404

        return jsonify(ok(updated))
    finally:
        session.close()


@bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_products(product_id: int):
    """删除产品"""
    session = get_session()
    try:
        try:
            delete_product(session, product_id)
        except ValueError as e:
            log_error(
                "删除产品失败",
                error=e,
                extra={
                    "endpoint": f"DELETE /products/{product_id}",
                    "product_id": product_id
                }
            )
            return jsonify(err(error_code=ErrorCode.NOT_FOUND)), 404
        return jsonify(ok({'message': 'deleted'}))
    finally:
        session.close()


@bp.route('/products/<int:product_id>/chart', methods=['GET'])
def get_product_chart(product_id: int):
    """
    获取产品市值走势
    返回 manual 和 interpolated 点
    """
    from models.product import Product
    
    window = request.args.get('window', '8w')
    
    today = date.today()
    start_date = today - timedelta(weeks=8)
    if window == '4w': start_date = today - timedelta(weeks=4)
    elif window == '12w': start_date = today - timedelta(weeks=12)
    elif window == '24w': start_date = today - timedelta(weeks=24)
    elif window == '1y': start_date = today - timedelta(days=365)
    elif window == 'ytd': start_date = date(today.year, 1, 1)
    
    session = get_session()
    try:
        product = session.get(Product, product_id)
        if not product:
            return jsonify(err("product not found", code=404)), 404
        
        # 获取估值序列（包含 source 标记）
        series = get_valuation_series(session, product_id, start_date, today, interpolate=True)
        
        # 转换为前端格式
        points = [
            {
                "date": p["date"].isoformat() if isinstance(p["date"], date) else p["date"],
                "market_value": p["value"],
                "source": p["source"]
            }
            for p in series
        ]
        
        return jsonify(ok({
            "product_id": product_id,
            "valuation_mode": product.valuation_mode.value,
            "points": points
        }))
    finally:
        session.close()


@bp.route('/products/<int:product_id>/metrics', methods=['GET'])
def get_product_metrics(product_id: int):
    """
    获取产品收益指标
    检测现金流事件，返回参考收益率或严格收益率
    """
    from models.product import Product
    
    window = request.args.get('window', '8w')
    
    today = date.today()
    start_date = today
    if window == '4w': start_date = today - timedelta(weeks=4)
    elif window == '8w': start_date = today - timedelta(weeks=8)
    elif window == '12w': start_date = today - timedelta(weeks=12)
    elif window == '24w': start_date = today - timedelta(weeks=24)
    elif window == '1y': start_date = today - timedelta(days=365)
    elif window == 'ytd': start_date = date(today.year, 1, 1)
    else:
        start_date = today - timedelta(weeks=8)
        
    session = get_session()
    try:
        product = session.get(Product, product_id)
        if not product:
            return jsonify(err("product not found", code=404)), 404
        
        # 获取估值序列
        series = get_valuation_series(session, product_id, start_date, today, interpolate=True)
        
        # 检查有效估值点（manual + interpolated）≥ 2 周
        if len(series) < 14:
            return jsonify(ok({
                "product_id": product_id,
                "valuation_mode": product.valuation_mode.value,
                "window": window,
                "status": "insufficient_data",
                "metrics": None,
                "reason": "估值点不足2周"
            }))
        
        # 检测窗口内是否有现金流事件（Transaction）
        transactions = session.exec(
            select(Transaction).where(
                Transaction.product_id == product_id,
                Transaction.trade_date >= start_date,
                Transaction.trade_date <= today
            )
        ).all()
        
        has_cashflow = len(transactions) > 0
        
        # 计算指标
        metrics = calculate_metrics(series)
        
        if not metrics:
            return jsonify(ok({
                "product_id": product_id,
                "valuation_mode": product.valuation_mode.value,
                "window": window,
                "status": "insufficient_data",
                "metrics": None
            }))
        
        # 如果有现金流事件，标记为参考值
        if has_cashflow:
            return jsonify(ok({
                "product_id": product_id,
                "valuation_mode": product.valuation_mode.value,
                "window": window,
                "status": "degraded",
                "metrics": metrics,
                "degraded_reason": "窗口期内发生资金流动，收益指标为参考值",
                "degraded_fields": ["twr", "annualized"]
            }))
            
        return jsonify(ok({
            "product_id": product_id,
            "valuation_mode": product.valuation_mode.value,
            "window": window,
            "status": "ok",
            "metrics": metrics
        }))
    finally:
        session.close()


@bp.route('/products/<int:product_id>/pending_redeem', methods=['GET'])
def get_product_pending_redeem_info(product_id: int):
    """
    获取单个产品的在途赎回信息（Sprint 4）
    
    Returns:
        {
            "product_id": int,
            "pending_amount": float,        # 在途金额
            "latest_request_date": str,     # 最近申请日
            "estimated_settle_date": str    # 预计到账日
        }
    """
    from models.product import Product
    
    session = get_session()
    try:
        product = session.get(Product, product_id)
        if not product:
            return jsonify(err("product not found", code=404)), 404
        
        result = get_product_pending_redeem(session, product_id)
        
        # 补充产品信息
        result["product_name"] = product.name
        result["settle_days"] = product.settle_days
        
        return jsonify(ok(result))
    finally:
        session.close()


@bp.route('/products/<int:product_id>/liquidity_status', methods=['GET'])
def get_product_liquidity_status(product_id: int):
    """
    获取产品流动性状态（Sprint 5）
    
    展示产品的时间维度流动性信息：
    - 是否处于锁定期
    - 锁定期结束日
    - 最近可变现日期
    
    Returns:
        {
            "product_id": int,
            "product_name": str,
            "is_locked": bool,              # 是否处于锁定期
            "lock_end_date": str | null,    # 锁定期结束日
            "next_liquid_date": str | null, # 最近可变现日期
            "liquidity_type": str,          # "open" | "closed" | "periodic_open"
            "term_days": int,
            "settle_days": int,
            "note": str                     # 提示说明
        }
    """
    from datetime import date, timedelta
    from models.product import Product
    from models.transaction import Transaction, TransactionCategory
    from sqlmodel import select
    
    session = get_session()
    try:
        product = session.get(Product, product_id)
        if not product:
            return jsonify(err("product not found", code=404)), 404
        
        today = date.today()
        
        # 确定流动性类型
        liquidity_type = product.liquidity_rule.value
        
        # 查询最近一笔买入
        latest_buy = session.exec(
            select(Transaction)
            .where(Transaction.product_id == product_id)
            .where(Transaction.category == TransactionCategory.BUY)
            .order_by(Transaction.trade_date.desc())
            .limit(1)
        ).first()
        
        is_locked = False
        lock_end_date = None
        next_liquid_date = None
        note = ""
        
        if product.liquidity_rule.value == 'open':
            # 开放式产品，随时可变现
            is_locked = False
            next_liquid_date = today.isoformat()
            note = "开放式产品，随时可赎回"
            
        elif product.liquidity_rule.value == 'closed':
            # 封闭式产品，基于最近买入 + term_days 计算锁定期
            if latest_buy and product.term_days:
                lock_end_date = latest_buy.trade_date + timedelta(days=product.term_days)
                is_locked = today < lock_end_date
                next_liquid_date = lock_end_date.isoformat()
                note = f"封闭式产品，预计 {lock_end_date.isoformat()} 后可变现"
            else:
                note = "封闭式产品，锁定期信息不完整"
                
        elif product.liquidity_rule.value == 'periodic_open':
            # 定期开放产品
            if latest_buy and product.term_days:
                lock_end_date = latest_buy.trade_date + timedelta(days=product.term_days)
                is_locked = today < lock_end_date
                next_liquid_date = lock_end_date.isoformat()
                note = f"定期开放产品，预计 {lock_end_date.isoformat()} 后进入开放期"
            else:
                note = "定期开放产品，开放期信息不完整"
        
        return jsonify(ok({
            "product_id": product_id,
            "product_name": product.name,
            "is_locked": is_locked,
            "lock_end_date": lock_end_date.isoformat() if lock_end_date else None,
            "next_liquid_date": next_liquid_date,
            "liquidity_type": liquidity_type,
            "term_days": product.term_days,
            "settle_days": product.settle_days,
            "note": note
        }))
    finally:
        session.close()
