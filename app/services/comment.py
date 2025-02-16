"""
文件名：comment.py
描述：评论服务类
作者：denny
创建日期：2025-02-16
"""

from sqlalchemy import desc
from app.models import Comment, db

class CommentService:
    @staticmethod
    def get_recent_comments(limit=5):
        """获取最新评论"""
        return Comment.query.filter_by(status=1).order_by(desc(Comment.created_at)).limit(limit).all()
    
    @staticmethod
    def get_comments_by_post(post_id):
        """获取文章评论"""
        return Comment.query.filter_by(post_id=post_id, status=1).order_by(Comment.created_at).all()
    
    @staticmethod
    def create_comment(post_id, nickname, email, content, parent_id=None):
        """创建评论"""
        comment = Comment(
            post_id=post_id,
            nickname=nickname,
            email=email,
            content=content,
            parent_id=parent_id,
            status=1
        )
        db.session.add(comment)
        db.session.commit()
        return comment 