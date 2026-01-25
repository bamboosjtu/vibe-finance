from flask import jsonify, request
from datetime import date

from database import get_session
from services.snapshot_service import list_snapshots
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
    """获取指定日期的资产汇总"""
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
        
        # 可用现金 = 流动资产 - 负债
        available_cash = liquid_assets + liabilities
        
        return jsonify(ok({
            "date": target_date.isoformat(),
            "total_assets": total_assets,
            "liquid_assets": liquid_assets,
            "liabilities": liabilities,
            "available_cash": available_cash,
            "by_type": by_type
        }))
    finally:
        session.close()
