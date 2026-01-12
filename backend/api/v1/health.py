from flask import jsonify
from . import bp


@bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "code": 200,
        "data": {"status": "healthy"},
        "message": "Backend is running"
    })
