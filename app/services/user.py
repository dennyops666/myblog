"""
文件名：user.py
描述：用户服务
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, UTC
from flask import current_app
from app.extensions import db
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.services.security import SecurityService
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
import re

class UserService:
    """用户服务类"""
    
    def __init__(self):
        self.security = SecurityService()
    
    def create_user(self, username, email, password, nickname='', is_active=True, role_ids=None):
        """创建用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            nickname: 昵称
            is_active: 是否激活
            role_ids: 角色ID列表
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            # 验证用户名
            # 验证管理员用户名
            if User.is_admin_username(username):
                admin_user = User.get_admin_user()
                if admin_user:
                    return {'status': False, 'message': '超级管理员用户名已存在，不能创建同名用户'}
            
            # 检查用户名是否已存在
            if User.query.filter_by(username=username).first():
                return {'status': False, 'message': '用户名已存在'}
            
            # 验证邮箱
            if not email:
                return {'status': False, 'message': '邮箱不能为空'}
            
            # 验证密码
            result = self.validate_password(password)
            if not result['success']:
                return {'status': False, 'message': result['message']}
            
            # 检查用户名和邮箱是否已存在
            if User.query.filter_by(username=username).first():
                return {'status': False, 'message': '该用户名已被使用'}
                
            if User.query.filter_by(email=email).first():
                return {'status': False, 'message': '该邮箱已被使用'}
            
            # 创建用户对象
            user = User(
                username=username,
                email=email,
                nickname=nickname or username,
                is_active=True if is_active in [True, 'on', 1, '1'] else False  # 处理各种可能的is_active值
            )
            user.set_password(password)
            
            # 分配角色
            if role_ids:
                # 过滤掉 super_admin 角色
                roles = Role.query.filter(
                    Role.id.in_(role_ids),
                    Role.name != 'super_admin'
                ).all()
                user.roles = roles
            else:
                # 如果没有指定角色，添加默认角色
                default_role = Role.query.filter_by(name='user').first()
                if default_role:
                    user.roles.append(default_role)
            
            # 保存到数据库
            db.session.add(user)
            db.session.commit()
            
            return {'status': True, 'message': '用户创建成功', 'user': user}
                
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建用户失败: {str(e)}")
            return {'status': False, 'message': '创建用户失败'}
    
    @staticmethod
    def validate_password(password):
        """
        验证密码是否符合要求
        :param password: 密码
        :return: 验证结果和错误消息
        """
        if not password:
            return {'success': False, 'message': '密码不能为空'}
        
        if len(password) < 6:
            return {'success': False, 'message': '长度至少6位，必须包含字母和数字'}
        
        if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
            return {'success': False, 'message': '长度至少6位，必须包含字母和数字'}
        
        return {'success': True, 'message': '密码验证通过'}

    def update_user(self, user_id, username=None, email=None, password=None, nickname=None, is_active=None, role_ids=None):
        """更新用户信息
        
        Args:
            user_id: 用户ID
            username: 用户名
            email: 邮箱
            password: 密码
            nickname: 昵称
            is_active: 是否激活
            role_ids: 角色ID列表
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'status': False, 'message': '用户不存在'}
                
            # 检查是否是超级管理员用户
            if user.is_admin_user:
                # 不能修改超级管理员用户名
                if username and username != user.username:
                    return {'status': False, 'message': '不能修改超级管理员用户名'}
                
                # 不能将超级管理员用户与非超级管理员角色关联
                if role_ids is not None:
                    from app.models.role import Role
                    super_admin_role = Role.query.filter_by(name='super_admin').first()
                    if not super_admin_role or str(super_admin_role.id) not in [str(rid) for rid in role_ids]:
                        return {'status': False, 'message': '超级管理员用户必须具有超级管理员角色'}
            else:
                # 非超级管理员用户不能使用admin用户名
                if username and User.is_admin_username(username) and username != user.username:
                    return {'status': False, 'message': '不能使用保留的用户名'}
                
                # 更新用户名（非超级管理员）
                if username and username != user.username:
                    # 检查用户名是否已存在
                    if User.query.filter_by(username=username).first():
                        return {'status': False, 'message': '用户名已存在'}
                    user.username = username
                
                # 设置激活状态
                if is_active is not None:
                    user.is_active = bool(is_active)
                
                # 更新角色（非超级管理员）
                if role_ids is not None:
                    # 将字符串ID转换为整数
                    role_ids = [int(rid) for rid in role_ids if rid]
                    
                    # 超级管理员角色检查
                    from app.models.role import Role
                    super_admin_role = Role.query.filter_by(name='super_admin').first()
                    if super_admin_role and super_admin_role.id in role_ids:
                        # 检查是否尝试将超级管理员角色分配给普通用户
                        if not user.is_admin_user:
                            # 获取当前超级管理员用户
                            admin_user = User.get_admin_user()
                            if admin_user:
                                current_app.logger.warning(f'尝试将超级管理员角色分配给普通用户 {user.username}')
                                return {'status': False, 'message': '超级管理员角色已分配给专用账号，不能分配给其他用户'}
                    
                    # 添加调试日志
                    current_app.logger.debug(f'更新用户角色，用户ID={user_id}，角色ID列表={role_ids}')
                    
                    # 获取选中的角色
                    selected_roles = Role.query.filter(Role.id.in_(role_ids)).all()
                    current_app.logger.debug(f'找到 {len(selected_roles)} 个角色: {[r.name for r in selected_roles]}')
                    
                    # 更新用户的角色
                    user.roles = selected_roles
            
            # 验证邮箱唯一性
            if email and email != user.email:
                if User.query.filter_by(email=email).first():
                    return {'status': False, 'message': '邮箱已存在'}
                user.email = email
                
            # 更新昵称
            if nickname is not None:
                user.nickname = nickname
                
            # 更新密码
            if password:
                # 验证密码格式
                result = self.validate_password(password)
                if not result['success']:
                    return {'status': False, 'message': result['message']}
                user.set_password(password)
            
            # 更新时间
            user.updated_at = datetime.now(UTC)
            
            # 保存更改
            db.session.commit()
            
            return {'status': True, 'message': '更新成功', 'user': user}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'更新用户失败: {str(e)}')
            return {'status': False, 'message': '更新失败'}
    
    def get_user_stats(self, user_id):
        """获取用户统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 包含用户统计信息的字典
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'status': False, 'message': '用户不存在'}
            
            stats = {
                'posts_count': user.posts.count(),
                'comments_count': user.comments.count(),
                'roles_count': len(user.roles),
                'last_login': user.last_login,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'is_super_admin': user.is_super_admin
            }
            
            return {'status': True, 'stats': stats}
            
        except Exception as e:
            current_app.logger.error(f'获取用户统计信息失败: {str(e)}')
            return {'status': False, 'message': '获取用户统计信息失败'}
    
    def validate_user_data(self, username=None, email=None, password=None, nickname=None):
        """验证用户数据
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            nickname: 昵称
            
        Returns:
            dict: 验证结果
        """
        try:
            # 验证用户名
            if username:
                if len(username) < 3:
                    return {'status': False, 'message': '用户名长度不能小于3个字符'}
                    
                if not re.match(r'^[a-zA-Z0-9_]+$', username):
                    return {'status': False, 'message': '用户名只能包含字母、数字和下划线'}
                    
                if username in ['admin', 'superadmin', 'administrator']:
                    return {'status': False, 'message': '不能使用系统保留的用户名'}
            
            # 验证邮箱
            if email:
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                    return {'status': False, 'message': '请输入有效的邮箱地址'}
            
            # 验证密码
            if password:
                result = self.validate_password(password)
                if not result['success']:
                    return {'status': False, 'message': result['message']}
            
            # 验证昵称
            if nickname:
                if len(nickname) < 2:
                    return {'status': False, 'message': '昵称长度不能小于2个字符'}
                    
                if len(nickname) > 20:
                    return {'status': False, 'message': '昵称长度不能超过20个字符'}
            
            return {'status': True, 'message': '验证通过'}
            
        except Exception as e:
            current_app.logger.error(f'验证用户数据失败: {str(e)}')
            return {'status': False, 'message': '验证用户数据失败'}
    
    def can_delete_user(self, current_user, target_user):
        """检查当前用户是否可以删除目标用户
        
        Args:
            current_user: 当前登录用户
            target_user: 要删除的目标用户
            
        Returns:
            bool: 是否可以删除
        """
        # 不能删除超级管理员
        if target_user.username == 'admin' or target_user.is_super_admin or target_user.is_admin_user or any(role.name == 'super_admin' for role in target_user.roles):
            return False
            
        # 不能删除自己
        if current_user.id == target_user.id:
            return False
            
        # 超级管理员可以删除任何用户（除了自己和其他超级管理员）
        if current_user.username == 'admin':
            return True
            
        # 检查当前用户是否是管理员
        is_admin = any(role.name == 'admin' for role in current_user.roles)
        if not is_admin:
            return False
            
        # 管理员只能删除普通用户
        target_is_admin = any(role.name == 'admin' for role in target_user.roles)
        return not target_is_admin
    
    def delete_user(self, user_id):
        """删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # 不能删除超级管理员用户
            if user.is_admin_user or user.is_super_admin or user.username == 'admin' or any(role.name == 'super_admin' for role in user.roles):
                current_app.logger.warning(f'尝试删除超级管理员用户: {user.username}')
                return False
                
            # 开始事务
            db.session.begin_nested()
            
            try:
                # 删除用户的操作日志
                from app.models.operation_log import OperationLog
                OperationLog.query.filter_by(user_id=user_id).delete()
                
                # 删除用户的评论
                from app.models.comment import Comment
                Comment.query.filter_by(user_id=user_id).delete()
                
                # 删除用户的文章
                from app.models.post import Post
                # 先删除文章的标签关联
                posts = Post.query.filter_by(author_id=user_id).all()
                for post in posts:
                    post.tags = []
                # 再删除文章
                Post.query.filter_by(author_id=user_id).delete()
                
                # 删除用户角色关系
                user.roles = []
                
                # 删除用户
                db.session.delete(user)
                
                # 提交嵌套事务
                db.session.commit()
                return True
                
            except Exception as e:
                # 回滚嵌套事务
                db.session.rollback()
                raise e
                
        except Exception as e:
            current_app.logger.error(f'删除用户失败: {str(e)}')
            # 回滚主事务
            db.session.rollback()
            return False
    
    def get_user(self, user_id):
        """获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'status': 'error', 'message': '用户不存在'}
                
            return {'status': 'success', 'user': user}
            
        except Exception as e:
            current_app.logger.error(f"获取用户失败: {str(e)}")
            return {'status': 'error', 'message': '获取用户失败，请稍后重试'}
    
    def get_users(self, page=1, per_page=10, current_user=None, status=None, role=None, search=None):
        """获取用户列表
        
        Args:
            page: 页码
            per_page: 每页数量
            current_user: 当前登录用户
            status: 用户状态筛选（active/inactive）
            role: 角色筛选
            search: 搜索关键词
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            query = User.query
            
            # 如果不是超级管理员，不显示超级管理员用户
            if not current_user or not current_user.is_super_admin:
                query = query.filter(~User.roles.any(Role.name == 'super_admin'))
            
            # 状态筛选
            if status:
                if status == 'active':
                    query = query.filter(User.is_active == True)
                elif status == 'inactive':
                    query = query.filter(User.is_active == False)
            
            # 角色筛选
            if role:
                query = query.filter(User.roles.any(Role.name == role))
            
            # 搜索过滤
            if search:
                search = f'%{search}%'
                query = query.filter(
                    db.or_(
                        User.username.ilike(search),
                        User.email.ilike(search),
                        User.nickname.ilike(search)
                    )
                )
            
            # 执行分页查询
            pagination = query.order_by(User.created_at.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            # 获取用户统计信息
            stats = {
                'total': User.query.count(),
                'active': User.query.filter_by(is_active=True).count(),
                'inactive': User.query.filter_by(is_active=False).count(),
                'admin': len(User.get_admin_users()),
                'super_admin': len(User.get_super_admin_users())
            }
            
            return {
                'status': 'success',
                'users': pagination.items,
                'pagination': pagination,
                'stats': stats
            }
            
        except Exception as e:
            current_app.logger.error(f"获取用户列表失败: {str(e)}")
            current_app.logger.exception(e)
            return {'status': 'error', 'message': '获取用户列表失败'}
    
    def get_user_details(self, user_id):
        """获取用户详细信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 包含用户详细信息的字典
        """
        try:
            user = User.query.get(user_id)
            if not user:
                current_app.logger.warning(f'获取用户详细信息失败: 用户 {user_id} 不存在')
                return {'status': False, 'message': '用户不存在'}
            
            # 获取用户基本信息
            user_info = user.to_dict()
            
            # 获取用户统计信息
            stats = {
                'posts_count': user.posts.count(),
                'comments_count': user.comments.count(),
                'roles_count': len(user.roles),
                'last_login': user.last_login,
                'created_at': user.created_at,
                'updated_at': user.updated_at
            }
            
            # 获取用户角色信息
            roles = [{
                'id': role.id,
                'name': role.name,
                'description': role.description
            } for role in user.roles]
            
            # 获取用户最近的操作日志
            from app.models.operation_log import OperationLog
            recent_logs = OperationLog.query.filter_by(user_id=user_id)\
                .order_by(OperationLog.created_at.desc())\
                .limit(5)\
                .all()
            
            logs = [{
                'action': log.action,
                'details': log.details,
                'created_at': log.created_at,
                'data': log.data
            } for log in recent_logs]
            
            # 获取用户最近的文章
            recent_posts = user.posts.order_by(Post.created_at.desc()).limit(5).all()
            posts = [{
                'id': post.id,
                'title': post.title,
                'created_at': post.created_at,
                'status': post.status
            } for post in recent_posts]
            
            # 获取用户最近的评论
            recent_comments = user.comments.order_by(Comment.created_at.desc()).limit(5).all()
            comments = [{
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at,
                'status': comment.status
            } for comment in recent_comments]
            
            return {
                'status': True,
                'user': user_info,
                'stats': stats,
                'roles': roles,
                'recent_logs': logs,
                'recent_posts': posts,
                'recent_comments': comments
            }
            
        except Exception as e:
            current_app.logger.error(f'获取用户详细信息失败: {str(e)}')
            current_app.logger.exception(e)
            return {'status': False, 'message': '获取用户详细信息失败'}
    
    def verify_password(self, user_id, password):
        """验证用户密码
        
        Args:
            user_id: 用户ID
            password: 密码
            
        Returns:
            bool: 密码是否正确
        """
        user = db.session.get(User, user_id)
        if not user:
            return False
            
        return check_password_hash(user.password, password)
    
    def get_user_by_username(self, username):
        """根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            dict: 包含用户信息和状态的字典
        """
        if not username:
            return {'success': False, 'message': '用户名不能为空'}
            
        try:
            user = User.query.filter_by(username=username).first()
            if not user:
                return {'success': False, 'message': '用户不存在'}
                
            # 检查用户状态
            if not user.is_active:
                current_app.logger.warning(f'禁用账号尝试登录: {username}')
                return {'success': False, 'message': '您的账号已被禁用，请联系管理员'}
                
            return {'success': True, 'message': '获取用户成功', 'user': user}
            
        except Exception as e:
            current_app.logger.error(f"获取用户失败: {str(e)}")
            return {'success': False, 'message': '获取用户失败'}
    
    def get_user_by_email(self, email):
        """根据邮箱获取用户
        
        Args:
            email: 邮箱
            
        Returns:
            User: 用户对象
        """
        return User.query.filter_by(email=email).first()
    
    def search_users(self, keyword, page=1, per_page=10):
        """搜索用户
        
        Args:
            keyword: 关键词
            page: 页码
            per_page: 每页数量
            
        Returns:
            dict: 包含分页信息的字典
        """
        try:
            # 初始化查询
            query = User.query
            
            # 关键词搜索
            if keyword:
                keyword = f'%{keyword}%'
                query = query.filter(
                    db.or_(
                        User.username.ilike(keyword),
                        User.email.ilike(keyword),
                        User.nickname.ilike(keyword)
                    )
                )
            
            # 执行分页查询
            pagination = query.order_by(User.created_at.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            # 获取统计信息
            stats = {
                'total': query.count(),
                'active': query.filter(User.is_active == True).count(),
                'inactive': query.filter(User.is_active == False).count()
            }
            
            # 获取角色统计
            role_stats = {}
            for role in Role.query.all():
                role_stats[role.name] = query.filter(User.roles.any(Role.name == role.name)).count()
            
            # 获取最近注册用户统计
            from datetime import datetime, timedelta
            now = datetime.now()
            recent_stats = {
                'today': query.filter(User.created_at >= now.replace(hour=0, minute=0, second=0, microsecond=0)).count(),
                'this_week': query.filter(User.created_at >= (now - timedelta(days=7))).count(),
                'this_month': query.filter(User.created_at >= (now - timedelta(days=30))).count()
            }
            
            return {
                'status': True,
                'items': pagination.items,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next,
                    'prev_num': pagination.prev_num,
                    'next_num': pagination.next_num
                },
                'stats': stats,
                'role_stats': role_stats,
                'recent_stats': recent_stats
            }
            
        except Exception as e:
            current_app.logger.error(f'搜索用户失败: {str(e)}')
            current_app.logger.exception(e)
            return {'status': False, 'message': '搜索用户失败'}
    
    def get_global_user_stats(self):
        """获取用户统计信息（所有用户）"""
        return {
            'total': User.query.count(),
            'active': User.query.filter_by(is_active=True).count(),
            'inactive': User.query.filter_by(is_active=False).count()
        }
        
    def get_default_user_stats(self):
        """获取默认的用户统计信息"""
        return {
            'total_users': 0,
            'active_users': 0
        }

    def get_user_by_id(self, user_id):
        """根据ID获取用户"""
        return User.query.get(user_id)
        
    def is_admin(self, user):
        """检查用户是否是管理员
        
        Args:
            user: 用户对象
            
        Returns:
            bool: 是否是管理员
        """
        if hasattr(user, 'is_admin') and user.is_admin:
            return True
            
        if hasattr(user, 'roles'):
            return any(role.name == 'admin' for role in user.roles)
            
        return False
        
    def check_password(self, user, password):
        """检查密码是否正确
        
        Args:
            user: 用户对象
            password: 明文密码
            
        Returns:
            bool: 密码是否正确
        """
        if hasattr(user, 'check_password'):
            return user.check_password(password)
            
        if hasattr(user, 'password'):
            return check_password_hash(user.password, password)
            
        return False 