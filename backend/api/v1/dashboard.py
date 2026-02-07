from flask import jsonify, request
from datetime import date

from database import get_session
from services.snapshot_service import list_snapshots
from services.cash_service import get_cash_summary, calculate_available_cash, calculate_cash_timeline
from services.redeem_service import calculate_pending_redeems, summarize_future_cash_flow
from models.snapshot import Snapshot
from sqlmodel import select
from utils.response import ok, err

from . import bp


@bp.route('/dashboard/available_dates', methods=['GET'])
def get_available_dates():
    """获取所有有快照的日期列表"""
    session = get_session()
    try:
        statement = select(Snapshot.date).distinct().order_by(Snapshot.date.desc())
        result = session.exec(statement).all()
        dates = [date_obj.isoformat() for date_obj in result]
        return jsonify(ok({
            "dates": dates
            }))
    finally:
        session.close()


@bp.route('/dashboard/latest_date', methods=['GET'])
def get_latest_snapshot_date():
    """获取最近有 Snapshot 的日期"""
    session = get_session()
    try:
        # 查找最新的快照日期
        statement = select(Snapshot.date).order_by(Snapshot.date.desc()).limit(1)
        result = session.exec(statement).first()
        
        if result:
            return jsonify(ok({
                "date": result.isoformat()
            }))
        else:
            return jsonify(ok({
                "date": None
            }))
    finally:
        session.close()


@bp.route('/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    """获取指定日期的资产汇总（Sprint 4 增强版）"""
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify(err('date is required', code=400)), 400
    
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify(err('invalid date format', code=400)), 400
    
    session = get_session()
    try:
        snapshots = list_snapshots(session, target_date)
        
        # 计算汇总指标
        total_assets = 0.0
        liquid_assets = 0.0
        liabilities = 0.0
        
        by_type = {
            'cash': 0.0,
            'debit': 0.0,
            'credit': 0.0,
            'investment_cash': 0.0,
            'other': 0.0,
        }
        
        for snapshot in snapshots:
            balance = snapshot.balance if snapshot.balance is not None else 0.0
            
            # 总资产
            total_assets += balance
            
            # 按类型分组
            account_type = snapshot.account.type if snapshot.account else 'other'
            if account_type in by_type:
                by_type[account_type] += balance
            
            # 流动资产
            if snapshot.account and snapshot.account.is_liquid:
                liquid_assets += balance
            
            # 负债（信用卡）
            if snapshot.account and snapshot.account.type == 'credit':
                liabilities += balance
        
        # 基础可用现金 = 流动资产 - 负债
        base_available_cash = liquid_assets + liabilities
        
        # Sprint 4: 计算实际可用现金（扣除在途赎回）
        cash_summary = get_cash_summary(session, target_date)
        
        return jsonify(ok({
            "date": target_date.isoformat(),
            "total_assets": total_assets,
            "liquid_assets": liquid_assets,
            "liabilities": liabilities,
            "available_cash": base_available_cash,           # 基础可用现金（兼容旧版）
            "real_available_cash": cash_summary["real_available"],  # 实际可用现金（扣除在途）
            "pending_redeems": cash_summary["pending_redeems"],     # 在途赎回金额
            "future_7d": cash_summary["future_7d"],                 # 未来7天预计到账
            "future_30d": cash_summary["future_30d"],               # 未来30天预计到账
            "future_90d": cash_summary["future_90d"],               # 未来90天预计到账（Sprint 5）
            "by_type": by_type
        }))
    finally:
        session.close()


@bp.route('/dashboard/pending_redeems', methods=['GET'])
def get_pending_redeems():
    """
    获取在途赎回资金明细
    
    Query Params:
        product_id: 可选，指定产品ID
    """
    product_id = request.args.get('product_id', type=int)
    
    session = get_session()
    try:
        result = calculate_pending_redeems(session, product_id)
        return jsonify(ok(result))
    finally:
        session.close()


@bp.route('/dashboard/future_cash_flow', methods=['GET'])
def get_future_cash_flow():
    """
    获取未来现金流预测
    
    Query Params:
        days: 预测天数，默认30天
    """
    days = request.args.get('days', default=30, type=int)
    
    session = get_session()
    try:
        result = summarize_future_cash_flow(session, days_7=7, days_30=days)
        return jsonify(ok(result))
    finally:
        session.close()


@bp.route('/dashboard/cash_detail', methods=['GET'])
def get_cash_detail():
    """
    获取现金详情（包含账户明细和在途明细）
    
    Query Params:
        date: 目标日期，默认为最新快照日期
    """
    date_str = request.args.get('date')
    target_date = None
    
    if date_str:
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            return jsonify(err('invalid date format', code=400)), 400
    
    session = get_session()
    try:
        result = calculate_available_cash(session, target_date)
        return jsonify(ok(result))
    finally:
        session.close()


@bp.route('/dashboard/cash_timeline', methods=['GET'])
def get_cash_timeline():
    """
    获取资金时间轴视图（Sprint 5）
    
    展示从当前时间点开始的资金流动性变化：
    - 当前：可用现金、在途赎回、锁定资金
    - 未来里程碑：+7d、+30d、+90d 的预计可用现金
    
    Query Params:
        milestones: 里程碑天数，逗号分隔，默认 "7,30,90"
        
    Response:
        {
            "current": {
                "date": "2024-01-15",
                "available_cash": 50000,
                "pending_redeems": 30000,
                "locked_in_products": 200000
            },
            "milestones": [
                {
                    "date": "2024-01-22",
                    "label": "+7天",
                    "days_from_now": 7,
                    "projected_available_cash": 65000,
                    "accumulated_inflow": 15000,
                    "changes": [...]
                }
            ]
        }
    """
    milestones_str = request.args.get('milestones', '7,30,90')
    
    try:
        milestones = [int(x.strip()) for x in milestones_str.split(',')]
    except ValueError:
        return jsonify(err('invalid milestones format, expected comma-separated integers', code=400)), 400
    
    session = get_session()
    try:
        result = calculate_cash_timeline(session, milestones)
        return jsonify(ok(result))
    finally:
        session.close()
