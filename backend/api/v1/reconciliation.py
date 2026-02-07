from flask import jsonify, request
from datetime import date

from database import get_session
from utils.response import ok, err
from services.reconciliation_service import (
    get_all_warnings,
    check_account_diffs,
    check_redeem_consistency,
    check_valuation_gaps,
    update_warning_status,
    restore_warning_to_open
)

from . import bp


@bp.route('/reconciliation/warnings', methods=['GET'])
def get_reconciliation_warnings():
    """
    获取所有对账警告（聚合接口）
    
    Query Params:
        - date: 检查日期（ISO格式，默认今天）
        - account_threshold: 账户差异阈值（默认 1.0）
        - gap_days: 估值断档阈值天数（默认 14）
        - redeem_buffer: 赎回缓冲天数（默认 3）
    
    Returns:
        {
            "items": [
                {
                    "id": str,
                    "level": "warn" | "info",
                    "type": "account_diff" | "redeem_anomaly" | "valuation_gap",
                    "title": str,
                    "description": str,
                    "object_type": "account" | "product",
                    "object_id": int,
                    "object_name": str,
                    "date": str | null,
                    "diff_value": float | null,
                    "suggested_action": str,
                    "link_to": str
                }
            ],
            "summary": {
                "total": int,
                "warn": int,
                "info": int
            }
        }
    """
    # 解析参数
    date_str = request.args.get('date')
    target_date = date.today() if not date_str else date.fromisoformat(date_str)
    
    account_threshold = request.args.get('account_threshold', 1.0, type=float)
    gap_days = request.args.get('gap_days', 14, type=int)
    redeem_buffer = request.args.get('redeem_buffer', 3, type=int)
    
    session = get_session()
    try:
        warnings = get_all_warnings(
            session,
            target_date=target_date,
            account_diff_threshold=account_threshold,
            valuation_gap_days=gap_days,
            redeem_buffer_days=redeem_buffer
        )
        
        warn_count = sum(1 for w in warnings if w.level == 'warn')
        info_count = sum(1 for w in warnings if w.level == 'info')
        
        return jsonify(ok({
            "items": [w.to_dict() for w in warnings],
            "summary": {
                "total": len(warnings),
                "warn": warn_count,
                "info": info_count
            }
        }))
    finally:
        session.close()


@bp.route('/reconciliation/account_diffs', methods=['GET'])
def get_account_diffs():
    """
    获取账户对账差异（S6-2）
    
    Query Params:
        - date: 检查日期（ISO格式，默认今天）
        - threshold: 差异阈值（默认 1.0）
    
    Returns:
        {
            "items": [
                {
                    "account_id": int,
                    "account_name": str,
                    "check_date": str,
                    "snapshot_balance": float,
                    "derived_balance": float,
                    "diff": float,
                    "severity": "info" | "warn",
                    "hint": str
                }
            ]
        }
    """
    date_str = request.args.get('date')
    target_date = date.today() if not date_str else date.fromisoformat(date_str)
    threshold = request.args.get('threshold', 1.0, type=float)
    
    session = get_session()
    try:
        diffs = check_account_diffs(session, target_date, threshold)
        return jsonify(ok({
            "items": [d.to_dict() for d in diffs],
            "check_date": target_date.isoformat(),
            "threshold": threshold
        }))
    finally:
        session.close()


@bp.route('/reconciliation/redeem_check', methods=['GET'])
def get_redeem_check():
    """
    获取赎回在途一致性检查（S6-3）
    
    Query Params:
        - buffer_days: 缓冲天数（默认 3）
    
    Returns:
        {
            "items": [
                {
                    "product_id": int,
                    "product_name": str,
                    "pending_amount": float,
                    "status": "normal" | "negative" | "overdue",
                    "latest_request_date": str | null,
                    "expected_settle_date": str | null,
                    "days_pending": int | null,
                    "hint": str
                }
            ]
        }
    """
    buffer_days = request.args.get('buffer_days', 3, type=int)
    
    session = get_session()
    try:
        checks = check_redeem_consistency(session, buffer_days)
        return jsonify(ok({
            "items": [c.to_dict() for c in checks],
            "buffer_days": buffer_days
        }))
    finally:
        session.close()


@bp.route('/reconciliation/valuation_gaps', methods=['GET'])
def get_valuation_gaps():
    """
    获取估值断档产品列表（S6-4）
    
    Query Params:
        - gap_days: 断档阈值天数（默认 14）
    
    Returns:
        {
            "items": [
                {
                    "product_id": int,
                    "product_name": str,
                    "last_valuation_date": str | null,
                    "days_since": int,
                    "has_recent_trade": bool,
                    "severity": "info" | "warn",
                    "hint": str
                }
            ]
        }
    """
    gap_days = request.args.get('gap_days', 14, type=int)
    
    session = get_session()
    try:
        gaps = check_valuation_gaps(session, gap_days)
        return jsonify(ok({
            "items": [g.to_dict() for g in gaps],
            "gap_threshold_days": gap_days
        }))
    finally:
        session.close()


@bp.route('/reconciliation/warnings/<warning_id>/status', methods=['PUT'])
def update_warning_status_endpoint(warning_id: str):
    """
    更新警告状态（S6-5）
    
    Body Params:
        - status: 新状态 (open/acknowledged/muted)
        - mute_reason: 静音原因（当 status=muted 时可选）
    
    Returns:
        {
            "id": int,
            "warning_id": str,
            "status": str,
            "mute_reason": str | null,
            "updated_at": str
        }
    """
    data = request.get_json() or {}
    status = data.get('status')
    mute_reason = data.get('mute_reason')
    
    if not status:
        return jsonify(err('status is required', code=400)), 400
    
    if status not in ['open', 'acknowledged', 'muted']:
        return jsonify(err('invalid status, must be open/acknowledged/muted', code=400)), 400
    
    session = get_session()
    try:
        record = update_warning_status(session, warning_id, status, mute_reason)
        return jsonify(ok({
            "id": record.id,
            "warning_id": record.warning_id,
            "status": record.status,
            "mute_reason": record.mute_reason,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None
        }))
    finally:
        session.close()


@bp.route('/reconciliation/warnings/<warning_id>/restore', methods=['POST'])
def restore_warning_endpoint(warning_id: str):
    """
    将警告恢复为 open 状态（S6-5）
    
    Returns:
        {
            "id": int,
            "warning_id": str,
            "status": str,
            "updated_at": str
        }
    """
    session = get_session()
    try:
        record = restore_warning_to_open(session, warning_id)
        if not record:
            return jsonify(err('warning not found', code=404)), 404
        
        return jsonify(ok({
            "id": record.id,
            "warning_id": record.warning_id,
            "status": record.status,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None
        }))
    finally:
        session.close()
