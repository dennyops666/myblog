"""
文件名：comment.py
描述：评论服务
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, UTC
from flask import current_app
from app.extensions import db
from app.models.comment import Comment
from app.models.post import Post
from app.services.security import SecurityService

class CommentService:
    """评论服务类"""
    
    def __init__(self):
        self.security_service = SecurityService()
        
    def create_comment(self, post_id, content, nickname=None, email=None, author_id=None, parent_id=None):
        """创建评论
        
        Args:
            post_id: 文章ID
            content: 评论内容
            nickname: 昵称（匿名评论时使用）
            email: 邮箱（匿名评论时使用）
            author_id: 作者ID（可选）
            parent_id: 父评论ID（可选）
            
        Returns:
            dict: 包含状态和消息的字典
            
        Raises:
            ValueError: 如果必要参数缺失或无效
        """
        try:
            if not content:
                return {'status': 'error', 'message': '评论内容不能为空'}
            
            # 检查文章是否存在
            post = db.session.get(Post, post_id)
            if not post:
                return {'status': 'error', 'message': '文章不存在'}
            
            # 检查父评论是否存在
            parent = None
            if parent_id:
                parent = db.session.get(Comment, parent_id)
                if not parent or parent.post_id != post_id:
                    return {'status': 'error', 'message': '父评论不存在或不属于该文章'}
            
            # 清理输入
            content = self.security_service.sanitize_comment(content)
            
            # 创建评论
            comment = Comment(
                content=content,
                post_id=post_id,
                author_id=author_id,
                parent_id=parent_id,
                nickname=nickname,
                email=email,
                status=1 if author_id else 0  # 已登录用户评论直接通过，匿名评论需要审核
            )
            
            db.session.add(comment)
            db.session.commit()
            
            return {'status': 'success', 'message': '评论创建成功', 'comment': comment}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建评论失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
            
    def update_comment(self, comment_id, content):
        """更新评论
        
        Args:
            comment_id: 评论ID
            content: 新内容
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            comment = db.session.get(Comment, comment_id)
            if not comment:
                return {'status': 'error', 'message': '评论不存在'}
                
            # 清理输入
            content = self.security_service.sanitize_comment(content)
            
            # 更新评论
            comment.content = content
            comment.updated_at = datetime.now(UTC)
            db.session.commit()
            
            return {'status': 'success', 'message': '评论更新成功', 'comment': comment}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新评论失败: {str(e)}")
            return {'status': 'error', 'message': '更新评论失败，请稍后重试'}
            
    def delete_comment(self, comment_id):
        """删除评论
        
        Args:
            comment_id: 评论ID
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            comment = db.session.get(Comment, comment_id)
            if not comment:
                return {'status': 'error', 'message': '评论不存在'}
                
            db.session.delete(comment)
            db.session.commit()
            
            return {'status': 'success', 'message': '评论删除成功'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"删除评论失败: {str(e)}")
            return {'status': 'error', 'message': '删除评论失败，请稍后重试'}
            
    def get_comment(self, comment_id):
        """获取评论
        
        Args:
            comment_id: 评论ID
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            comment = db.session.get(Comment, comment_id)
            if not comment:
                return {'status': 'error', 'message': '评论不存在'}
                
            return {'status': 'success', 'comment': comment}
            
        except Exception as e:
            current_app.logger.error(f"获取评论失败: {str(e)}")
            return {'status': 'error', 'message': '获取评论失败，请稍后重试'}
            
    def get_comments(self, page=1, per_page=10, post_id=None, author_id=None):
        """获取评论列表
        
        Args:
            page: 页码
            per_page: 每页数量
            post_id: 文章ID
            author_id: 作者ID
            
        Returns:
            Pagination: 分页对象
        """
        try:
            query = Comment.query
            
            # 按文章筛选
            if post_id:
                query = query.filter_by(post_id=post_id)
                
            # 按作者筛选
            if author_id:
                query = query.filter_by(author_id=author_id)
                
            # 分页
            return query.order_by(Comment.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
        except Exception as e:
            current_app.logger.error(f"获取评论列表失败: {str(e)}")
            raise e
    
    def get_comment_by_id(self, comment_id):
        """根据ID获取评论"""
        return db.session.get(Comment, comment_id)
    
    def get_comments_by_post(self, post_id, page=1, per_page=10, include_pending=False):
        """获取文章的评论列表"""
        query = Comment.query.filter_by(post_id=post_id)
        if not include_pending:
            query = query.filter_by(status=1)  # 只获取已审核的评论
        
        return query.order_by(Comment.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    def approve_comment(self, comment_id):
        """审核通过评论"""
        try:
            comment = self.get_comment_by_id(comment_id)
            if not comment:
                return False, "评论不存在"
            
            comment.status = 1  # 设置为已审核
            db.session.commit()
            return True, "评论审核通过"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"审核评论失败: {str(e)}")
            return False, str(e)
    
    def reject_comment(self, comment_id):
        """拒绝评论"""
        try:
            comment = self.get_comment_by_id(comment_id)
            if not comment:
                return False, "评论不存在"
            
            db.session.delete(comment)  # 直接删除被拒绝的评论
            db.session.commit()
            return True, "评论已被拒绝并删除"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"拒绝评论失败: {str(e)}")
            return False, str(e)
    
    def get_pending_comments(self, page=1, per_page=10):
        """获取待审核的评论列表
        
        Args:
            page: 页码
            per_page: 每页数量
            
        Returns:
            Pagination: 分页对象
        """
        try:
            return Comment.query.filter_by(status=0).order_by(
                Comment.created_at.desc()
            ).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
        except Exception as e:
            current_app.logger.error(f"获取待审核评论列表失败: {str(e)}")
            raise e
    
    def get_comment_stats(self):
        """获取评论统计信息"""
        total_comments = Comment.query.count()
        pending_comments = Comment.query.filter_by(status=0).count()
        approved_comments = Comment.query.filter_by(status=1).count()
        
        return {
            'total_comments': total_comments,
            'pending_comments': pending_comments,
            'approved_comments': approved_comments
        }

    def get_comments_by_post_id(self, post_id, include_pending=False):
        """获取文章的评论列表
        
        Args:
            post_id: 文章ID
            include_pending: 是否包含待审核评论
            
        Returns:
            list: 评论列表
        """
        query = Comment.query.filter_by(post_id=post_id)
        if not include_pending:
            query = query.filter_by(status=1)  # 只获取已审核的评论
        return query.order_by(Comment.created_at.desc()).all() 