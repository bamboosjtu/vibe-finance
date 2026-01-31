from flask import jsonify, request
from datetime import date

from database import get_session
from services.valuation_service import batch_upsert_valuations, list_valuations, delete_valuation
from utils.response import ok, err, err_safe, ErrorCode
from utils.logger import log_error

from . import bp


@bp.route('/valuations/batch_upsert', methods=['POST'], endpoint='batch_upsert_valuations')
def batch_upsert():
    """批量录入/更新产品估值点"""
    payload = request.get_json(silent=True) or {}
    rows = payload.get('rows', [])
    source = payload.get('source', 'manual')

    if not rows:
        return jsonify(ok({"inserted": 0, "updated": 0, "warnings": []}))

    session = get_session()
    try:
        result = batch_upsert_valuations(session, rows)
        return jsonify(ok(result))
    except Exception as e:
        log_error(
            "批量录入估值点失败",
            error=e,
            extra={
                "endpoint": "POST /valuations/batch_upsert",
                "rows_count": len(rows),
                "source": source
            }
        )
        return jsonify(err_safe(e, code=500)), 500
    finally:
        session.close()


@bp.route('/products/<int:product_id>/valuations', methods=['GET'])
def get_product_valuations(product_id: int):
    """获取产品估值点列表"""
    start_date_str = request.args.get('from')
    end_date_str = request.args.get('to')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    if not start_date_str or not end_date_str:
        return jsonify(err("from and to dates are required", code=400)), 400

    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except ValueError:
        return jsonify(err("invalid date format", code=400)), 400

    session = get_session()
    try:
        valuations = list_valuations(session, product_id, start_date, end_date)

        # 分页逻辑
        total = len(valuations)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_valuations = valuations[start_idx:end_idx]

        points = [
            {"date": v.date.isoformat(), "market_value": v.market_value}
            for v in paginated_valuations
        ]
        return jsonify(ok({
            "product_id": product_id,
            "points": points,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }))
    except Exception as e:
        log_error(
            "获取产品估值点列表失败",
            error=e,
            extra={
                "endpoint": f"GET /products/{product_id}/valuations",
                "product_id": product_id,
                "params": {"from": start_date_str, "to": end_date_str, "page": page, "page_size": page_size}
            }
        )
        return jsonify(err_safe(e, code=500)), 500
    finally:
        session.close()


@bp.route('/products/<int:product_id>/valuations', methods=['DELETE'])
def delete_product_valuation(product_id: int):
    """删除产品估值点"""
    date_str = request.args.get('date')
    if not date_str:
        return jsonify(err("date is required", code=400)), 400

    try:
        valuation_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify(err("invalid date format", code=400)), 400

    session = get_session()
    try:
        success = delete_valuation(session, product_id, valuation_date)
        if success:
            return jsonify(ok({"message": "deleted"}))
        else:
            return jsonify(err("valuation not found", code=404)), 404
    except Exception as e:
        log_error(
            "删除产品估值点失败",
            error=e,
            extra={
                "endpoint": f"DELETE /products/{product_id}/valuations",
                "product_id": product_id,
                "date": date_str
            }
        )
        return jsonify(err_safe(e, code=500)), 500
    finally:
        session.close()
