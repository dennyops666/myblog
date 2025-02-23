"""
文件名：__init__.py
描述：模型模块初始化
作者：denny
创建日期：2024-03-21
"""

from app.extensions import db

# 导入所有模型
from .user import User
from .role import Role
from .category import Category
from .tag import Tag
from .post import Post
from .comment import Comment

__all__ = [
    'db',
    'User',
    'Role',
    'Category',
    'Tag',
    'Post',
    'Comment'
]
