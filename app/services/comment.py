"""
文件名：comment.py
描述：评论服务类
作者：denny
创建日期：2024-03-21
"""

from sqlalchemy import desc
from app.models import Comment, Post, User, db
from app.utils.markdown import markdown_to_html

class CommentService:
    @staticmethod
    def create_comment(content, post_id, author_id, parent_id=None):
        """创建评论
        
        参数：
            content (str): 评论内容
            post_id (int): 文章ID
            author_id (int): 作者ID
            parent_id (int, optional): 父评论ID
        
        返回：
            Comment: 创建的评论对象
        
        异常：
            ValueError: 当参数无效时抛出
        """
        # 验证参数
        if not content:
            raise ValueError('评论内容不能为空')
        
        # 验证文章是否存在
        post = db.session.get(Post, post_id)
        if not post:
            raise ValueError('文章不存在')
        
        # 验证用户是否存在
        user = db.session.get(User, author_id)
        if not user:
            raise ValueError('用户不存在')
        
        # 如果有父评论，验证其是否存在
        if parent_id:
            parent_comment = db.session.get(Comment, parent_id)
            if not parent_comment:
                raise ValueError('父评论不存在')
            if parent_comment.post_id != post_id:
                raise ValueError('父评论不属于该文章')
        
        # 创建评论
        comment = Comment(
            content=content,
            post_id=post_id,
            author_id=author_id,
            parent_id=parent_id,
            status=0  # 默认待审核
        )
        
        try:
            db.session.add(comment)
            db.session.commit()
            return comment
        except Exception as e:
            db.session.rollback()
            raise ValueError(f'创建评论失败：{str(e)}')
    
    @staticmethod
    def get_comments_by_post(post_id, include_pending=False):
        """获取文章的评论列表
        
        参数：
            post_id (int): 文章ID
            include_pending (bool): 是否包含待审核评论
        
        返回：
            list: 评论列表
        """
        query = Comment.query.filter_by(post_id=post_id)
        if not include_pending:
            query = query.filter_by(status=1)
        return query.order_by(Comment.created_at.desc()).all()
    
    @staticmethod
    def get_recent_comments(limit=5, include_pending=False):
        """获取最新评论
        
        参数：
            limit (int): 返回的评论数量
            include_pending (bool): 是否包含待审核评论
        
        返回：
            list: 评论列表
        """
        query = Comment.query
        if not include_pending:
            query = query.filter_by(status=1)
        return query.order_by(Comment.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def approve_comment(comment_id):
        """审核通过评论
        
        参数：
            comment_id (int): 评论ID
        
        返回：
            Comment: 更新后的评论对象
        
        异常：
            ValueError: 当评论不存在时抛出
        """
        comment = db.session.get(Comment, comment_id)
        if not comment:
            raise ValueError('评论不存在')
        
        comment.status = 1
        try:
            db.session.commit()
            return comment
        except Exception as e:
            db.session.rollback()
            raise ValueError(f'审核评论失败：{str(e)}')
    
    @staticmethod
    def reject_comment(comment_id):
        """拒绝评论（删除）
        
        参数：
            comment_id (int): 评论ID
        
        异常：
            ValueError: 当评论不存在时抛出
        """
        comment = db.session.get(Comment, comment_id)
        if not comment:
            raise ValueError('评论不存在')
        
        try:
            db.session.delete(comment)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f'删除评论失败：{str(e)}') 