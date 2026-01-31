from flask import jsonify, request
from datetime import date
from typing import Optional

from database import get_session
from models.transaction import Transaction, TransactionCategory
from services.transaction_service import (
    create_transaction,
    list_transactions,
    delete_transaction,
    get_product_transactions
)
from utils.response import ok, err, err_safe, ErrorCode
from utils.logger import log_error

from . import bp


@bp.route('/transactions', methods=['POST'])
def create():
    """创建交易记录"""
    payload = request.get_json(silent=True) or {}

    # 必填字段校验
    required = ['product_id', 'account_id', 'category', 'trade_date', 'amount']
    for field in required:
        if field not in payload:
            return jsonify(err(f'{field} is required', code=400)), 400

    # 校验 category
    if payload['category'] not in [
        TransactionCategory.BUY,
        TransactionCategory.REDEEM_REQUEST,
        TransactionCategory.REDEEM_SETTLE,
        TransactionCategory.FEE
    ]:
        return jsonify(err('invalid category', code=400)), 400

    session = get_session()
    try:
        transaction = create_transaction(
            session,
            product_id=payload['product_id'],
            account_id=payload['account_id'],
            category=payload['category'],
            trade_date=payload['trade_date'],
            amount=payload['amount'],
            settle_date=payload.get('settle_date'),
            note=payload.get('note')
        )
        return jsonify(ok({
            "id": transaction.id,
            "product_id": transaction.product_id,
            "account_id": transaction.account_id,
            "category": transaction.category,
            "trade_date": transaction.trade_date.isoformat(),
            "settle_date": transaction.settle_date.isoformat() if transaction.settle_date else None,
            "amount": transaction.amount,
            "note": transaction.note
        }))
    except Exception as e:
        # 记录结构化错误日志，包含上下文信息
        log_error(
            "创建交易记录失败",
            error=e,
            extra={
                "endpoint": "POST /transactions",
                "payload": payload,
                "remote_addr": request.remote_addr
            }
        )
        # 返回安全的错误响应，不暴露内部细节
        return jsonify(err_safe(e, code=500)), 500
    finally:
        session.close()


@bp.route('/transactions', methods=['GET'])
def list_all():
    """查询交易记录列表"""
    product_id = request.args.get('product_id', type=int)
    account_id = request.args.get('account_id', type=int)
    category = request.args.get('category')
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    # 日期解析
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    if from_date:
        try:
            start_date = date.fromisoformat(from_date)
        except ValueError:
            return jsonify(err("invalid from date format", code=400)), 400
    if to_date:
        try:
            end_date = date.fromisoformat(to_date)
        except ValueError:
            return jsonify(err("invalid to date format", code=400)), 400

    session = get_session()
    try:
        result = list_transactions(
            session,
            product_id=product_id,
            account_id=account_id,
            category=category,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )

        items = [
            {
                "id": t.id,
                "product_id": t.product_id,
                "account_id": t.account_id,
                "category": t.category,
                "trade_date": t.trade_date.isoformat(),
                "settle_date": t.settle_date.isoformat() if t.settle_date else None,
                "amount": t.amount,
                "note": t.note
            }
            for t in result['items']
        ]

        return jsonify(ok({
            "items": items,
            "pagination": result['pagination']
        }))
    except Exception as e:
        log_error(
            "查询交易记录列表失败",
            error=e,
            extra={
                "endpoint": "GET /transactions",
                "params": {
                    "product_id": product_id,
                    "account_id": account_id,
                    "category": category,
                    "from": from_date,
                    "to": to_date,
                    "page": page,
                    "page_size": page_size
                }
            }
        )
        return jsonify(err_safe(e, code=500)), 500
    finally:
        session.close()


@bp.route('/transactions/<int:transaction_id>', methods=['DELETE'])
def delete(transaction_id: int):
    """删除交易记录"""
    session = get_session()
    try:
        success = delete_transaction(session, transaction_id)
        if success:
            return jsonify(ok({"message": "deleted"}))
        else:
            return jsonify(err("transaction not found", code=404)), 404
    except Exception as e:
        log_error(
            "删除交易记录失败",
            error=e,
            extra={
                "endpoint": f"DELETE /transactions/{transaction_id}",
                "transaction_id": transaction_id
            }
        )
        return jsonify(err_safe(e, code=500)), 500
    finally:
        session.close()


@bp.route('/products/<int:product_id>/transactions', methods=['GET'])
def get_product_transactions_api(product_id: int):
    """获取指定产品的交易记录"""
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    window = request.args.get('window', '8w')

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    # 如果提供了from/to，使用它们；否则根据window计算
    if from_date:
        try:
            start_date = date.fromisoformat(from_date)
        except ValueError:
            return jsonify(err("invalid from date format", code=400)), 400
    if to_date:
        try:
            end_date = date.fromisoformat(to_date)
        except ValueError:
            return jsonify(err("invalid to date format", code=400)), 400

    # 根据window参数计算日期范围（与chart接口保持一致）
    if not start_date or not end_date:
        from datetime import timedelta
        today = date.today()
        if not end_date:
            end_date = today
        if not start_date:
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
                start_date = today - timedelta(weeks=8)

    session = get_session()
    try:
        transactions = get_product_transactions(
            session,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date
        )

        items = [
            {
                "id": t.id,
                "account_id": t.account_id,
                "category": t.category,
                "trade_date": t.trade_date.isoformat(),
                "settle_date": t.settle_date.isoformat() if t.settle_date else None,
                "amount": t.amount,
                "note": t.note
            }
            for t in transactions
        ]

        return jsonify(ok({
            "product_id": product_id,
            "items": items
        }))
    except Exception as e:
        log_error(
            "获取产品交易记录失败",
            error=e,
            extra={
                "endpoint": f"GET /products/{product_id}/transactions",
                "product_id": product_id,
                "params": {"from": from_date, "to": to_date, "window": window}
            }
        )
        return jsonify(err_safe(e, code=500)), 500
    finally:
        session.close()
