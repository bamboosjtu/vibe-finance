from flask import jsonify, request

from database import get_session
from services.institution_service import create_institution, list_institutions
from utils.response import ok, err

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
        return jsonify(err('name is required', code=400)), 400

    session = get_session()
    try:
        try:
            institution = create_institution(session, name=name)
        except ValueError as e:
            return jsonify(err(str(e), code=400)), 400
        return jsonify(ok(institution))
    finally:
        session.close()
