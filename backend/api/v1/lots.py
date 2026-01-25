from flask import jsonify, request
from datetime import date

from database import get_session
from models.lot import LotStatus
from services.lot_service import create_lot, list_lots_by_product, patch_lot, delete_lot
from utils.response import ok, err

from . import bp


@bp.route('/lots', methods=['POST'])
def post_lots():
    payload = request.get_json(silent=True) or {}

    product_id = payload.get('product_id')
    if not product_id:
        return jsonify(err('product_id is required', code=400)), 400

    open_date_str = payload.get('open_date')
    if not open_date_str:
        return jsonify(err('open_date is required', code=400)), 400

    try:
        open_date = date.fromisoformat(open_date_str)
    except ValueError:
        return jsonify(err('invalid open_date format', code=400)), 400

    principal = payload.get('principal')
    if principal is None:
        return jsonify(err('principal is required', code=400)), 400

    if principal <= 0:
        return jsonify(err('principal must be greater than 0', code=400)), 400

    note = payload.get('note')

    session = get_session()
    try:
        lot = create_lot(
            session,
            product_id=product_id,
            open_date=open_date,
            principal=principal,
            note=note,
        )
        return jsonify(ok(lot))
    finally:
        session.close()


@bp.route('/products/<int:product_id>/lots', methods=['GET'])
def get_product_lots(product_id: int):
    session = get_session()
    try:
        lots = list_lots_by_product(session, product_id)
        return jsonify(ok({
            "product_id": product_id,
            "items": lots
        }))
    finally:
        session.close()


@bp.route('/lots/<int:lot_id>', methods=['PATCH'])
def patch_lots(lot_id: int):
    payload = request.get_json(silent=True) or {}

    principal = payload.get('principal')
    if principal is not None and principal <= 0:
        return jsonify(err('principal must be greater than 0', code=400)), 400
    
    note = payload.get('note')

    session = get_session()
    try:
        try:
            updated = patch_lot(
                session,
                lot_id=lot_id,
                principal=principal,
                note=note,
            )
        except ValueError as e:
            return jsonify(err(str(e), code=404)), 404
        return jsonify(ok(updated))
    finally:
        session.close()


@bp.route('/lots/<int:lot_id>', methods=['DELETE'])
def delete_lots(lot_id: int):
    session = get_session()
    try:
        try:
            delete_lot(session, lot_id)
        except ValueError as e:
            return jsonify(err(str(e), code=404)), 404
        return jsonify(ok({'message': 'deleted'}))
    finally:
        session.close()
