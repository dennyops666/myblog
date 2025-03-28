"""
文件名：__init__.py
描述：模型包初始化
作者：denny
"""

from app.extensions import db

# 导入所有模型
from .user import User
from .post import Post, PostStatus
from .category import Category
from .tag import Tag
from .comment import Comment
from .role import Role
from .permission import Permission
from .operation_log import OperationLog

__all__ = [
    'db',
    'User',
    'Post',
    'PostStatus',
    'Category',
    'Tag',
    'Comment',
    'Role',
    'Permission',
    'OperationLog'
]
