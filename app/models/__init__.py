"""
文件名：__init__.py
描述：数据模型包初始化
作者：denny
创建日期：2025-02-16
"""

from app.extensions import db
from .user import User
from .post import Post
from .category import Category
from .tag import Tag
from .comment import Comment

__all__ = ['db', 'User', 'Post', 'Category', 'Tag', 'Comment']
