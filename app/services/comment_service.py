"""
文件名：comment_service.py
描述：评论服务类
作者：denny
创建日期：2024-03-21
"""

from app.models import Comment, Post, User
from app.extensions import db
from sqlalchemy.exc import IntegrityError
from app.utils.markdown import markdown_to_html

class CommentService:
    @staticmethod
    def create_comment(content, post_id, author_id, parent_id=None, status=0):
        """创建新评论
        
        Args:
            content (str): 评论内容
            post_id (int): 文章ID
            author_id (int): 作者ID
            parent_id (int, optional): 父评论ID
            status (int, optional): 评论状态，默认为0（待审核）
            
        Returns:
            Comment: 创建的评论对象
            
        Raises:
            ValueError: 当参数无效时抛出
        """
        # 验证评论内容
        if not content:
            raise ValueError("评论内容不能为空")
            
        # 验证文章是否存在
        post = db.session.get(Post, post_id)
        if not post:
            raise ValueError("文章不存在")
            
        # 验证用户是否存在
        user = db.session.get(User, author_id)
        if not user:
            raise ValueError("用户不存在")
            
        # 如果有父评论，验证其是否存在
        if parent_id:
            parent_comment = db.session.get(Comment, parent_id)
            if not parent_comment:
                raise ValueError("父评论不存在")
            if parent_comment.post_id != post_id:
                raise ValueError("父评论不属于该文章")
            
        comment = Comment(
            content=content,
            post_id=post_id,
            author_id=author_id,
            parent_id=parent_id,
            status=status
        )
        
        try:
            db.session.add(comment)
            db.session.commit()
            
            # 发送通知
            from app.services.notification import NotificationService
            notification_service = NotificationService()
            
            # 如果是回复评论，通知原评论作者
            if parent_id:
                notification_service.notify_comment_reply(comment)
            # 否则通知文章作者
            else:
                notification_service.notify_new_comment(comment)
                
            return comment
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"创建评论失败：{str(e)}")
    
    @staticmethod
    def get_comment(comment_id):
        """获取评论"""
        return db.session.get(Comment, comment_id)
    
    @staticmethod
    def get_comments_by_post(post_id, page=1, per_page=10, include_pending=False):
        """获取文章的评论列表
        
        Args:
            post_id (int): 文章ID
            page (int): 页码
            per_page (int): 每页数量
            include_pending (bool): 是否包含待审核评论
            
        Returns:
            Pagination: 评论分页对象
        """
        query = Comment.query.filter_by(post_id=post_id, parent_id=None)
        if not include_pending:
            query = query.filter_by(status=1)
        return query.order_by(Comment.created_at.desc())\
            .paginate(page=page, per_page=per_page)
    
    @staticmethod
    def get_total_pending_comments():
        """获取待审核评论数量"""
        return Comment.query.filter_by(status=0).count()
    
    @staticmethod
    def get_pending_comments(page=1, per_page=10):
        """获取待审核的评论列表"""
        return Comment.query.filter_by(status=0)\
            .order_by(Comment.created_at.desc())\
            .paginate(page=page, per_page=per_page)
    
    @staticmethod
    def get_recent_comments(limit=5):
        """获取最近的评论"""
        return Comment.query.filter_by(status=1)\
            .order_by(Comment.created_at.desc())\
            .limit(limit).all()
    
    @staticmethod
    def update_comment_status(comment_id, status):
        """更新评论状态"""
        comment = CommentService.get_comment(comment_id)
        if comment:
            comment.status = status
            db.session.commit()
            return comment
        return None
    
    @staticmethod
    def delete_comment(comment_id):
        """删除评论"""
        comment = CommentService.get_comment(comment_id)
        if comment:
            db.session.delete(comment)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def approve_comment(comment_id):
        """审核通过评论"""
        comment = CommentService.get_comment(comment_id)
        if not comment:
            raise ValueError("评论不存在")
            
        comment.status = 1
        db.session.commit()
        return comment
    
    @staticmethod
    def reject_comment(comment_id):
        """拒绝评论
        
        Args:
            comment_id (int): 评论ID
            
        Returns:
            bool: 是否成功删除评论
            
        Raises:
            ValueError: 当评论不存在时抛出
        """
        comment = CommentService.get_comment(comment_id)
        if not comment:
            raise ValueError("评论不存在")
            
        db.session.delete(comment)
        db.session.commit()
        return True
    
    @staticmethod
    def update(comment_id, **kwargs):
        """更新评论
        
        Args:
            comment_id (int): 评论ID
            **kwargs: 要更新的字段
            
        Returns:
            Comment: 更新后的评论对象
            
        Raises:
            ValueError: 当评论不存在或更新失败时抛出
        """
        comment = CommentService.get_comment(comment_id)
        if not comment:
            raise ValueError("评论不存在")
            
        try:
            for key, value in kwargs.items():
                if hasattr(comment, key):
                    setattr(comment, key, value)
                    
            # 如果更新了内容，重新解析Markdown
            if 'content' in kwargs:
                result = markdown_to_html(kwargs['content'])
                comment.html_content = result['html']
                
            db.session.commit()
            return comment
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"更新评论失败：{str(e)}") 