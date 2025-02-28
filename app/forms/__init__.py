"""
文件名：__init__.py
描述：表单包初始化
作者：denny
创建日期：2024-03-21
"""

from flask_wtf import FlaskForm
from .auth import LoginForm, RegisterForm
from .admin import PostForm, CategoryForm, TagForm, ProfileForm
from .comment import CommentForm

# 导出所有表单类
__all__ = [
    'LoginForm',
    'RegisterForm',
    'PostForm',
    'CategoryForm',
    'TagForm',
    'ProfileForm',
    'CommentForm'
] 