"""
文件名：comment.py
描述：评论服务
作者：denny
"""

from datetime import datetime, timedelta
from flask import current_app
from app.extensions import db
from app.models.comment import Comment, CommentStatus
from app.models.post import Post
from app.models.user import User
from app.services.security import SecurityService
from app.utils.markdown import markdown_to_html
from sqlalchemy import or_, and_, func
from typing import Dict, List, Optional

class CommentService:
    """评论服务类"""
    
    def __init__(self):
        self.security_service = SecurityService()
        
    @staticmethod
    def create_comment(post_id, content, author_id=None, nickname=None, email=None, parent_id=None):
        """
        创建评论
        :param post_id: 文章ID
        :param content: 评论内容
        :param author_id: 作者ID（可选）
        :param nickname: 昵称（可选）
        :param email: 邮箱（可选）
        :param parent_id: 父评论ID（可选）
        :return: 创建的评论对象
        """
        try:
            # 验证评论内容
            if not content or len(content.strip()) == 0:
                return {
                    'success': False,
                    'message': '评论内容不能为空'
                }
            
            if len(content) > 1000:  # 限制评论长度
                return {
                    'success': False,
                    'message': '评论内容不能超过1000个字符'
                }
            
            # 如果是匿名评论，验证昵称和邮箱
            if not author_id:
                if not nickname or not email:
                    return {
                        'success': False,
                        'message': '请输入昵称和邮箱'
                    }

            # 检查是否存在相同内容的评论（5分钟内）
            current_time = datetime.now()
            five_minutes_ago = current_time - timedelta(minutes=5)
            
            # 开始事务
            db.session.begin()
            
            try:
                # 构建查询条件
                duplicate_conditions = [
                    Comment.post_id == post_id,
                    Comment.content.ilike(content.strip()),  # 内容相同（不区分大小写）
                    Comment.created_at >= five_minutes_ago,
                    Comment.created_at <= current_time
                ]
                
                # 如果是登录用户，检查author_id
                if author_id:
                    duplicate_conditions.append(Comment.author_id == author_id)
                else:
                    # 如果是匿名用户，检查email
                    duplicate_conditions.append(Comment.email == email)
                
                # 使用SELECT FOR UPDATE锁定相关记录
                existing_comment = Comment.query.with_for_update().filter(and_(*duplicate_conditions)).first()
                
                if existing_comment:
                    # 回滚事务
                    db.session.rollback()
                    current_app.logger.info(
                        f'发现重复评论: post_id={post_id}, '
                        f'author_id={author_id}, email={email}, '
                        f'content={content}, '
                        f'existing_comment_id={existing_comment.id}, '
                        f'existing_time={existing_comment.created_at}, '
                        f'current_time={current_time}, '
                        f'five_minutes_ago={five_minutes_ago}'
                    )
                    return {
                        'success': False,
                        'message': '请不要重复发表相同的评论'
                    }

                # 验证父评论是否存在
                if parent_id:
                    parent_comment = Comment.query.get(parent_id)
                    if not parent_comment:
                        # 回滚事务
                        db.session.rollback()
                        return {
                            'success': False,
                            'message': '父评论不存在'
                        }
                    
                    # 如果回复的是子评论，则将parent_id设置为顶级评论的ID
                    if parent_comment.parent_id is not None:
                        parent_id = parent_comment.parent_id

                # 创建评论 - 所有评论都自动通过审核
                comment_status = CommentStatus.APPROVED  # 所有评论都设置为已审核
                current_app.logger.info(f'设置评论状态: author_id={author_id}, status={comment_status}')
                
                comment = Comment(
                    post_id=post_id,
                    content=content.strip(),  # 去除首尾空格
                    html_content=markdown_to_html(content.strip()),  # 转换Markdown为HTML
                    author_id=author_id,
                    nickname=nickname.strip() if nickname else None,  # 去除昵称首尾空格
                    email=email.strip() if email else None,  # 去除邮箱首尾空格
                    parent_id=parent_id,
                    status=comment_status,  # 所有评论都自动通过审核
                    created_at=current_time,
                    updated_at=current_time
                )
                
                current_app.logger.info(f'评论对象创建: post_id={post_id}, author_id={author_id}, initial_status={comment_status}')
                
                # 添加评论
                db.session.add(comment)
                
                # 再次强制设置状态，确保评论状态为已审核
                if comment.status != CommentStatus.APPROVED:
                    comment.status = CommentStatus.APPROVED
                    current_app.logger.warning(f'强制更正评论状态: status={CommentStatus.APPROVED}')
                
                # 提交事务
                db.session.commit()
                
                # 验证提交后的状态，并确保评论状态是已审核
                db.session.refresh(comment)
                
                # 再次强制确认：如果评论状态不是已审核，强制更新为已审核
                if comment.status != CommentStatus.APPROVED:
                    current_app.logger.warning(f'发现评论状态不正确: id={comment.id}, status={comment.status}，强制更新为已审核')
                    # 直接执行SQL更新以避免任何可能的模型逻辑干扰
                    db.session.execute(
                        db.text("UPDATE comments SET status = :status WHERE id = :id"),
                        {"status": int(CommentStatus.APPROVED), "id": comment.id}
                    )
                    db.session.commit()
                    db.session.refresh(comment)
                
                current_app.logger.info(f'评论创建成功: id={comment.id}, post_id={post_id}, author_id={author_id}, status={comment.status}, content={content}, created_at={current_time}')
                
                return {
                    'success': True,
                    'message': '评论发表成功',  # 所有评论都自动通过，不再显示"请等待审核"
                    'comment': {
                        'id': comment.id,
                        'content': comment.content,
                        'html_content': comment.html_content,
                        'author_name': comment.author.username if comment.author else comment.nickname,
                        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'status': comment.status
                    }
                }
                
            except Exception as e:
                # 回滚事务
                if db.session.is_active:
                    db.session.rollback()
                current_app.logger.error(f'创建评论失败: {str(e)}')
                return {
                    'success': False,
                    'message': '评论创建失败'
                }
                
        except Exception as e:
            current_app.logger.error(f'创建评论失败: {str(e)}')
            return {
                'success': False,
                'message': '评论创建失败'
            }

    @staticmethod
    def get_post_comments(post_id):
        """
        获取文章的评论列表
        :param post_id: 文章ID
        :return: 评论列表
        """
        try:
            # 只获取已审核状态的评论，排除被拒绝的评论
            comments = Comment.query.filter(
                Comment.post_id == post_id,
                Comment.parent_id == None,  # 只获取顶级评论
                Comment.status == CommentStatus.APPROVED  # 只获取已审核的评论
            ).order_by(Comment.created_at.desc()).all()
            
            # 获取评论的回复
            for comment in comments:
                # 手动加载回复，并过滤出已审核的回复
                comment.replies = Comment.query.filter(
                    Comment.parent_id == comment.id,
                    Comment.status == CommentStatus.APPROVED
                ).order_by(Comment.created_at.asc()).all()
            
            return comments
            
        except Exception as e:
            current_app.logger.error(f'获取评论列表失败: {str(e)}')
            return []

    @staticmethod
    def get_comment_by_id(comment_id):
        """
        根据ID获取评论
        :param comment_id: 评论ID
        :return: 评论对象
        """
        try:
            return Comment.query.get(comment_id)
        except Exception as e:
            current_app.logger.error(f'获取评论失败: {str(e)}')
            return None
            
    def get_comment_stats(self):
        """获取评论统计数据
        
        Returns:
            dict: 包含各状态评论数量的字典
        """
        try:
            from app.models.comment import Comment, CommentStatus
            
            pending_count = Comment.query.filter_by(status=CommentStatus.PENDING).count()
            approved_count = Comment.query.filter_by(status=CommentStatus.APPROVED).count()
            rejected_count = Comment.query.filter_by(status=CommentStatus.REJECTED).count()
            
            current_app.logger.info(f'评论统计: 待审核 {pending_count}, 已审核 {approved_count}, 已拒绝 {rejected_count}')
            
            return {
                'pending_count': pending_count,
                'approved_count': approved_count,
                'rejected_count': rejected_count
            }
        except Exception as e:
            current_app.logger.error(f'获取评论统计失败: {str(e)}')
            return {
                'pending_count': 0,
                'approved_count': 0,
                'rejected_count': 0
            }
    
    def get_recent_comments(self, search=None, limit=5) -> List[Comment]:
        """获取最近评论
        
        Args:
            search: 搜索关键词
            limit: 返回的评论数量
            
        Returns:
            List[Comment]: 评论列表
        """
        try:
            # 构建基础查询
            query = Comment.query
            
            # 如果有搜索关键词，添加搜索条件
            if search:
                search_query = or_(
                    Comment.content.ilike(f'%{search}%'),
                    Comment.author_name.ilike(f'%{search}%'),
                    Comment.author_email.ilike(f'%{search}%')
                )
                query = query.filter(search_query)
            
            # 获取最新的评论
            comments = query.order_by(Comment.created_at.desc()).limit(limit).all()
            
            current_app.logger.info('成功获取最近评论', extra={
                'data': {
                    'search': search,
                    'limit': limit,
                    'count': len(comments)
                }
            })
            
            return comments
            
        except Exception as e:
            current_app.logger.error(f'获取最近评论失败: {str(e)}')
            current_app.logger.exception(e)
            return []
            
    def count_comments(self, search=None):
        """统计评论数量
        
        Args:
            search: 搜索关键词
            
        Returns:
            int: 评论数量
        """
        try:
            query = Comment.query
            
            # 如果有搜索条件，添加搜索过滤
            if search:
                query = query.filter(
                    or_(
                        Comment.content.ilike(f'%{search}%'),
                        Comment.nickname.ilike(f'%{search}%'),
                        Comment.email.ilike(f'%{search}%')
                    )
                )
            
            count = query.count()
            
            current_app.logger.info('成功统计评论数量', extra={
                'data': {
                    'search': search,
                    'count': count
                }
            })
            
            return count
            
        except Exception as e:
            current_app.logger.error(f'统计评论数量失败: {str(e)}')
            current_app.logger.exception(e)
            return 0
            
    def count_comments_since(self, start_time: datetime) -> int:
        """统计指定时间之后的评论数量
        
        Args:
            start_time: 开始时间
            
        Returns:
            int: 评论数量
        """
        try:
            count = Comment.query.filter(Comment.created_at >= start_time).count()
            
            current_app.logger.info('成功统计指定时间之后的评论数量', extra={
                'data': {
                    'start_time': start_time,
                    'count': count
                }
            })
            
            return count
            
        except Exception as e:
            current_app.logger.error(f'统计指定时间之后的评论数量失败: {str(e)}')
            current_app.logger.exception(e)
            return 0

    @staticmethod
    def update_comment_status(comment_id, status):
        """
        更新评论状态
        :param comment_id: 评论ID
        :param status: 状态（0-待审核，1-已通过，2-已拒绝）
        :return: 是否更新成功
        """
        try:
            comment = Comment.query.get(comment_id)
            if comment:
                comment.status = status
                db.session.commit()
                return True
            return False
        except Exception as e:
            current_app.logger.error(f'更新评论状态失败: {str(e)}')
            db.session.rollback()
            return False

    @staticmethod
    def delete_comment(comment_id):
        """
        删除评论
        :param comment_id: 评论ID
        :return: 是否删除成功
        """
        try:
            comment = Comment.query.get(comment_id)
            if comment:
                db.session.delete(comment)
                db.session.commit()
                return True
            return False
        except Exception as e:
            current_app.logger.error(f'删除评论失败: {str(e)}')
            db.session.rollback()
            return False

    def get_comments(self, page=1, per_page=10, status=None, parent_only=False):
        """获取评论列表"""
        try:
            query = Comment.query
            
            # 根据状态筛选
            if status is not None:
                query = query.filter(Comment.status == status)
                
            # 如果只显示父评论
            if parent_only:
                query = query.filter(Comment.parent_id == None)
                
            # 按时间倒序排序
            query = query.order_by(Comment.created_at.desc())
            
            # 使用 SQLAlchemy 的分页
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            comments = pagination.items
            
            return {
                'status': 'success',
                'comments': comments,
                'pagination': pagination
            }
            
        except Exception as e:
            current_app.logger.error(f'获取评论列表失败: {str(e)}')
            return {
                'status': 'error',
                'message': '获取评论列表失败'
            }
            
    def count_comments_by_status(self, status):
        """获取指定状态的评论数量"""
        try:
            return Comment.query.filter_by(status=status).count()
        except Exception as e:
            current_app.logger.error(f'获取评论数量失败: {str(e)}')
            return 0
            
    def delete_comment(self, comment_id, delete_replies=False):
        """删除评论"""
        try:
            comment = Comment.query.get(comment_id)
            if not comment:
                return {
                    'status': 'error',
                    'message': '评论不存在'
                }
                
            deleted_replies_count = 0
            if delete_replies:
                # 删除所有回复
                replies = Comment.query.filter_by(parent_id=comment_id).all()
                for reply in replies:
                    db.session.delete(reply)
                    deleted_replies_count += 1
                    
            # 删除评论
            db.session.delete(comment)
            db.session.commit()
            
            return {
                'status': 'success',
                'message': '删除成功',
                'deleted_replies_count': deleted_replies_count
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'删除评论失败: {str(e)}')
            return {
                'status': 'error',
                'message': '删除失败'
            }
            
    def approve_comment(self, comment_id, approve_replies=False):
        """审核通过评论"""
        try:
            comment = Comment.query.get(comment_id)
            if not comment:
                return {
                    'status': 'error',
                    'message': '评论不存在'
                }
                
            comment.status = CommentStatus.APPROVED
            
            if approve_replies:
                # 审核通过所有回复
                Comment.query.filter_by(parent_id=comment_id).update({
                    'status': CommentStatus.APPROVED
                })
                
            db.session.commit()
            
            return {
                'status': 'success',
                'message': '审核通过'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'审核评论失败: {str(e)}')
            return {
                'status': 'error',
                'message': '审核失败'
            }
            
    def reject_comment(self, comment_id, reject_replies=False):
        """拒绝评论
        
        Args:
            comment_id: 评论id
            reject_replies: 是否同时拒绝回复
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            from app.extensions import db
            from app.models.comment import Comment, CommentStatus
            
            comment = Comment.query.get(comment_id)
            if not comment:
                current_app.logger.error(f'评论未找到: {comment_id}')
                return {
                    'status': 'error',
                    'message': f'评论未找到: {comment_id}'
                }
            
            # 更新评论状态
            comment.status = CommentStatus.REJECTED
            
            # 如果需要同时拒绝回复
            if reject_replies and comment.parent_id is None:
                replies = Comment.query.filter_by(parent_id=comment_id).all()
                for reply in replies:
                    reply.status = CommentStatus.REJECTED
                    current_app.logger.info(f'回复已拒绝: {reply.id}')
            
            db.session.commit()
            current_app.logger.info(f'评论已拒绝: {comment_id}')
            
            return {
                'status': 'success',
                'message': '评论已拒绝'
            }
        except Exception as e:
            current_app.logger.error(f'拒绝评论失败: {str(e)}')
            return {
                'status': 'error',
                'message': f'拒绝评论失败: {str(e)}'
            }
            
    def batch_delete_comments(self, comment_ids, delete_replies=False):
        """批量删除评论"""
        try:
            if not comment_ids:
                return {
                    'status': 'error',
                    'message': '请选择要删除的评论'
                }
                
            deleted_count = 0
            deleted_replies_count = 0
            
            for comment_id in comment_ids:
                result = self.delete_comment(comment_id, delete_replies)
                if result['status'] == 'success':
                    deleted_count += 1
                    if 'deleted_replies_count' in result:
                        deleted_replies_count += result['deleted_replies_count']
                        
            if deleted_count > 0:
                message = f'成功删除 {deleted_count} 条评论'
                if deleted_replies_count > 0:
                    message += f'，包含 {deleted_replies_count} 条回复'
                    
                return {
                    'status': 'success',
                    'message': message
                }
            else:
                return {
                    'status': 'error',
                    'message': '删除失败，请稍后重试'
                }
                
        except Exception as e:
            current_app.logger.error(f'批量删除评论失败: {str(e)}')
            return {
                'status': 'error',
                'message': '系统错误，请稍后重试'
            }

    def get_comments_by_post(self, post_id, page=1, per_page=10, include_pending=False):
        """获取文章的评论列表
        
        Args:
            post_id: 文章ID
            page: 页码
            per_page: 每页数量
            include_pending: 是否包含待审核评论
            
        Returns:
            list: 评论列表，包含子评论
        """
        try:
            # 获取顶级评论
            query = Comment.query.filter_by(post_id=post_id, parent_id=None)
            if not include_pending:
                # 只获取已审核通过的评论，明确排除待审核和已拒绝的评论
                query = query.filter_by(status=CommentStatus.APPROVED)
            else:
                # 即使包含待审核评论，也要排除已拒绝的评论
                query = query.filter(Comment.status != CommentStatus.REJECTED)
            
            # 按创建时间倒序排序
            query = query.order_by(Comment.created_at.desc())
            
            # 获取分页数据
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            # 获取每个顶级评论的子评论
            comments = []
            for comment in pagination.items:
                # 获取子评论
                replies_query = Comment.query.filter_by(post_id=post_id, parent_id=comment.id)
                if not include_pending:
                    # 只获取已审核通过的子评论
                    replies_query = replies_query.filter_by(status=CommentStatus.APPROVED)
                else:
                    # 即使包含待审核子评论，也要排除已拒绝的子评论
                    replies_query = replies_query.filter(Comment.status != CommentStatus.REJECTED)
                    
                replies = replies_query.order_by(Comment.created_at.asc()).all()
                
                # 添加子评论属性
                comment.replies = replies
                comments.append(comment)
            
            # 替换分页对象中的items
            pagination.items = comments
            return pagination
            
        except Exception as e:
            current_app.logger.error(f"获取文章评论列表失败: {str(e)}")
            raise e
    
    def get_pending_comments(self, page=1, per_page=10):
        """获取待审核的评论列表
        
        Args:
            page: 页码
            per_page: 每页数量
            
        Returns:
            Pagination: 分页对象
        """
        try:
            current_app.logger.info('获取待审核评论列表，参数：%s', {
                'page': page,
                'per_page': per_page
            })
            
            # 获取待审核的评论
            query = Comment.query.filter_by(status=CommentStatus.PENDING)
            
            # 按创建时间倒序排序
            query = query.order_by(Comment.created_at.desc())
            
            # 分页
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            current_app.logger.info('查询到 %d 条待审核评论', len(pagination.items))
            return pagination
            
        except Exception as e:
            current_app.logger.error(f"获取待审核评论列表失败: {str(e)}")
            raise e
    
    def get_comment_tree(self, post_id, include_pending=False, user_id=None, user_email=None):
        """获取评论树
        
        Args:
            post_id: 文章ID
            include_pending: 是否包含待审核评论
            user_id: 用户ID
            user_email: 用户邮箱
            
        Returns:
            list: 评论树列表
        """
        try:
            current_app.logger.info(f"获取评论树，参数：post_id={post_id}, include_pending={include_pending}, user_id={user_id}, user_email={user_email}")
            
            # 构建基本查询
            query = Comment.query.filter(Comment.post_id == post_id)
            
            # 处理评论状态过滤
            if not include_pending:
                # 只获取已审核通过的评论
                query = query.filter(Comment.status == CommentStatus.APPROVED)
            elif user_id or user_email:
                # 显示已通过的评论和用户自己的待审核评论，但排除被拒绝的评论
                query = query.filter(or_(
                    Comment.status == CommentStatus.APPROVED,
                    and_(
                        Comment.status == CommentStatus.PENDING,
                        or_(
                            Comment.author_id == user_id if user_id else False,
                            Comment.email == user_email if user_email else False
                        )
                    )
                ))
            else:
                # 只显示已审核通过的评论
                query = query.filter(Comment.status == CommentStatus.APPROVED)
            
            # 始终排除被拒绝的评论
            query = query.filter(Comment.status != CommentStatus.REJECTED)
            
            # 获取所有符合条件的评论
            comments = query.order_by(Comment.created_at.asc()).all()
            current_app.logger.info(f"查询到 {len(comments)} 条评论")
            
            # 构建评论树
            comment_dict = {}  # 用于存储所有评论的字典
            root_comments = []  # 存储顶级评论
            
            # 第一次遍历：创建所有评论的字典
            for comment in comments:
                comment_data = {
                    'id': comment.id,
                    'content': comment.content,
                    'html_content': comment.html_content,
                    'author_name': comment.author.username if comment.author else comment.nickname,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': comment.status,
                    'children': []
                }
                comment_dict[comment.id] = comment_data
            
            # 第二次遍历：构建树形结构
            for comment in comments:
                if comment.parent_id is None:
                    # 这是一个顶级评论
                    root_comments.append(comment_dict[comment.id])
                else:
                    # 这是一个回复
                    parent_comment = comment_dict.get(comment.parent_id)
                    if parent_comment:
                        parent_comment['children'].append(comment_dict[comment.id])
            
            current_app.logger.info(f"构建评论树完成，根评论数：{len(root_comments)}")
            return root_comments
            
        except Exception as e:
            current_app.logger.error(f"获取评论树失败: {str(e)}")
            return []

    def get_comments_by_post_id(self, post_id, include_pending=False, user_id=None, user_email=None):
        """
        获取文章的评论列表
        :param post_id: 文章ID
        :param include_pending: 是否包含待审核评论
        :param user_id: 用户ID（用于获取用户自己的待审核评论）
        :param user_email: 用户邮箱（用于获取匿名用户自己的待审核评论）
        :return: 评论列表
        """
        try:
            # 基础查询：获取顶级评论（没有父评论的评论）
            query = Comment.query.filter(
                Comment.post_id == post_id,
                Comment.parent_id == None  # 只获取顶级评论
            )

            # 处理评论状态过滤
            if not include_pending:
                # 只获取已审核的评论
                query = query.filter(Comment.status == CommentStatus.APPROVED)
            else:
                # 如果包含待审核评论，需要根据用户身份过滤
                if user_email:
                    # 获取已审核的评论和用户自己的待审核评论
                    query = query.filter(
                        or_(
                            Comment.status == CommentStatus.APPROVED,
                            and_(
                                Comment.status == CommentStatus.PENDING,
                                Comment.email == user_email
                            )
                        )
                    )
                elif user_id:
                    # 获取已审核的评论和用户自己的待审核评论
                    query = query.filter(
                        or_(
                            Comment.status == CommentStatus.APPROVED,
                            and_(
                                Comment.status == CommentStatus.PENDING,
                                Comment.author_id == user_id
                            )
                        )
                    )
                else:
                    # 只获取已审核的评论
                    query = query.filter(Comment.status == CommentStatus.APPROVED)
            
            # 始终排除被拒绝的评论
            query = query.filter(Comment.status != CommentStatus.REJECTED)

            # 按创建时间排序
            query = query.order_by(Comment.created_at.desc())

            # 获取所有符合条件的顶级评论
            top_level_comments = query.all()

            # 为每个顶级评论获取回复
            for comment in top_level_comments:
                # 获取回复
                replies_query = Comment.query.filter(
                    Comment.parent_id == comment.id
                )
                
                # 处理回复的状态过滤
                if not include_pending:
                    replies_query = replies_query.filter(Comment.status == CommentStatus.APPROVED)
                else:
                    if user_email:
                        replies_query = replies_query.filter(
                            or_(
                                Comment.status == CommentStatus.APPROVED,
                                and_(
                                    Comment.status == CommentStatus.PENDING,
                                    Comment.email == user_email
                                )
                            )
                        )
                    else:
                        replies_query = replies_query.filter(Comment.status == CommentStatus.APPROVED)
                
                # 获取回复并排序
                replies = replies_query.order_by(Comment.created_at.asc()).all()
                
                # 设置回复
                comment.children = replies

            return top_level_comments

        except Exception as e:
            current_app.logger.error(f"Error getting comments for post {post_id}: {str(e)}")
            return []

    def get_comment_count(self, post_id):
        """获取文章的评论数
        
        Args:
            post_id: 文章ID
            
        Returns:
            int: 评论数量
        """
        try:
            # 只统计已审核的评论
            count = Comment.query.filter(
                Comment.post_id == post_id,
                Comment.status == CommentStatus.APPROVED
            ).count()
            
            return count
        except Exception as e:
            current_app.logger.error(f"获取评论数失败: {str(e)}")
            return 0

    def ensure_user_comment_status(self):
        """确保所有评论状态正确（待审核状态的评论改为已审核），但不修改已拒绝的评论
        
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            from app.extensions import db
            from app.models.comment import Comment, CommentStatus
            
            # 获取所有待审核状态的评论，不包括已拒绝的评论
            comments_to_update = Comment.query.filter(Comment.status == CommentStatus.PENDING).all()
            
            if not comments_to_update:
                return {
                    'success': True,
                    'message': '所有评论状态已正确'
                }
            
            update_count = 0
            for comment in comments_to_update:
                # 更新状态为已审核
                comment.status = CommentStatus.APPROVED
                update_count += 1
            
            db.session.commit()
            
            current_app.logger.info(f'已修正{update_count}条评论的状态')
            
            return {
                'success': True,
                'message': f'已修正{update_count}条评论的状态'
            }
        except Exception as e:
            current_app.logger.error(f'修正评论状态失败: {str(e)}')
            return {
                'success': False,
                'message': f'修正评论状态失败: {str(e)}'
            }