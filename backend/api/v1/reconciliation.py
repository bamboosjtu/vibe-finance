from flask import jsonify, request
from datetime import date

from database import get_session
from utils.response import ok, err

from . import bp


@bp.route('/reconciliation/warnings', methods=['GET'])
def get_reconciliation_warnings():
    """获取对账警告（Snapshot vs Transaction）
    
    当前阶段返回空数据，提示交易流水尚未启用。
    对账功能将在 Sprint 6 开始实现。
    """
    date_str = request.args.get('date')
    
    if date_str:
        try:
            date.fromisoformat(date_str)
        except ValueError:
            return jsonify(err('invalid date format', code=400)), 400
    
    session = get_session()
    try:
        return jsonify(ok({
            "items": [],
            "note": "交易流水尚未启用，对账将在 Sprint 6 开始"
        }))
    finally:
        session.close()
