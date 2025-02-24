"""
文件名：__init__.py
描述：模型包初始化
作者：denny
创建日期：2024-03-21
"""

from app.extensions import db

# 导入所有模型
from .user import User
from .post import Post
from .category import Category
from .tag import Tag
from .comment import Comment
from .role import Role
from .session import UserSession
from .permission import Permission

__all__ = [
    'db',
    'User',
    'Post',
    'Category',
    'Tag',
    'Comment',
    'Role',
    'UserSession',
    'Permission'
]
