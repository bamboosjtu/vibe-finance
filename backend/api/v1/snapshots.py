from flask import request, jsonify
from datetime import date
from database import get_session
from services import snapshot_service
from utils.response import ok, err
from . import bp


@bp.route('/snapshots/batch_upsert', methods=['POST'])
def batch_upsert():
    data = request.json
    if not data or 'rows' not in data:
        return jsonify(err("Missing 'rows' in request body", code=400)), 400
        
    rows = data['rows']
    # source = data.get('source', 'manual')
    
    session = get_session()
    try:
        inserted, updated, warnings = snapshot_service.batch_upsert_snapshots(session, rows)
        return jsonify(ok({
            "inserted": inserted,
            "updated": updated,
            "warnings": warnings
        }))
    finally:
        session.close()


@bp.route('/snapshots', methods=['GET'])
def list_snapshots_route():
    date_str = request.args.get('date')
    fill_previous = request.args.get('fill', 'false').lower() == 'true'
    
    if not date_str:
        return jsonify(err("Missing 'date' parameter", code=400)), 400
        
    try:
        query_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify(err("Invalid date format", code=400)), 400
        
    session = get_session()
    try:
        snapshots = snapshot_service.list_snapshots(session, query_date, fill_previous)
        items = [
            {
                "account_id": s.account_id,
                "balance": s.balance,
                "date": s.date.isoformat() # 返回实际的快照日期，以便前端知道数据来源
            }
            for s in snapshots
        ]
        return jsonify(ok({
            "date": date_str,
            "items": items
        }))
    finally:
        session.close()
