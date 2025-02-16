"""
文件名：comment_service.py
描述：评论服务类
作者：denny
创建日期：2025-02-16
"""

from app.models import Comment, db

class CommentService:
    @staticmethod
    def create_comment(content, post_id, author_name, author_email, parent_id=None, status=0):
        """创建新评论"""
        if not content or not post_id or not author_name or not author_email:
            raise ValueError("评论内容、文章ID、作者名和邮箱不能为空")
            
        comment = Comment(
            content=content,
            post_id=post_id,
            author_name=author_name,
            author_email=author_email,
            parent_id=parent_id,
            status=status
        )
        db.session.add(comment)
        db.session.commit()
        return comment
    
    @staticmethod
    def get_comment_by_id(comment_id):
        """根据ID获取评论"""
        return Comment.query.get(comment_id)
    
    @staticmethod
    def get_comments_by_post(post_id, page=1, per_page=10):
        """获取文章的评论列表"""
        return Comment.query.filter_by(post_id=post_id, parent_id=None, status=1)\
            .order_by(Comment.created_at.desc())\
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
        comment = CommentService.get_comment_by_id(comment_id)
        if comment:
            comment.status = status
            db.session.commit()
            return comment
        return None
    
    @staticmethod
    def delete_comment(comment_id):
        """删除评论"""
        comment = CommentService.get_comment_by_id(comment_id)
        if comment:
            db.session.delete(comment)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def approve_comment(comment):
        """审核通过评论"""
        comment.status = 1
        db.session.commit()
        return comment
    
    @staticmethod
    def reject_comment(comment):
        """拒绝评论"""
        db.session.delete(comment)
        db.session.commit() 