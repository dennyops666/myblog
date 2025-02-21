"""
文件名：__init__.py
描述：模型初始化
作者：denny
创建日期：2024-03-21
"""

from app.extensions import db
from app.models.user import User
from app.models.role import Role
from app.models.post import Post
from app.models.comment import Comment
from app.models.category import Category
from app.models.tag import Tag

__all__ = [
    'db',
    'User',
    'Role',
    'Post',
    'Comment',
    'Category',
    'Tag'
]
