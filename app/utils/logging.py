"""
文件名：logging.py
描述：日志记录工具模块
作者：denny
创建日期：2024-03-09
"""
import logging
import traceback
from typing import Any, Dict, Optional
from flask import current_app, request, has_request_context
from flask_login import current_user

def get_log_context() -> Dict[str, Any]:
    """获取日志上下文信息"""
    context = {
        'Action': '-',
        'Data': '-',
        'Exception': None
    }
    
    if has_request_context():
        context.update({
            'Request': {
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.user_agent.string
            },
            'User': {
                'id': current_user.id if not current_user.is_anonymous else None,
                'username': current_user.username if not current_user.is_anonymous else None,
                'is_admin': current_user.is_admin if not current_user.is_anonymous else False
            }
        })
    
    return context

def log_info(
    message: str,
    extra: Optional[Dict[str, Any]] = None,
    exc_info: bool = False
) -> None:
    """记录信息级别日志
    
    Args:
        message: 日志消息
        extra: 额外信息
        exc_info: 是否包含异常信息
    """
    context = get_log_context()
    if extra:
        context.update(extra)
    current_app.logger.info(
        message,
        extra={'Context': context},
        exc_info=exc_info
    )

def log_warning(
    message: str,
    extra: Optional[Dict[str, Any]] = None,
    exc_info: bool = False
) -> None:
    """记录警告级别日志
    
    Args:
        message: 日志消息
        extra: 额外信息
        exc_info: 是否包含异常信息
    """
    context = get_log_context()
    if extra:
        context.update(extra)
    current_app.logger.warning(
        message,
        extra={'Context': context},
        exc_info=exc_info
    )

def log_error(
    message: str,
    extra: Optional[Dict[str, Any]] = None,
    exc_info: bool = True
) -> None:
    """记录错误级别日志
    
    Args:
        message: 日志消息
        extra: 额外信息
        exc_info: 是否包含异常信息，默认为 True
    """
    context = get_log_context()
    if extra:
        context.update(extra)
    
    # 添加堆栈跟踪
    if exc_info:
        context['Exception'] = traceback.format_exc()
    
    current_app.logger.error(
        message,
        extra={'Context': context},
        exc_info=exc_info
    )

def setup_logging():
    """设置日志记录
    
    此函数用于初始化应用程序的日志配置
    """
    # 这里是一个空的实现，因为Flask自己会处理基本的日志配置
    # 只是为了保持与导入兼容
    pass
