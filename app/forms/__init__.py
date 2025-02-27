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

class BaseForm(FlaskForm):
    """基础表单类，禁用 CSRF 保护"""
    class Meta:
        csrf = False

# 修改所有表单类的父类为 BaseForm
LoginForm.__bases__ = (BaseForm,)
RegisterForm.__bases__ = (BaseForm,)
PostForm.__bases__ = (BaseForm,)
CategoryForm.__bases__ = (BaseForm,)
TagForm.__bases__ = (BaseForm,)
ProfileForm.__bases__ = (BaseForm,)
CommentForm.__bases__ = (BaseForm,)

__all__ = [
    'LoginForm',
    'RegisterForm',
    'PostForm',
    'CategoryForm',
    'TagForm',
    'ProfileForm',
    'CommentForm'
] 