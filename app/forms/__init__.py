"""
文件名：__init__.py
描述：表单包初始化
作者：denny
"""

from flask_wtf import FlaskForm

class BaseForm(FlaskForm):
    """基础表单类"""
    class Meta:
        csrf = False
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

from .auth import LoginForm, RegisterForm
from .admin.post import PostForm
from .comment import CommentForm
# 从tag_form模块导入TagForm
from .tag_form import TagForm
# 从tag模块导入TagCreateForm和TagEditForm
from .tag import TagCreateForm, TagEditForm

# 导出所有表单类
__all__ = [
    'BaseForm',
    'LoginForm',
    'RegisterForm',
    'PostForm',
    'CommentForm',
    'TagForm',
    'TagCreateForm',
    'TagEditForm'
] 