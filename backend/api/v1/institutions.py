from flask import jsonify, request

from database import get_session
from services.institution_service import create_institution, list_institutions
from utils.response import ok, err, ErrorCode
from utils.logger import log_error

from . import bp


@bp.route('/institutions', methods=['GET'])
def get_institutions():
    session = get_session()
    try:
        items = list_institutions(session)
        return jsonify(ok({"items": items}))
    finally:
        session.close()


@bp.route('/institutions', methods=['POST'])
def post_institutions():
    payload = request.get_json(silent=True) or {}
    name = payload.get('name')
    if not name:
        return jsonify(err(error_code=ErrorCode.BAD_REQUEST)), 400

    session = get_session()
    try:
        try:
            institution = create_institution(session, name=name)
        except ValueError as e:
            log_error(
                "创建机构失败",
                error=e,
                extra={
                    "endpoint": "POST /institutions",
                    "name": name
                }
            )
            return jsonify(err(error_code=ErrorCode.BAD_REQUEST)), 400
        return jsonify(ok(institution))
    finally:
        session.close()
