from typing import Any, Optional


def _serialize(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    if isinstance(value, tuple):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if hasattr(value, "model_dump"):
        return _serialize(value.model_dump())
    if hasattr(value, "dict"):
        return _serialize(value.dict())
    return value


def ok(data: Any = None, message: str = "ok", code: int = 200):
    return {
        "code": code,
        "data": _serialize(data),
        "message": message,
    }


def err(message: str, code: int = 400, data: Optional[Any] = None):
    return {
        "code": code,
        "data": _serialize(data),
        "message": message,
    }
