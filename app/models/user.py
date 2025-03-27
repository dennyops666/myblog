"""
文件名：user.py
描述：用户模型
作者：denny
创建日期：2024-03-21
"""

from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC
from app.models.permission import Permission
from sqlalchemy import desc

# 从role模块导入user_roles表
from app.models.role import user_roles, Role

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    __table_args__ = (
        db.Index('idx_user_username', 'username'),
        db.Index('idx_user_email', 'email'),
        db.UniqueConstraint('username', name='uq_user_username'),
        db.UniqueConstraint('email', name='uq_user_email'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    nickname = db.Column(db.String(64), nullable=True)
    avatar = db.Column(db.String(200), nullable=True, default='/static/images/default-avatar.png')
    bio = db.Column(db.Text, nullable=True, default='')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin_user = db.Column(db.Boolean, default=False, nullable=False, index=True)  # 标记超级管理员用户
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now(UTC), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC), nullable=False)
    # 关系
    # 用户角色关系
    roles = db.relationship(
        'Role',
        secondary=user_roles,
        back_populates='users',
        lazy='joined',  # 总是加载角色，因为权限检查频繁
        order_by='Role.name',
        cascade='save-update, merge',
        passive_deletes=True,
        collection_class=list
    )
    
    # 用户文章关系
    posts = db.relationship(
        'Post',
        backref=db.backref('author', lazy=True),
        lazy=True,  # 按需加载文章
        cascade='all, delete-orphan',
        order_by='desc(Post.created_at)'
    )
    
    # 用户评论关系
    comments = db.relationship(
        'Comment',
        back_populates='author',
        lazy='dynamic',  # 动态加载评论，支持过滤和分页
        cascade='all, delete-orphan',
        foreign_keys='Comment.author_id',
        order_by='desc(Comment.created_at)'
    )
    
    # 用户操作日志关系
    operation_logs = db.relationship(
        'OperationLog',
        back_populates='user',
        lazy='dynamic',  # 动态加载日志，支持过滤和分页
        cascade='all, delete-orphan',
        order_by='OperationLog.created_at.desc()'
    )
    
    @property
    def password(self):
        raise AttributeError('密码不是可读属性')
        
    @password.setter
    def password(self, password):
        self.set_password(password)
    
    @property
    def is_super_admin(self):
        """判断用户是否是超级管理员"""
        return self.has_role('super_admin') or self.is_admin_user
    
    def set_password(self, password):
        """设置用户密码
        
        Args:
            password: 明文密码，将被哈希存储
            
        Raises:
            ValueError: 当密码为空或不是字符串时抛出
        """
        if not password or not isinstance(password, str):
            raise ValueError('密码不能为空且必须是字符串')
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """验证用户密码
        
        Args:
            password: 要验证的明文密码
            
        Returns:
            bool: 如果密码正确返回 True，否则返回 False
            
        Raises:
            ValueError: 当密码为空或不是字符串时抛出
        """
        if not password or not isinstance(password, str):
            raise ValueError('密码不能为空且必须是字符串')
        return check_password_hash(self.password_hash, password)
        
    # 别名方法，为了兼容性保留
    check_password = verify_password
        
    def has_role(self, role_name):
        """检查用户是否有指定角色
        
        Args:
            role_name: 角色名称
            
        Returns:
            bool: 如果用户有指定角色返回 True，否则返回 False
            
        Raises:
            ValueError: 当角色名为空或不是字符串时抛出
        """
        if not role_name or not isinstance(role_name, str):
            raise ValueError('角色名不能为空且必须是字符串')
        return any(role.name == role_name for role in self.roles)
        
    def has_permission(self, permission):
        """检查用户是否有指定权限
        
        Args:
            permission: 权限值，可以是 Permission 枚举或整数
            
        Returns:
            bool: 如果用户有指定权限返回 True，否则返回 False
        """
        if not self.roles:
            return False
        if isinstance(permission, Permission):
            permission = permission.value
        return any(role.has_permission(permission) for role in self.roles)
        
    def add_role(self, role):
        """添加角色
        
        Args:
            role: Role 实例
            
        Raises:
            ValueError: 当角色实例为 None 时抛出
            TypeError: 当角色不是 Role 类型时抛出
        """
        if role is None:
            raise ValueError('角色不能为 None')
        if not isinstance(role, Role):
            raise TypeError('角色必须是 Role 类型')
            
        if not self.has_role(role.name):
            self.roles.append(role)
            
    def remove_role(self, role):
        """移除角色
        
        Args:
            role: Role 实例
            
        Raises:
            ValueError: 当角色实例为 None 时抛出
            TypeError: 当角色不是 Role 类型时抛出
        """
        if role is None:
            raise ValueError('角色不能为 None')
        if not isinstance(role, Role):
            raise TypeError('角色必须是 Role 类型')
            
        if self.has_role(role.name):
            self.roles.remove(role)
            
    def set_active_status(self, status):
        """设置用户活动状态
        
        Args:
            status: 状态值，会被转换为布尔值
            
        Note:
            该方法会将任何输入值转换为布尔值。
            如果需要更精确的控制，请使用 activate() 或 deactivate()。
        """
        self.is_active = bool(status)
            
    def activate(self):
        """激活用户
        
        这是设置用户状态为活跃的推荐方法。
        """
        self.is_active = True
        
    def deactivate(self):
        """停用用户
        
        这是设置用户状态为非活跃的推荐方法。
        停用的用户将无法登录或进行任何操作。
        """
        self.is_active = False
            
    @property
    def is_admin(self):
        """判断用户是否是管理员
        
        Returns:
            bool: 如果用户是管理员或超级管理员返回 True，否则返回 False
            
        Note:
            该属性会检查用户是否有 'Admin' 角色或是超级管理员。
            超级管理员自动拥有管理员权限。
        """
        return self.has_role('Admin') or self.is_super_admin
    
    @property
    def display_name(self):
        """获取用户显示名称
        
        Returns:
            str: 用户的显示名称，如果设置了昵称则返回昵称，
                否则返回用户名
            
        Note:
            该属性优先返回用户设置的昵称，如果没有设置昵称，
            则返回用户名。
        """
        return self.nickname or self.username
    
    @property
    def avatar_url(self):
        """获取用户头像URL
        
        Returns:
            str: 用户头像的URL，如果没有设置头像则返回默认头像URL
            
        Note:
            该属性直接返回 avatar 字段的值，因为在模型定义中已经
            设置了默认值为 '/static/images/default-avatar.png'。
        """
        return self.avatar
    
    def to_dict(self):
        """将用户信息转换为字典
        
        Returns:
            dict: 包含用户信息的字典，包含以下字段:
                - id: 用户ID
                - username: 用户名
                - email: 邮箱
                - nickname: 昵称
                - avatar: 头像URL
                - bio: 个人简介
                - is_active: 是否活跃
                - is_admin: 是否管理员
                - is_super_admin: 是否超级管理员
                - created_at: 创建时间（ISO格式）
                - updated_at: 更新时间（ISO格式）
                - stats: 用户统计信息
                    - posts: 文章统计
                        - total: 总数
                        - published: 已发布数
                        - draft: 草稿数
                    - comments: 评论统计
                        - total: 总数
                        - approved: 已通过数
                        - pending: 待审核数
                    - roles: 角色统计
                        - total: 总数
                        - names: 角色名称列表
            
        Note:
            该方法会查询数据库以获取用户的文章、评论和角色统计信息。
            如果只需要基本信息，可以使用 to_simple_dict() 方法。
        """
        base_dict = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nickname': self.nickname,
            'avatar': self.avatar_url,
            'bio': self.bio,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'is_super_admin': self.is_super_admin,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'stats': {
                'posts': {
                    'total': 0,
                    'published': 0,
                    'draft': 0
                },
                'comments': {
                    'total': 0,
                    'approved': 0,
                    'pending': 0
                },
                'roles': {
                    'total': len(self.roles),
                    'names': [role.name for role in self.roles]
                }
            }
        }
        
        # 尝试获取文章统计信息
        try:
            base_dict['stats']['posts'].update({
                'total': self.posts.count(),
                'published': self.posts.filter_by(status='published').count(),
                'draft': self.posts.filter_by(status='draft').count()
            })
        except Exception:
            pass
            
        # 尝试获取评论统计信息
        try:
            base_dict['stats']['comments'].update({
                'total': self.comments.count(),
                'approved': self.comments.filter_by(status='approved').count(),
                'pending': self.comments.filter_by(status='pending').count()
            })
        except Exception:
            pass
            
        return base_dict
            
    def to_simple_dict(self):
        """将用户基本信息转换为字典
        
        Returns:
            dict: 包含用户基本信息的字典，不包含统计信息
            
        Note:
            该方法只返回用户的基本信息，不查询数据库，
            适用于只需要基本信息的场景。
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nickname': self.nickname,
            'avatar': self.avatar_url,
            'bio': self.bio,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'is_super_admin': self.is_super_admin,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @property
    def status(self):
        """获取用户状态
        
        Returns:
            str: 用户状态，可能的值为:
                - 'inactive': 用户未激活
                - 'super_admin': 超级管理员
                - 'admin': 管理员
                - 'active': 普通活跃用户
        """
        if not self.is_active:
            return 'inactive'
        if self.is_super_admin:
            return 'super_admin'
        if self.is_admin:
            return 'admin'
        return 'active'
    
    @classmethod
    def get_active_users(cls):
        """获取所有活跃用户
        
        Returns:
            Query: 活跃用户查询对象，按创建时间降序排序
        """
        return cls.query.filter_by(is_active=True).order_by(cls.created_at.desc())
        
    @classmethod
    def get_by_username(cls, username):
        """根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            User | None: 找到的用户实例或 None
        """
        return cls.query.filter_by(username=username).first()
        
    @classmethod
    def get_by_email(cls, email):
        """根据邮箱获取用户
        
        Args:
            email: 邮箱地址
            
        Returns:
            User | None: 找到的用户实例或 None
        """
        return cls.query.filter_by(email=email).first()
        
    @classmethod
    def get_users_by_role(cls, role_name):
        """根据角色名获取用户
        
        Args:
            role_name: 角色名称
            
        Returns:
            list[User]: 具有指定角色的用户列表
        """
        role = Role.query.filter_by(name=role_name).first()
        return role.users if role else []
        
    @classmethod
    def get_admin_users(cls):
        """获取所有管理员用户
        
        Returns:
            list[User]: 管理员用户列表
        """
        return cls.get_users_by_role('admin')
    
    @classmethod
    def get_super_admin_users(cls):
        """获取所有超级管理员用户
        
        Returns:
            list[User]: 超级管理员用户列表
        """
        return cls.get_users_by_role('super_admin')
        
    @classmethod
    def create_user(cls, username, email, password, roles=None, **kwargs):
        """创建新用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            roles: 角色列表，可选
            **kwargs: 其他可选字段
            
        Returns:
            User: 新创建的用户实例
            
        Raises:
            ValueError: 当用户名或邮箱已存在时抛出
        """
        user = cls(username=username, email=email, **kwargs)
        user.set_password(password)
        
        if roles:
            user.roles.extend(roles)
        
        db.session.add(user)
        return user
            
    def update_profile(self, **kwargs):
        """更新用户信息
        
        Args:
            **kwargs: 要更新的字段及其值
            
        Raises:
            ValueError: 当尝试更新受保护的字段或无效字段时抛出
        """
        protected_fields = {'id', 'username', 'email', 'password', 'roles', 'created_at', 'is_active'}
        invalid_fields = set(kwargs) - set(self.__table__.columns.keys())
        protected_updates = set(kwargs) & protected_fields
        
        if invalid_fields:
            raise ValueError(f'无效的字段：{invalid_fields}')
        if protected_updates:
            raise ValueError(f'不允许更新受保护的字段：{protected_updates}')
        
        for key, value in kwargs.items():
            setattr(self, key, value)
    def __init__(self, **kwargs):
        """初始化用户实例
        
        Args:
            **kwargs: 用户属性字典
        """
        # 先设置默认值
        self.nickname = kwargs.get('username')
        self.avatar = '/static/images/default-avatar.png'
        self.bio = ''
        self.roles = []
        
        # 再调用父类的 __init__，覆盖默认值
        super(User, self).__init__(**kwargs)
            
    def __repr__(self):
        """返回用户实例的字符串表示
        
        Returns:
            str: 用户实例的字符串表示
        """
        return f'<User {self.username}>'

    def get_id(self):
        """返回用户ID的字符串表示
        
        Returns:
            str: 用户ID的字符串表示
        """
        return str(self.id)

    @property
    def is_authenticated(self):
        """检查用户是否已认证
        
        Returns:
            bool: 如果用户已认证返回 True，否则返回 False
        """
        return True
    
    @property
    def is_anonymous(self):
        """检查是否是匿名用户
        
        Returns:
            bool: 总是返回 False，因为这是一个已注册的用户
        """
        return False

    def can_modify_username(self):
        """判断是否可以修改用户名
        
        超级管理员用户admin不能修改用户名
        """
        return not self.is_admin_user
    
    def can_modify_roles(self):
        """判断是否可以修改角色
        
        超级管理员用户admin不能修改角色
        """
        return not self.is_admin_user
    
    @classmethod
    def get_admin_user(cls):
        """获取超级管理员用户"""
        try:
            return cls.query.filter_by(is_admin_user=True).first()
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"获取超级管理员用户时出错: {str(e)}")
            # 如果字段不存在，尝试按用户名查找
            return cls.query.filter_by(username='admin').first()
    
    @classmethod
    def is_admin_username(cls, username):
        """判断是否是超级管理员用户名"""
        return username.lower() == 'admin'
        
    @classmethod
    def create_admin_user_if_not_exists(cls):
        """如果不存在超级管理员用户，则创建"""
        from app.models.role import Role
        from flask import current_app
        
        try:
            # 检查是否已存在超级管理员用户
            admin_user = cls.get_admin_user() or cls.query.filter_by(username='admin').first()
            if admin_user:
                # 如果数据库还没有is_admin_user字段，则此时无法设置
                try:
                    admin_user.is_admin_user = True
                except:
                    pass
                return admin_user
            
            # 获取超级管理员角色
            super_admin_role = Role.query.filter_by(name='super_admin').first()
            if not super_admin_role:
                super_admin_role = Role.query.filter_by(name='Admin').first()
                if not super_admin_role:
                    current_app.logger.error('创建超级管理员用户失败: 超级管理员角色不存在')
                    return None
            
            # 创建超级管理员用户
            admin_user = cls(
                username='admin',
                email='admin@example.com',
                nickname='系统管理员',
                is_active=True
            )
            
            # 尝试设置is_admin_user字段，如果不存在则忽略
            try:
                admin_user.is_admin_user = True
            except:
                pass
            
            admin_user.set_password('admin123')  # 设置初始密码
            admin_user.roles = [super_admin_role]
            
            try:
                from app.extensions import db
                db.session.add(admin_user)
                db.session.commit()
                current_app.logger.info('成功创建超级管理员用户')
                return admin_user
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'创建超级管理员用户失败: {str(e)}')
                return None
        except Exception as e:
            current_app.logger.error(f'创建超级管理员用户过程中发生错误: {str(e)}')
            return None