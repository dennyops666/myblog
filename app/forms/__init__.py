"""
文件名：__init__.py
描述：表单模块初始化
作者：denny
创建日期：2025-02-16
"""

from .auth import LoginForm, RegisterForm
from .comment import CommentForm

__all__ = ['LoginForm', 'RegisterForm', 'CommentForm'] 