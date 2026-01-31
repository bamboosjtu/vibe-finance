"""
结构化日志模块
提供统一的日志记录方式，支持结构化输出
"""

import logging
import sys
import traceback
from typing import Any, Dict, Optional
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 添加额外字段
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        # 异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # 简单格式化为 JSON-like 字符串
        parts = [f"{k}={v!r}" for k, v in log_data.items()]
        return " | ".join(parts)


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """设置并获取日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加处理器
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# 应用主日志记录器
app_logger = setup_logger("app")


def log_error(
    message: str,
    error: Optional[Exception] = None,
    extra: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> None:
    """
    记录错误日志

    Args:
        message: 错误描述
        error: 异常对象
        extra: 额外上下文数据
        request_id: 请求ID（用于追踪）
    """
    extra_attrs = {"extra_data": extra or {}}
    if request_id:
        extra_attrs["request_id"] = request_id

    if error:
        app_logger.error(
            message,
            exc_info=error,
            extra=extra_attrs
        )
    else:
        app_logger.error(message, extra=extra_attrs)


def log_warning(
    message: str,
    extra: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> None:
    """记录警告日志"""
    extra_attrs = {"extra_data": extra or {}}
    if request_id:
        extra_attrs["request_id"] = request_id
    app_logger.warning(message, extra=extra_attrs)


def log_info(
    message: str,
    extra: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> None:
    """记录信息日志"""
    extra_attrs = {"extra_data": extra or {}}
    if request_id:
        extra_attrs["request_id"] = request_id
    app_logger.info(message, extra=extra_attrs)


def log_debug(
    message: str,
    extra: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> None:
    """记录调试日志"""
    extra_attrs = {"extra_data": extra or {}}
    if request_id:
        extra_attrs["request_id"] = request_id
    app_logger.debug(message, extra=extra_attrs)
