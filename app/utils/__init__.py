"""
文件名：__init__.py
描述：工具包初始化
作者：denny
"""

from .markdown import markdown_to_html
from .logging import log_error, log_info, log_warning
from .validation import validate_email, validate_username, validate_password
from datetime import datetime, UTC

__all__ = [
    'markdown_to_html',
    'log_error',
    'log_info',
    'log_warning',
    'validate_email',
    'validate_username',
    'validate_password',
]

def get_current_date():
    """获取当前日期，格式为YYYY-MM
    
    Returns:
        str: 当前日期，格式为YYYY-MM
    """
    now = datetime.now(UTC)
    return now.strftime('%Y-%m')

"""
工具函数包
""" 