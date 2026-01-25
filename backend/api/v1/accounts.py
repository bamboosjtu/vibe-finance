from flask import jsonify, request

from database import get_session
from models.account import AccountType
from services.account_service import create_account, list_accounts, patch_account, delete_account
from utils.response import ok, err

from . import bp


@bp.route('/accounts', methods=['GET'])
def get_accounts():
    session = get_session()
    try:
        items = list_accounts(session)
        return jsonify(ok({"items": items}))
    finally:
        session.close()


@bp.route('/accounts', methods=['POST'])
def post_accounts():
    payload = request.get_json(silent=True) or {}

    name = payload.get('name')
    if not name:
        return jsonify(err('name is required', code=400)), 400

    type_raw = payload.get('type')
    if not type_raw:
        return jsonify(err('type is required', code=400)), 400

    try:
        account_type = AccountType(type_raw)
    except Exception:
        return jsonify(err('invalid account type', code=400)), 400

    institution_id = payload.get('institution_id')
    is_liquid = payload.get('is_liquid')
    currency = payload.get('currency') or 'CNY'

    session = get_session()
    try:
        account = create_account(
            session,
            name=name,
            account_type=account_type,
            institution_id=institution_id,
            is_liquid=is_liquid,
            currency=currency,
        )
        return jsonify(ok(account))
    finally:
        session.close()


@bp.route('/accounts/<int:account_id>', methods=['PATCH'])
def patch_accounts(account_id: int):
    payload = request.get_json(silent=True) or {}

    name = payload.get('name')
    institution_id = payload.get('institution_id')
    is_liquid = payload.get('is_liquid')
    currency = payload.get('currency')

    account_type = None
    if 'type' in payload:
        try:
            account_type = AccountType(payload.get('type'))
        except Exception:
            return jsonify(err('invalid account type', code=400)), 400

    session = get_session()
    try:
        try:
            updated = patch_account(
                session,
                account_id=account_id,
                name=name,
                institution_id=institution_id,
                account_type=account_type,
                is_liquid=is_liquid,
                currency=currency,
            )
        except ValueError as e:
            return jsonify(err(str(e), code=404)), 404
        return jsonify(ok(updated))
    finally:
        session.close()


@bp.route('/accounts/<int:account_id>', methods=['DELETE'])
def delete_accounts(account_id: int):
    session = get_session()
    try:
        try:
            delete_account(session, account_id)
        except ValueError as e:
            return jsonify(err(str(e), code=404)), 404
        return jsonify(ok({'message': 'deleted'}))
    finally:
        session.close()
