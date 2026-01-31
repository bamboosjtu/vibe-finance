from typing import Any, Optional
from enum import Enum


class ErrorCode(Enum):
    """统一错误码枚举"""
    # 成功
    SUCCESS = 200

    # 客户端错误 (4xx)
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429

    # 服务端错误 (5xx)
    INTERNAL_ERROR = 500
    NOT_IMPLEMENTED = 501
    SERVICE_UNAVAILABLE = 503


# 错误码对应的对外消息（用户友好的描述，不包含敏感信息）
ERROR_MESSAGES = {
    ErrorCode.SUCCESS: "操作成功",
    ErrorCode.BAD_REQUEST: "请求参数错误",
    ErrorCode.UNAUTHORIZED: "未授权访问",
    ErrorCode.FORBIDDEN: "访问被拒绝",
    ErrorCode.NOT_FOUND: "请求的资源不存在",
    ErrorCode.METHOD_NOT_ALLOWED: "请求方法不允许",
    ErrorCode.CONFLICT: "资源冲突",
    ErrorCode.UNPROCESSABLE_ENTITY: "请求数据无法处理",
    ErrorCode.TOO_MANY_REQUESTS: "请求过于频繁",
    ErrorCode.INTERNAL_ERROR: "服务器内部错误",
    ErrorCode.NOT_IMPLEMENTED: "功能尚未实现",
    ErrorCode.SERVICE_UNAVAILABLE: "服务暂时不可用",
}


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
    """成功响应"""
    return {
        "code": code,
        "data": _serialize(data),
        "message": message,
    }


def err(
    message: Optional[str] = None,
    code: int = 400,
    data: Optional[Any] = None,
    error_code: Optional[ErrorCode] = None
):
    """
    错误响应

    Args:
        message: 对外展示的错误消息（如果不提供，使用默认消息）
        code: HTTP 状态码
        data: 额外数据
        error_code: 错误码枚举（用于获取默认消息）
    """
    # 优先使用传入的消息，否则根据 error_code 获取默认消息
    if message:
        public_message = message
    elif error_code and error_code in ERROR_MESSAGES:
        public_message = ERROR_MESSAGES[error_code]
    else:
        # 根据 HTTP 状态码获取默认消息
        default_code = ErrorCode.INTERNAL_ERROR if code >= 500 else ErrorCode.BAD_REQUEST
        public_message = ERROR_MESSAGES.get(default_code, "操作失败")

    return {
        "code": code,
        "data": _serialize(data),
        "message": public_message,
    }


def err_safe(
    error: Exception,
    code: int = 500,
    public_message: Optional[str] = None,
    error_code: Optional[ErrorCode] = None
):
    """
    安全的错误响应（不暴露内部错误细节）

    用于捕获异常时返回给客户端，内部错误细节不会暴露给用户，
    但可以通过日志记录详细错误信息。

    Args:
        error: 捕获的异常对象
        code: HTTP 状态码
        public_message: 对外展示的错误消息（如果不提供，使用默认消息）
        error_code: 错误码枚举
    """
    # 对外消息：绝不暴露异常详情
    if public_message:
        message = public_message
    elif error_code and error_code in ERROR_MESSAGES:
        message = ERROR_MESSAGES[error_code]
    elif code >= 500:
        message = ERROR_MESSAGES[ErrorCode.INTERNAL_ERROR]
    else:
        message = ERROR_MESSAGES[ErrorCode.BAD_REQUEST]

    return {
        "code": code,
        "data": None,
        "message": message,
    }
