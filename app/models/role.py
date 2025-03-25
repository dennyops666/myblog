"""

文件名：role.py
描述：角色模型
作者：denny
创建日期：2024-03-21
"""

from app.extensions import db
from datetime import datetime, UTC
from app.models.permission import Permission
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

# 用户角色关联表
user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE', name='fk_user_roles_user_id')),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE', name='fk_user_roles_role_id')),
    db.Column('created_at', db.DateTime, default=lambda: datetime.now(UTC), nullable=False),
    db.Index('idx_user_roles_user_id', 'user_id'),
    db.Index('idx_user_roles_role_id', 'role_id'),
    db.UniqueConstraint('user_id', 'role_id', name='uq_user_roles_user_role'),
    info={'bind_key': None},  # 使用默认数据库
    extend_existing=True
)

class Role(db.Model):
    """角色模型"""
    __tablename__ = 'roles'
    __table_args__ = (
        db.Index('idx_role_name', 'name'),
        db.UniqueConstraint('name', name='uq_role_name'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.String(256), nullable=True)
    permissions = db.Column(db.Integer, nullable=False, default=0)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # 用户关联
    users = db.relationship('User', secondary=user_roles,
                           back_populates='roles',
                           lazy='dynamic',
                           cascade='save-update, merge',
                           passive_deletes=True,
                           order_by='User.username')
    
    def __init__(self, **kwargs):
        # 验证角色名称
        if 'name' in kwargs:
            if not Role.validate_role_naming(kwargs['name']):
                raise ValueError(f'角色名称无效: {kwargs["name"]}')
        
        # 验证权限值
        if 'permissions' in kwargs:
            if not isinstance(kwargs['permissions'], int) or kwargs['permissions'] < 0:
                raise ValueError(f'权限值无效: {kwargs["permissions"]}')
        
        # 设置默认值
        kwargs.setdefault('permissions', 0)
        kwargs.setdefault('description', '')
        kwargs.setdefault('is_default', False)
        
        # 设置时间戳
        now = datetime.now(UTC)
        kwargs.setdefault('created_at', now)
        kwargs.setdefault('updated_at', now)
        
        # 调用父类初始化
        super(Role, self).__init__(**kwargs)
        
        # 初始化用户关联
        if 'users' not in kwargs:
            self.users = []
            
    def get_users(self, active_only=True):
        """获取角色的用户列表"""
        try:
            query = self.users
            if active_only:
                query = query.filter_by(is_active=True)
            users = query.order_by('User.username').all()
            current_app.logger.info(f'获取角色 {self.name} 的用户列表，数量: {len(users)}')
            return users
        except Exception as e:
            current_app.logger.error(f'获取角色 {self.name} 的用户列表失败: {str(e)}')
            return []
    
    def add_user(self, user):
        """添加用户到角色"""
        try:
            # 检查用户是否有效
            if not hasattr(user, 'id') or not user.id:
                current_app.logger.error(f'无法添加无效用户到角色 {self.name}')
                return False
            
            # 检查用户是否已在角色中
            if user in self.users:
                current_app.logger.warning(f'用户 {user.username} 已在角色 {self.name} 中')
                return True
            
            # 添加用户
            self.users.append(user)
            self.updated_at = datetime.now(UTC)
            db.session.commit()
            
            current_app.logger.info(f'将用户 {user.username} 添加到角色 {self.name}')
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'添加用户到角色 {self.name} 失败: {str(e)}')
            return False
    
    def remove_user(self, user):
        """从角色中移除用户"""
        try:
            # 检查用户是否有效
            if not hasattr(user, 'id') or not user.id:
                current_app.logger.error(f'无法从角色 {self.name} 中移除无效用户')
                return False
            
            # 检查用户是否在角色中
            if user not in self.users:
                current_app.logger.warning(f'用户 {user.username} 不在角色 {self.name} 中')
                return True
            
            # 移除用户
            self.users.remove(user)
            self.updated_at = datetime.now(UTC)
            db.session.commit()
            
            current_app.logger.info(f'从角色 {self.name} 中移除用户 {user.username}')
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'从角色 {self.name} 中移除用户失败: {str(e)}')
            return False
    
    def clear_users(self):
        """清除角色的所有用户"""
        try:
            # 获取当前用户数量
            users_count = self.users.count()
            
            # 清除用户
            self.users = []
            self.updated_at = datetime.now(UTC)
            db.session.commit()
            
            current_app.logger.info(f'清除角色 {self.name} 的所有用户，共 {users_count} 个')
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'清除角色 {self.name} 的用户失败: {str(e)}')
            return False
    
    @classmethod
    def validate_role_naming(cls, name):
        """验证角色名称
        
        规则:
        1. 长度在3-64个字符之间
        2. 只能包含字母、数字
        3. 不能与系统保留字重名
        4. 必须以字母开头
        """
        try:
            # 检查基本条件
            if not name or not isinstance(name, str):
                return False
            
            # 检查长度
            name_length = len(name)
            if name_length < 3 or name_length > 64:
                return False
            
            # 检查格式
            import re
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
                return False
            
            # 检查保留字
            reserved_names = {
                'role', 'root', 'system',
                'anonymous', 'default', 'test', 'temp', 'tmp'
            }
            if name.lower() in reserved_names:
                return False
            
            return True
            
        except Exception as e:
            current_app.logger.error(f'验证角色 {name} 的命名时发生错误: {str(e)}')
            return False
    
    def validate_user_distribution(self):
        """验证用户分布
        
        检查点:
        1. 总用户数不能超过限制
        2. 活跃用户比例不能过低
        3. 权限级别与用户数量的合理性
        """
        try:
            # 获取用户统计
            total_users = self.users.count()
            active_users = self.users.filter_by(is_active=True).count()
            
            # 检查总用户数
            if total_users > current_app.config.get('MAX_USERS_PER_ROLE', 1000):
                current_app.logger.warning(f'角色 {self.name} 的用户数量 ({total_users}) 超过限制')
                return False
            
            # 检查活跃用户比例
            if total_users > 0:
                active_ratio = active_users / total_users
                min_ratio = current_app.config.get('MIN_ACTIVE_USER_RATIO', 0.1)
                if active_ratio < min_ratio:
                    current_app.logger.warning(
                        f'角色 {self.name} 的活跃用户比例 ({active_ratio:.2%}) '
                        f'低于最小要求 ({min_ratio:.2%})'
                    )
                    return False
            
            # 检查权限级别与用户数量的合理性
            if self.permissions & Permission.SUPER_ADMIN.value:
                max_super_admins = current_app.config.get('MAX_SUPER_ADMINS', 3)
                if total_users > max_super_admins:
                    current_app.logger.warning(
                        f'超级管理员角色 {self.name} 的用户数量 ({total_users}) '
                        f'超过限制 ({max_super_admins})'
                    )
                    return False
            
            return True
        except Exception as e:
            current_app.logger.error(f'验证角色 {self.name} 的用户分布失败: {str(e)}')
            return False
    
    def check_permission_inheritance(self, parent_role):
        """检查权限继承关系
        
        检查点:
        1. 父角色必须具有更高的权限
        2. 不能形成循环继承
        3. 继承链不能过长
        """
        try:
            # 检查父角色是否有效
            if not isinstance(parent_role, Role) or not parent_role.id:
                current_app.logger.error(f'父角色无效: {parent_role}')
                return False
            
            # 检查权限级别
            if parent_role.permissions <= self.permissions:
                current_app.logger.warning(
                    f'父角色 {parent_role.name} 的权限 ({parent_role.permissions}) '
                    f'不高于当前角色 {self.name} 的权限 ({self.permissions})'
                )
                return False
            
            # 检查是否形成循环
            visited_roles = {self.id}
            current_role = parent_role
            max_depth = current_app.config.get('MAX_ROLE_INHERITANCE_DEPTH', 5)
            
            for _ in range(max_depth):
                if not current_role or not current_role.id:
                    break
                
                if current_role.id in visited_roles:
                    current_app.logger.error(
                        f'检测到角色继承循环: '
                        f'{self.name} -> {parent_role.name} -> ...'
                    )
                    return False
                
                visited_roles.add(current_role.id)
                current_role = current_role.parent if hasattr(current_role, 'parent') else None
            
            if current_role:
                current_app.logger.warning(f'角色继承链过长: {self.name} -> {parent_role.name} -> ...')
                return False
            
            return True
        except Exception as e:
            current_app.logger.error(f'检查角色 {self.name} 的权限继承关系失败: {str(e)}')
            return False
    
    def update_users(self, users):
        """批量更新角色的用户列表"""
        try:
            # 验证用户列表
            if not isinstance(users, (list, tuple)):
                current_app.logger.error(f'角色 {self.name} 的用户列表类型无效: {type(users)}')
                return False
            
            # 验证每个用户
            invalid_users = []
            for user in users:
                if not hasattr(user, 'id') or not user.id:
                    invalid_users.append(user)
                    current_app.logger.error(f'检测到无效用户: {user}')
            
            if invalid_users:
                current_app.logger.error(f'角色 {self.name} 的用户列表中包含 {len(invalid_users)} 个无效用户')
                return False
            
            # 获取当前用户列表
            old_users = set(self.users)
            new_users = set(users)
            
            # 计算需要添加和移除的用户
            users_to_add = new_users - old_users
            users_to_remove = old_users - new_users
            
            # 批量更新用户
            for user in users_to_add:
                self.users.append(user)
                current_app.logger.info(f'将用户 {user.username} 添加到角色 {self.name}')
            
            for user in users_to_remove:
                self.users.remove(user)
                current_app.logger.info(f'从角色 {self.name} 中移除用户 {user.username}')
            
            # 更新时间戳并保存
            self.updated_at = datetime.now(UTC)
            db.session.commit()
            
            current_app.logger.info(
                f'更新角色 {self.name} 的用户列表成功\n'
                f'- 添加了 {len(users_to_add)} 个用户\n'
                f'- 移除了 {len(users_to_remove)} 个用户\n'
                f'- 当前共有 {len(new_users)} 个用户'
            )
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'更新角色 {self.name} 的用户列表失败: {str(e)}')
            return False
    
    def has_permission(self, permission):
        """检查是否具有指定权限"""
        try:
            if not isinstance(permission, (int, Permission)):
                current_app.logger.error(f'无效的权限类型: {type(permission)}')
                return False
            
            # 如果是 Permission 枚举，获取其值
            perm_value = permission.value if isinstance(permission, Permission) else permission
            
            # 检查权限
            has_perm = bool(self.permissions & perm_value)
            current_app.logger.debug(
                f'检查角色 {self.name} 的权限: '
                f'{perm_value} -> {"Yes" if has_perm else "No"}'
            )
            return has_perm
        except Exception as e:
            current_app.logger.error(f'检查角色 {self.name} 的权限失败: {str(e)}')
            return False
    
    def add_permission(self, permission):
        """添加指定权限"""
        try:
            if not isinstance(permission, (int, Permission)):
                current_app.logger.error(f'无效的权限类型: {type(permission)}')
                return False
            
            # 如果是 Permission 枚举，获取其值
            perm_value = permission.value if isinstance(permission, Permission) else permission
            
            # 添加权限
            old_permissions = self.permissions
            self.permissions |= perm_value
            self.updated_at = datetime.now(UTC)
            db.session.commit()
            
            current_app.logger.info(
                f'为角色 {self.name} 添加权限: '
                f'{old_permissions} -> {self.permissions}'
            )
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'为角色 {self.name} 添加权限失败: {str(e)}')
            return False
    
    def remove_permission(self, permission):
        """移除指定权限"""
        try:
            if not isinstance(permission, (int, Permission)):
                current_app.logger.error(f'无效的权限类型: {type(permission)}')
                return False
            
            # 如果是 Permission 枚举，获取其值
            perm_value = permission.value if isinstance(permission, Permission) else permission
            
            # 移除权限
            old_permissions = self.permissions
            self.permissions &= ~perm_value
            self.updated_at = datetime.now(UTC)
            db.session.commit()
            
            current_app.logger.info(
                f'从角色 {self.name} 移除权限: '
                f'{old_permissions} -> {self.permissions}'
            )
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'从角色 {self.name} 移除权限失败: {str(e)}')
            return False
    
    def reset_permissions(self):
        """重置所有权限"""
        try:
            old_permissions = self.permissions
            self.permissions = 0
            self.updated_at = datetime.now(UTC)
            db.session.commit()
            
            current_app.logger.info(
                f'重置角色 {self.name} 的所有权限: '
                f'{old_permissions} -> 0'
            )
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'重置角色 {self.name} 的权限失败: {str(e)}')
            return False
    
    def has_permission(self, permission):
        """检查是否有指定权限"""
        try:
            if not isinstance(permission, (int, Permission)):
                current_app.logger.error(f'无效的权限类型: {type(permission)}')
                return False
            
            # 如果是 Permission 枚举，获取其值
            perm_value = permission.value if isinstance(permission, Permission) else permission
            
            # 检查权限
            has_perm = bool(self.permissions & perm_value)
            current_app.logger.debug(
                f'检查角色 {self.name} 的权限: '
                f'{perm_value} -> {"Yes" if has_perm else "No"}'
            )
            return has_perm
        except Exception as e:
            current_app.logger.error(f'检查角色 {self.name} 的权限失败: {str(e)}')
            return False
    
    def add_permission(self, permission):
        """添加指定权限"""
        try:
            if not isinstance(permission, (int, Permission)):
                current_app.logger.error(f'无效的权限类型: {type(permission)}')
                return False
            
            # 如果是 Permission 枚举，获取其值
            perm_value = permission.value if isinstance(permission, Permission) else permission
            
            # 添加权限
            old_permissions = self.permissions
            self.permissions |= perm_value
            self.updated_at = datetime.now(UTC)
            db.session.commit()
            
            current_app.logger.info(
                f'为角色 {self.name} 添加权限: '
                f'{old_permissions} -> {self.permissions}'
            )
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'为角色 {self.name} 添加权限失败: {str(e)}')
            return False
    
    def remove_permission(self, permission):
        """移除指定权限"""
        try:
            if not isinstance(permission, (int, Permission)):
                current_app.logger.error(f'无效的权限类型: {type(permission)}')
                return False
            
            # 如果是 Permission 枚举，获取其值
            perm_value = permission.value if isinstance(permission, Permission) else permission
            
            # 移除权限
            old_permissions = self.permissions
            self.permissions &= ~perm_value
            self.updated_at = datetime.now(UTC)
            db.session.commit()
            
            current_app.logger.info(
                f'从角色 {self.name} 移除权限: '
                f'{old_permissions} -> {self.permissions}'
            )
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'从角色 {self.name} 移除权限失败: {str(e)}')
            return False
    
    def reset_permissions(self):
        """重置所有权限"""
        try:
            old_permissions = self.permissions
            self.permissions = 0
            self.updated_at = datetime.now(UTC)
            db.session.commit()
            
            current_app.logger.info(
                f'重置角色 {self.name} 的所有权限: '
                f'{old_permissions} -> 0'
            )
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'重置角色 {self.name} 的权限失败: {str(e)}')
            return False
            
    def get_permissions(self):
        """获取所有权限"""
        permissions = []
        for permission in Permission:
            if self.has_permission(permission):
                permissions.append(permission)
        return permissions
    
    def get_permissions_list(self):
        """获取权限列表，包含权限名称和值"""
        return [
            {
                'name': permission.name,
                'value': permission.value,
                'description': permission.description if hasattr(permission, 'description') else None
            }
            for permission in self.get_permissions()
        ]
    
    def is_valid(self):
        """检查角色是否有效"""
        try:
            # 检查是否存在于数据库中
            if not self.id:
                current_app.logger.error(f'角色 {self.name} 未保存到数据库')
                return False
            
            # 检查是否可以从数据库中查询到
            db_role = self.query.get(self.id)
            if not db_role:
                current_app.logger.error(f'无法从数据库中查询到角色 {self.name}')
                return False
            
            # 检查数据库中的角色是否与当前角色一致
            if db_role.name != self.name:
                current_app.logger.error(f'数据库中的角色名称与当前角色不一致: {db_role.name} != {self.name}')
                return False
            
            # 验证角色的所有属性
            if not self.validate():
                current_app.logger.error(f'角色 {self.name} 的属性验证失败')
                return False
            
            current_app.logger.info(f'角色 {self.name} 有效')
            return True
        except Exception as e:
            current_app.logger.error(f'检查角色 {self.name} 的有效性时发生错误: {str(e)}')
            return False
    
    def validate_name(self):
        """验证角色名称"""
        try:
            # 使用类方法验证基本规则
            if not Role.validate_role_naming(self.name):
                return False
            
            # 检查唯一性
            existing_role = Role.query.filter(
                Role.name == self.name,
                Role.id != self.id if self.id else True
            ).first()
            if existing_role:
                current_app.logger.error(
                    f'角色名称已存在: {self.name}\n'
                    f'- 已存在角色ID: {existing_role.id}'
                )
                return False
            
            current_app.logger.info(f'角色名称验证通过: {self.name}')
            return True
        except Exception as e:
            current_app.logger.error(f'验证角色名称时发生错误: {str(e)}')
            return False
    
    def validate_uniqueness(self):
        """验证角色的唯一性
        
        检查点:
        1. 角色名称必须唯一
        2. 默认角色必须唯一
        3. 超级管理员角色必须唯一
        4. 权限组合不能重复
        """
        try:
            # 检查名称唯一性
            name_conflict = self.query.filter(
                Role.name == self.name,
                Role.id != self.id if self.id else True
            ).first()
            if name_conflict:
                current_app.logger.error(
                    f'角色名称已存在: {self.name}, '
                    f'冲突角色ID: {name_conflict.id}'
                )
                return False
            
            # 检查默认角色的唯一性
            if self.is_default:
                default_conflict = self.query.filter(
                    Role.is_default == True,
                    Role.id != self.id if self.id else True
                ).first()
                if default_conflict:
                    current_app.logger.error(
                        f'默认角色已存在: {default_conflict.name}, '
                        f'角色ID: {default_conflict.id}'
                    )
                    return False
            
            # 检查超级管理员角色的唯一性
            if self.has_permission(Permission.SUPER_ADMIN):
                admin_conflict = self.query.filter(
                    Role.permissions.op('&')(Permission.SUPER_ADMIN.value) == Permission.SUPER_ADMIN.value,
                    Role.id != self.id if self.id else True
                ).first()
                if admin_conflict:
                    current_app.logger.error(
                        f'超级管理员角色已存在: {admin_conflict.name}, '
                        f'角色ID: {admin_conflict.id}'
                    )
                    return False
            
            # 检查权限组合的唯一性
            if self.permissions > 0:
                perm_conflict = self.query.filter(
                    Role.permissions == self.permissions,
                    Role.id != self.id if self.id else True
                ).first()
                if perm_conflict:
                    current_app.logger.error(
                        f'相同的权限组合已存在:\n'
                        f'- 当前角色: {self.name} ({self.permissions})\n'
                        f'- 冲突角色: {perm_conflict.name} ({perm_conflict.permissions})'
                    )
                    return False
            
            current_app.logger.info(f'角色 {self.name} 的唯一性验证通过')
            return True
        except Exception as e:
            current_app.logger.error(f'验证角色 {self.name} 的唯一性时发生错误: {str(e)}')
            return False
    
    def validate_description(self):
        """验证角色描述"""
        try:
            # 检查描述是否为 None
            if self.description is None:
                self.description = ''
                current_app.logger.warning(f'角色 {self.name} 的描述为 None，已设置为空字符串')
                return True
            
            # 检查描述长度
            if len(self.description) > 256:
                current_app.logger.error(f'角色 {self.name} 的描述过长: {len(self.description)} > 256')
                return False
            
            # 检查描述是否包含非法字符
            if not all(ord(c) < 65536 for c in self.description):
                current_app.logger.error(f'角色 {self.name} 的描述包含非法字符')
                return False
            
            # 检查描述是否包含敏感词
            sensitive_words = {'password', 'token', 'secret', 'key', 'hash'}
            if any(word in self.description.lower() for word in sensitive_words):
                current_app.logger.error(f'角色 {self.name} 的描述包含敏感词')
                return False
            
            current_app.logger.info(f'角色 {self.name} 的描述有效')
            return True
        except Exception as e:
            current_app.logger.error(f'验证角色 {self.name} 的描述时发生错误: {str(e)}')
            return False
    
    def validate_users(self):
        """验证角色的用户关联"""
        try:
            # 检查用户关联是否初始化
            if self.users is None:
                self.users = []
                current_app.logger.warning(f'角色 {self.name} 的用户关联为 None，已初始化为空列表')
                return True
            
            # 检查用户列表是否有效
            try:
                users_count = self.users.count()
                current_app.logger.info(f'角色 {self.name} 关联的用户数量: {users_count}')
            except Exception as e:
                current_app.logger.error(f'获取角色 {self.name} 的用户数量时发生错误: {str(e)}')
                return False
            
            # 检查用户是否都有效
            for user in self.users:
                if not hasattr(user, 'id') or not user.id:
                    current_app.logger.error(f'角色 {self.name} 关联的用户无效: {user}')
                    return False
                
                if not hasattr(user, 'is_active'):
                    current_app.logger.error(f'角色 {self.name} 关联的用户缺少 is_active 属性: {user}')
                    return False
            
            current_app.logger.info(f'角色 {self.name} 的用户关联验证通过')
            return True
        except Exception as e:
            current_app.logger.error(f'验证角色 {self.name} 的用户关联时发生错误: {str(e)}')
            return False
    
    def validate_timestamps(self):
        """验证时间戳"""
        try:
            now = datetime.now(UTC)
            
            # 检查时间戳是否为 None
            if self.created_at is None:
                self.created_at = now
                current_app.logger.warning(f'角色 {self.name} 的创建时间为 None，已设置为当前时间')
            
            if self.updated_at is None:
                self.updated_at = now
                current_app.logger.warning(f'角色 {self.name} 的更新时间为 None，已设置为当前时间')
            
            # 检查时间戳类型
            if not isinstance(self.created_at, datetime):
                current_app.logger.error(f'角色 {self.name} 的创建时间类型无效: {type(self.created_at)}')
                return False
            
            if not isinstance(self.updated_at, datetime):
                current_app.logger.error(f'角色 {self.name} 的更新时间类型无效: {type(self.updated_at)}')
                return False
            
            # 检查时区
            if self.created_at.tzinfo is None:
                current_app.logger.error(f'角色 {self.name} 的创建时间缺少时区信息')
                return False
            
            if self.updated_at.tzinfo is None:
                current_app.logger.error(f'角色 {self.name} 的更新时间缺少时区信息')
                return False
            
            # 检查时间顺序
            if self.updated_at < self.created_at:
                current_app.logger.error(f'角色 {self.name} 的更新时间早于创建时间')
                return False
            
            # 检查时间有效性
            if self.created_at > now:
                current_app.logger.error(f'角色 {self.name} 的创建时间晚于当前时间')
                return False
            
            if self.updated_at > now:
                current_app.logger.error(f'角色 {self.name} 的更新时间晚于当前时间')
                return False
            
            # 检查时间间隔
            time_diff = self.updated_at - self.created_at
            max_diff = timedelta(days=365 * 10)  # 最大时间间隔为 10 年
            if time_diff > max_diff:
                current_app.logger.warning(f'角色 {self.name} 的创建和更新时间间隔超过 10 年')
            
            current_app.logger.info(f'角色 {self.name} 的时间戳验证通过')
            return True
        except Exception as e:
            current_app.logger.error(f'验证角色 {self.name} 的时间戳时发生错误: {str(e)}')
            return False
    
    def update_timestamps(self, update_created=False):
        """更新时间戳"""
        try:
            now = datetime.now(UTC)
            
            # 更新创建时间
            if update_created:
                old_created_at = self.created_at
                self.created_at = now
                current_app.logger.info(f'更新角色 {self.name} 的创建时间: {old_created_at} -> {now}')
            
            # 更新修改时间
            old_updated_at = self.updated_at
            self.updated_at = now
            current_app.logger.info(f'更新角色 {self.name} 的更新时间: {old_updated_at} -> {now}')
            
            # 验证时间戳
            if not self.validate_timestamps():
                # 如果验证失败，回滚时间戳
                if update_created:
                    self.created_at = old_created_at
                self.updated_at = old_updated_at
                current_app.logger.error(f'更新角色 {self.name} 的时间戳失败，已回滚到原值')
                return False
            
            # 保存到数据库
            try:
                db.session.commit()
                current_app.logger.info(f'更新角色 {self.name} 的时间戳成功')
                return True
            except SQLAlchemyError as e:
                db.session.rollback()
                current_app.logger.error(f'保存角色 {self.name} 的时间戳失败: {str(e)}')
                return False
        except Exception as e:
            current_app.logger.error(f'更新角色 {self.name} 的时间戳时发生错误: {str(e)}')
            return False
    
    def is_expired(self, max_inactive_days=365):
        """检查角色是否过期
        
        参数:
            max_inactive_days: 最大不活动天数，默认为 365 天
        
        返回:
            bool: 如果角色过期返回 True，否则返回 False
        """
        try:
            # 验证参数
            if not isinstance(max_inactive_days, int) or max_inactive_days <= 0:
                current_app.logger.error(f'角色 {self.name} 的最大不活动天数无效: {max_inactive_days}')
                return True
            
            # 检查时间戳
            if not self.validate_timestamps():
                current_app.logger.error(f'检查角色 {self.name} 是否过期时，时间戳验证失败')
                return True
            
            # 计算不活动时间
            now = datetime.now(UTC)
            inactive_days = (now - self.updated_at).days
            
            # 检查是否超过最大不活动时间
            if inactive_days > max_inactive_days:
                current_app.logger.warning(
                    f'角色 {self.name} 已过期:\n'
                    f'- 最后更新时间: {self.updated_at}\n'
                    f'- 不活动天数: {inactive_days}\n'
                    f'- 最大不活动天数: {max_inactive_days}'
                )
                return True
            
            # 检查是否超过警告时间
            warning_days = max_inactive_days - 30  # 警告时间为过期时间前 30 天
            if inactive_days > warning_days:
                current_app.logger.warning(
                    f'角色 {self.name} 即将过期:\n'
                    f'- 最后更新时间: {self.updated_at}\n'
                    f'- 不活动天数: {inactive_days}\n'
                    f'- 距离过期还有: {max_inactive_days - inactive_days} 天'
                )
            
            current_app.logger.info(f'角色 {self.name} 未过期，不活动天数: {inactive_days}')
            return False
        except Exception as e:
            current_app.logger.error(f'检查角色 {self.name} 是否过期时发生错误: {str(e)}')
            return True
    
    def needs_update(self, update_interval_days=30):
        """检查角色是否需要更新
        
        参数:
            update_interval_days: 更新间隔天数，默认为 30 天
        
        返回:
            bool: 如果角色需要更新返回 True，否则返回 False
        """
        try:
            # 验证参数
            if not isinstance(update_interval_days, int) or update_interval_days <= 0:
                current_app.logger.error(f'角色 {self.name} 的更新间隔天数无效: {update_interval_days}')
                return True
            
            # 检查时间戳
            if not self.validate_timestamps():
                current_app.logger.error(f'检查角色 {self.name} 是否需要更新时，时间戳验证失败')
                return True
            
            # 计算上次更新时间
            now = datetime.now(UTC)
            days_since_update = (now - self.updated_at).days
            
            # 检查是否需要更新
            if days_since_update >= update_interval_days:
                current_app.logger.warning(
                    f'角色 {self.name} 需要更新:\n'
                    f'- 最后更新时间: {self.updated_at}\n'
                    f'- 距离上次更新: {days_since_update} 天\n'
                    f'- 更新间隔: {update_interval_days} 天'
                )
                return True
            
            # 检查是否即将需要更新
            warning_days = update_interval_days - 7  # 警告时间为更新时间前 7 天
            if days_since_update >= warning_days:
                current_app.logger.warning(
                    f'角色 {self.name} 即将需要更新:\n'
                    f'- 最后更新时间: {self.updated_at}\n'
                    f'- 距离上次更新: {days_since_update} 天\n'
                    f'- 距离下次更新还有: {update_interval_days - days_since_update} 天'
                )
            
            # 检查是否有待审核的用户
            pending_users = self.users.filter_by(is_active=False).count()
            if pending_users > 0:
                current_app.logger.warning(
                    f'角色 {self.name} 有待审核的用户:\n'
                    f'- 待审核用户数量: {pending_users}'
                )
                return True
            
            current_app.logger.info(
                f'角色 {self.name} 不需要更新:\n'
                f'- 最后更新时间: {self.updated_at}\n'
                f'- 距离上次更新: {days_since_update} 天'
            )
            return False
        except Exception as e:
            current_app.logger.error(f'检查角色 {self.name} 是否需要更新时发生错误: {str(e)}')
            return True
    
    def is_active(self, min_active_users=1, max_inactive_days=30):
        """检查角色是否活跃
        
        参数:
            min_active_users: 最少活跃用户数，默认为 1
            max_inactive_days: 最大不活动天数，默认为 30 天
        
        返回:
            bool: 如果角色活跃返回 True，否则返回 False
        """
        try:
            # 验证参数
            if not isinstance(min_active_users, int) or min_active_users < 0:
                current_app.logger.error(f'角色 {self.name} 的最少活跃用户数无效: {min_active_users}')
                return False
            
            if not isinstance(max_inactive_days, int) or max_inactive_days <= 0:
                current_app.logger.error(f'角色 {self.name} 的最大不活动天数无效: {max_inactive_days}')
                return False
            
            # 检查角色是否有效
            if not self.is_valid():
                current_app.logger.error(f'角色 {self.name} 无效')
                return False
            
            # 检查是否过期
            if self.is_expired(max_inactive_days):
                current_app.logger.warning(f'角色 {self.name} 已过期')
                return False
            
            # 获取用户统计
            users_query = self.users
            total_users = users_query.count()
            active_users = users_query.filter_by(is_active=True).count()
            pending_users = users_query.filter_by(is_approved=False).count()
            
            # 检查活跃用户数量
            if active_users < min_active_users:
                current_app.logger.warning(
                    f'角色 {self.name} 的活跃用户数量不足:\n'
                    f'- 总用户数: {total_users}\n'
                    f'- 当前活跃用户数: {active_users}\n'
                    f'- 最少活跃用户数: {min_active_users}'
                )
                return False
            
            # 检查是否需要更新
            if self.needs_update():
                current_app.logger.warning(f'角色 {self.name} 需要更新')
                return False
            
            # 检查是否为默认角色
            if self.is_default and active_users == 0:
                current_app.logger.warning(
                    f'默认角色 {self.name} 没有活跃用户:\n'
                    f'- 总用户数: {total_users}\n'
                    f'- 待审核用户数: {pending_users}'
                )
                return False
            
            # 检查是否有过多的待审核用户
            if pending_users > active_users:
                current_app.logger.warning(
                    f'角色 {self.name} 有过多的待审核用户:\n'
                    f'- 总用户数: {total_users}\n'
                    f'- 活跃用户数: {active_users}\n'
                    f'- 待审核用户数: {pending_users}'
                )
                return False
            
            current_app.logger.info(
                f'角色 {self.name} 处于活跃状态:\n'
                f'- 总用户数: {total_users}\n'
                f'- 活跃用户数: {active_users}\n'
                f'- 待审核用户数: {pending_users}\n'
                f'- 最后更新时间: {self.updated_at}\n'
                f'- 是否为默认角色: {self.is_default}'
            )
            return True
        except Exception as e:
            current_app.logger.error(f'检查角色 {self.name} 是否活跃时发生错误: {str(e)}')
            return False
    
    def get_usage_stats(self):
        """获取角色的使用统计
        
        返回:
            dict: 包含角色的使用统计信息
        """
        try:
            # 获取用户统计
            users_query = self.users
            total_users = users_query.count()
            active_users = users_query.filter_by(is_active=True).count()
            inactive_users = users_query.filter_by(is_active=False).count()
            pending_users = users_query.filter_by(is_approved=False).count()
            
            # 获取时间统计
            now = datetime.now(UTC)
            days_since_creation = (now - self.created_at).days
            days_since_update = (now - self.updated_at).days
            
            # 获取状态统计
            status = {
                'is_active': self.is_active(),
                'needs_update': self.needs_update(),
                'is_expired': self.is_expired(),
                'is_valid': self.is_valid()
            }
            
            # 获取权限统计
            permissions = self.get_permissions_list()
            
            # 汇总统计信息
            stats = {
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'is_default': self.is_default,
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'inactive': inactive_users,
                    'pending': pending_users,
                    'active_ratio': round(active_users / total_users * 100, 2) if total_users > 0 else 0,
                    'pending_ratio': round(pending_users / total_users * 100, 2) if total_users > 0 else 0
                },
                'time': {
                    'created_at': self.created_at.isoformat(),
                    'updated_at': self.updated_at.isoformat(),
                    'days_since_creation': days_since_creation,
                    'days_since_update': days_since_update,
                    'needs_update_in': max(0, 30 - days_since_update),  # 距离下次更新的天数
                    'expires_in': max(0, 365 - days_since_update)  # 距离过期的天数
                },
                'status': status,
                'permissions': {
                    'count': len(permissions),
                    'list': permissions,
                    'highest': max((p['value'] for p in permissions), default=0)
                }
            }
            
            current_app.logger.info(
                f'获取角色 {self.name} 的使用统计:\n'
                f'- 总用户数: {total_users}\n'
                f'- 活跃用户数: {active_users}\n'
                f'- 活跃用户占比: {stats["users"]["active_ratio"]}%\n'
                f'- 创建天数: {days_since_creation}\n'
                f'- 最后更新天数: {days_since_update}\n'
                f'- 权限数量: {permission_count}'
            )
            return stats
        except Exception as e:
            current_app.logger.error(f'获取角色 {self.name} 的使用统计时发生错误: {str(e)}')
            return None
    
    def validate_permission_assignment(self, strict_mode=False):
        """检查角色的权限分配是否合理
        
        参数:
            strict_mode: 是否使用严格模式，默认为 False
        
        返回:
            bool: 如果权限分配合理返回 True，否则返回 False
        """
        try:
            # 获取角色的权限列表
            permissions = self.get_permissions_list()
            permission_count = len(permissions)
            
            # 检查权限数量
            if permission_count == 0:
                current_app.logger.warning(f'角色 {self.name} 没有任何权限')
                return not strict_mode
            
            # 检查是否有重复权限
            unique_permissions = set(permissions)
            if len(unique_permissions) != permission_count:
                current_app.logger.error(f'角色 {self.name} 存在重复权限')
                return False
            
            # 检查是否有无效权限
            all_permissions = set(Permission.get_all_permissions())
            invalid_permissions = unique_permissions - all_permissions
            if invalid_permissions:
                current_app.logger.error(
                    f'角色 {self.name} 存在无效权限:\n'
                    f'- 无效权限: {invalid_permissions}'
                )
                return False
            
            # 检查权限组合是否合理
            if Permission.ADMIN in permissions:
                # 如果有管理员权限，不应该再有其他权限
                if len(permissions) > 1:
                    current_app.logger.warning(
                        f'角色 {self.name} 的权限组合不合理:\n'
                        f'- 已有管理员权限，不应再有其他权限\n'
                        f'- 当前权限: {permissions}'
                    )
                    return not strict_mode
            else:
                # 检查是否有基础权限
                if Permission.READ not in permissions:
                    current_app.logger.warning(
                        f'角色 {self.name} 的权限组合不合理:\n'
                        f'- 缺少基础的读取权限\n'
                        f'- 当前权限: {permissions}'
                    )
                    return not strict_mode
                
                # 检查权限依赖
                if Permission.WRITE in permissions and Permission.READ not in permissions:
                    current_app.logger.warning(
                        f'角色 {self.name} 的权限组合不合理:\n'
                        f'- 写入权限依赖于读取权限\n'
                        f'- 当前权限: {permissions}'
                    )
                    return not strict_mode
                
                if Permission.DELETE in permissions and Permission.WRITE not in permissions:
                    current_app.logger.warning(
                        f'角色 {self.name} 的权限组合不合理:\n'
                        f'- 删除权限依赖于写入权限\n'
                        f'- 当前权限: {permissions}'
                    )
                    return not strict_mode
            
            # 检查是否为默认角色
            if self.is_default:
                # 默认角色应该只有基础权限
                if permission_count > 1 or (permission_count == 1 and Permission.READ not in permissions):
                    current_app.logger.warning(
                        f'默认角色 {self.name} 的权限组合不合理:\n'
                        f'- 默认角色应该只有基础权限\n'
                        f'- 当前权限: {permissions}'
                    )
                    return not strict_mode
            
            current_app.logger.info(
                f'角色 {self.name} 的权限分配合理:\n'
                f'- 权限数量: {permission_count}\n'
                f'- 权限列表: {permissions}\n'
                f'- 是否为默认角色: {self.is_default}'
            )
            return True
        except Exception as e:
            current_app.logger.error(f'检查角色 {self.name} 的权限分配时发生错误: {str(e)}')
            return False
    
    def validate_user_distribution(self, max_users_per_role=100, min_active_ratio=0.5):
        """检查角色的用户分布是否合理
        
        参数:
            max_users_per_role: 每个角色的最大用户数，默认为 100
            min_active_ratio: 最小活跃用户比例，默认为 0.5 (50%)
        
        返回:
            bool: 如果用户分布合理返回 True，否则返回 False
        """
        try:
            # 获取用户统计
            total_users = self.users.count()
            active_users = self.users.filter_by(is_active=True).count()
            
            # 检查用户总数
            if total_users > max_users_per_role:
                current_app.logger.warning(
                    f'角色 {self.name} 的用户数量超出限制:\n'
                    f'- 当前用户数: {total_users}\n'
                    f'- 最大用户数: {max_users_per_role}'
                )
                return False
            
            # 检查活跃用户比例
            if total_users > 0:
                active_ratio = active_users / total_users
                if active_ratio < min_active_ratio:
                    current_app.logger.warning(
                        f'角色 {self.name} 的活跃用户比例过低:\n'
                        f'- 当前活跃比例: {active_ratio:.2%}\n'
                        f'- 最小活跃比例: {min_active_ratio:.2%}'
                    )
                    return False
            
            # 检查用户权限分布
            users_by_permission = {}
            for user in self.users:
                for permission in user.get_permissions():
                    users_by_permission[permission] = users_by_permission.get(permission, 0) + 1
            
            # 检查权限分布是否均衡
            if users_by_permission:
                avg_users_per_permission = sum(users_by_permission.values()) / len(users_by_permission)
                max_deviation = 0.3  # 允许 30% 的偏差
                
                for permission, count in users_by_permission.items():
                    deviation = abs(count - avg_users_per_permission) / avg_users_per_permission
                    if deviation > max_deviation:
                        current_app.logger.warning(
                            f'角色 {self.name} 的权限分布不均衡:\n'
                            f'- 权限 {permission} 的用户数: {count}\n'
                            f'- 平均每个权限用户数: {avg_users_per_permission:.2f}\n'
                            f'- 偏差比例: {deviation:.2%}'
                        )
                        return False
            
            current_app.logger.info(
                f'角色 {self.name} 的用户分布合理:\n'
                f'- 总用户数: {total_users}\n'
                f'- 活跃用户数: {active_users}\n'
                f'- 活跃比例: {(active_ratio * 100):.2f}% (如果有用户)'
            )
            return True
        except Exception as e:
            current_app.logger.error(f'检查角色 {self.name} 的用户分布时发生错误: {str(e)}')
            return False
    
    @classmethod
    def validate_role_naming(cls, name):
        """验证角色名称
        
        规则:
        1. 长度在3-64个字符之间
        2. 只能包含字母、数字
        3. 不能与系统保留字重名
        4. 必须以字母开头
        """
        try:
            # 检查基本条件
            if not name or not isinstance(name, str):
                return False
            
            # 检查长度
            name_length = len(name)
            if name_length < 3 or name_length > 64:
                return False
            
            # 检查格式
            import re
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
                return False
            
            # 检查保留字
            reserved_names = {
                'role', 'root', 'system',
                'anonymous', 'default', 'test', 'temp', 'tmp'
            }
            if name.lower() in reserved_names:
                return False
            
            return True
            
        except Exception as e:
            current_app.logger.error(f'验证角色 {name} 的命名时发生错误: {str(e)}')
            return False
    
    def check_permission_inheritance(self, parent_role=None):
        """检查角色的权限继承关系
        
        参数:
            parent_role: 父角色对象，默认为 None
        
        返回:
            bool: 如果权限继承合理返回 True，否则返回 False
        """
        try:
            # 获取当前角色的权限
            current_permissions = set(self.get_permissions_list())
            
            # 如果没有指定父角色，尝试查找可能的父角色
            if parent_role is None:
                # 查找权限数量大于当前角色的所有角色
                potential_parents = Role.query.filter(
                    Role.id != self.id,
                    Role.permissions > self.permissions
                ).all()
                
                # 检查权限包含关系
                for role in potential_parents:
                    parent_permissions = set(role.get_permissions_list())
                    if current_permissions.issubset(parent_permissions):
                        parent_role = role
                        break
            
            # 如果找到父角色，检查继承关系
            if parent_role:
                parent_permissions = set(parent_role.get_permissions_list())
                
                # 检查权限包含关系
                if not current_permissions.issubset(parent_permissions):
                    current_app.logger.error(
                        f'角色 {self.name} 的权限继承关系不合理:\n'
                        f'- 父角色: {parent_role.name}\n'
                        f'- 当前角色缺少的权限: {parent_permissions - current_permissions}'
                    )
                    return False
                
                # 检查权限差异
                permission_diff = parent_permissions - current_permissions
                if not permission_diff:
                    current_app.logger.warning(
                        f'角色 {self.name} 与父角色 {parent_role.name} 的权限完全相同，建议合并角色'
                    )
                
                # 检查继承深度
                inheritance_depth = 1
                current_parent = parent_role
                while True:
                    next_parent = None
                    for role in Role.query.filter(Role.id != current_parent.id).all():
                        if set(role.get_permissions_list()).issuperset(set(current_parent.get_permissions_list())):
                            next_parent = role
                            break
                    
                    if next_parent is None:
                        break
                    
                    inheritance_depth += 1
                    current_parent = next_parent
                
                if inheritance_depth > 3:
                    current_app.logger.warning(
                        f'角色 {self.name} 的权限继承深度过大:\n'
                        f'- 当前继承深度: {inheritance_depth}\n'
                        f'- 建议继承深度不超过 3 层'
                    )
            
            current_app.logger.info(
                f'角色 {self.name} 的权限继承关系合理:\n'
                f'- 当前权限: {current_permissions}\n'
                f'- 父角色: {parent_role.name if parent_role else "无"}'
            )
            return True
        except Exception as e:
            current_app.logger.error(f'检查角色 {self.name} 的权限继承关系时发生错误: {str(e)}')
            return False
    
    def validate(self):
        """验证角色的所有属性"""
        try:
            # 验证名称
            if not self.validate_name():
                current_app.logger.error(f'角色名称验证失败: {self.name}')
                return False
            
            # 验证描述
            if not self.validate_description():
                current_app.logger.error(f'角色 {self.name} 的描述验证失败')
                return False
            
            # 验证权限
            if not self.validate_permissions():
                current_app.logger.error(f'角色 {self.name} 的权限验证失败')
                return False
            
            # 验证用户关联
            if not self.validate_users():
                current_app.logger.error(f'角色 {self.name} 的用户关联验证失败')
                return False
            
            # 验证唯一性
            if not self.validate_uniqueness():
                current_app.logger.error(f'角色 {self.name} 的唯一性验证失败')
                return False
            
            # 验证时间戳
            if not self.validate_timestamps():
                current_app.logger.error(f'角色 {self.name} 的时间戳验证失败')
                return False
            
            current_app.logger.info(f'角色 {self.name} 的所有属性验证通过')
            return True
        except Exception as e:
            current_app.logger.error(f'验证角色 {self.name} 时发生错误: {str(e)}')
            return False
    
    def validate_permissions(self):
        """验证角色权限设置
        
        检查点:
        1. 权限值必须为非负整数
        2. 权限值不能超过所有权限的总和
        3. 权限组合必须合理（依赖关系）
        4. 默认角色的权限限制
        """
        try:
            # 检查权限值类型和范围
            if not isinstance(self.permissions, int):
                current_app.logger.error(
                    f'角色 {self.name} 的权限值类型无效:\n'
                    f'- 期望类型: int\n'
                    f'- 实际类型: {type(self.permissions)}'
                )
                return False
            
            # 计算所有权限的总和
            all_permissions = sum(perm.value for perm in Permission)
            if not (0 <= self.permissions <= all_permissions):
                current_app.logger.error(
                    f'角色 {self.name} 的权限值超出范围:\n'
                    f'- 当前值: {self.permissions}\n'
                    f'- 允许范围: [0, {all_permissions}]'
                )
                return False
            
            # 检查是否包含未定义的权限位
            undefined_bits = self.permissions & ~all_permissions
            if undefined_bits:
                current_app.logger.error(
                    f'角色 {self.name} 包含未定义的权限位:\n'
                    f'- 未定义位: {bin(undefined_bits)}\n'
                    f'- 当前权限: {bin(self.permissions)}'
                )
                return False
            
            # 检查权限依赖关系
            permission_deps = {
                Permission.SUPER_ADMIN: [Permission.ADMIN, Permission.MODERATE],
                Permission.ADMIN: [Permission.MODERATE, Permission.POST],
                Permission.MODERATE: [Permission.COMMENT],
                Permission.POST: [Permission.COMMENT],
                Permission.COMMENT: [Permission.VIEW],
                Permission.VIEW: []
            }
            
            for perm, deps in permission_deps.items():
                if self.has_permission(perm):
                    for dep in deps:
                        if not self.has_permission(dep):
                            current_app.logger.error(
                                f'角色 {self.name} 的权限依赖关系不满足:\n'
                                f'- 当前权限: {perm.name}\n'
                                f'- 缺失依赖: {dep.name}'
                            )
                            return False
            
            # 检查超级管理员权限
            if self.has_permission(Permission.SUPER_ADMIN):
                # 超级管理员必须拥有所有权限
                if self.permissions != all_permissions:
                    missing_perms = [p.name for p in Permission if not self.has_permission(p)]
                    current_app.logger.error(
                        f'超级管理员角色 {self.name} 缺少以下权限:\n'
                        f'- 缺失权限: {missing_perms}'
                    )
                    return False
            
            # 检查默认角色的权限限制
            if self.is_default:
                # 默认角色不能有管理员权限
                admin_perms = [Permission.SUPER_ADMIN, Permission.ADMIN]
                for perm in admin_perms:
                    if self.has_permission(perm):
                        current_app.logger.error(
                            f'默认角色 {self.name} 不能有管理员权限:\n'
                            f'- 非法权限: {perm.name}'
                        )
                        return False
                
                # 默认角色必须至少有基本权限
                basic_perms = [Permission.VIEW, Permission.COMMENT]
                for perm in basic_perms:
                    if not self.has_permission(perm):
                        current_app.logger.error(
                            f'默认角色 {self.name} 缺少基本权限:\n'
                            f'- 缺失权限: {perm.name}'
                        )
                        return False
            
            # 检查是否至少有一个权限
            if self.permissions == 0:
                current_app.logger.error(f'角色 {self.name} 没有任何权限')
                return False
            
            current_app.logger.info(
                f'角色 {self.name} 的权限设置验证通过:\n'
                f'- 权限值: {self.permissions}\n'
                f'- 权限列表: {[p.name for p in self.get_permissions()]}'
            )
            return True
        except Exception as e:
            current_app.logger.error(f'验证角色 {self.name} 的权限设置时发生错误: {str(e)}')
            return False
        
    def update_permissions(self, permissions):
        """更新角色权限
        
        Args:
            permissions: 权限列表，可以是 Permission 枚举值或整数值的列表
            
        Returns:
            bool: 更新成功返回 True，否则返回 False
            
        Raises:
            ValueError: 权限值无效或权限组合不合理时抛出
        """
        try:
            # 保存原始权限值用于回滚
            old_permissions = self.permissions
            old_permission_list = [p.name for p in self.get_permissions()]
            
            # 计算新的权限值
            new_permissions = 0
            processed_permissions = []
            
            for permission in permissions:
                # 处理不同类型的权限输入
                if isinstance(permission, Permission):
                    perm_value = permission.value
                    perm_name = permission.name
                elif isinstance(permission, int):
                    # 验证整数值是否为有效的权限值
                    if permission not in [p.value for p in Permission]:
                        raise ValueError(
                            f'无效的权限值: {permission}\n'
                            f'有效值: {[p.value for p in Permission]}'
                        )
                    perm_value = permission
                    perm_name = Permission(permission).name
                else:
                    raise ValueError(
                        f'无效的权限类型: {type(permission)}\n'
                        f'期望类型: Permission 或 int'
                    )
                
                new_permissions |= perm_value
                processed_permissions.append(perm_name)
            
            # 更新权限值
            self.permissions = new_permissions
            
            # 验证新的权限设置
            if not self.validate_permissions():
                # 验证失败时回滚并提供详细错误信息
                self.permissions = old_permissions
                current_app.logger.error(
                    f'角色 {self.name} 的新权限设置无效:\n'
                    f'- 原权限: {old_permission_list}\n'
                    f'- 尝试设置: {processed_permissions}'
                )
                return False
            
            # 检查是否有实际变更
            if old_permissions == new_permissions:
                current_app.logger.info(
                    f'角色 {self.name} 的权限未发生变化:\n'
                    f'- 当前权限: {processed_permissions}'
                )
                return True
            
            # 更新时间戳
            self.updated_at = datetime.now(UTC)
            
            try:
                # 提交事务
                db.session.commit()
                
                # 记录权限变更
                added_perms = set(processed_permissions) - set(old_permission_list)
                removed_perms = set(old_permission_list) - set(processed_permissions)
                
                change_log = [
                    f'角色 {self.name} 的权限更新成功:',
                    f'- 权限值: {old_permissions} -> {new_permissions}',
                ]
                
                if added_perms:
                    change_log.append(f'- 新增权限: {sorted(added_perms)}')
                if removed_perms:
                    change_log.append(f'- 移除权限: {sorted(removed_perms)}')
                
                current_app.logger.info('\n'.join(change_log))
                return True
                
            except Exception as e:
                # 提交失败时回滚
                db.session.rollback()
                self.permissions = old_permissions
                current_app.logger.error(
                    f'角色 {self.name} 更新权限时数据库操作失败:\n'
                    f'- 错误信息: {str(e)}'
                )
                return False
                
        except Exception as e:
            # 确保任何异常发生时都回滚到原始状态
            self.permissions = old_permissions if 'old_permissions' in locals() else self.permissions
            if 'db' in locals():
                db.session.rollback()
            
            current_app.logger.error(
                f'角色 {self.name} 更新权限时发生错误:\n'
                f'- 错误类型: {type(e).__name__}\n'
                f'- 错误信息: {str(e)}'
            )
            return False
    
    @staticmethod
    def insert_roles():
        """初始化或更新默认角色
        
        这个方法会检查并确保所有默认角色都存在且配置正确。
        如果某个角色不存在，则创建它。
        如果已存在，则检查并更新其配置。
        
        Returns:
            bool: 初始化成功返回 True，否则返回 False
        """
        # 默认角色配置
        roles = [
            {
                'name': 'super_admin',
                'description': '超级管理员',
                'permissions': Permission.SUPER_ADMIN | Permission.ADMIN | Permission.MODERATE | Permission.POST | Permission.COMMENT | Permission.VIEW,
                'is_default': False,
                'order': 1  # 角色优先级，越小越高
            },
            {
                'name': 'admin',
                'description': '管理员',
                'permissions': Permission.ADMIN | Permission.MODERATE | Permission.POST | Permission.COMMENT | Permission.VIEW,
                'is_default': False,
                'order': 2
            },
            {
                'name': 'editor',
                'description': '编辑者',
                'permissions': Permission.POST | Permission.COMMENT | Permission.VIEW,
                'is_default': False,
                'order': 3
            },
            {
                'name': 'user',
                'description': '普通用户',
                'permissions': Permission.COMMENT | Permission.VIEW,
                'is_default': True,
                'order': 4
            }
        ]
        
        try:
            now = datetime.now(UTC)
            default_role_found = False
            success_count = 0
            total_count = len(roles)
            
            # 按优先级排序处理角色
            for role_data in sorted(roles, key=lambda x: x['order']):
                try:
                    current_app.logger.info(f'开始处理角色: {role_data["name"]}')
                    role = Role.query.filter_by(name=role_data['name']).first()
                    
                    if role is None:
                        # 创建新角色
                        role = Role(
                            name=role_data['name'],
                            description=role_data['description'],
                            permissions=role_data['permissions'].value,
                            is_default=role_data['is_default'],
                            created_at=now,
                            updated_at=now
                        )
                        
                        # 验证角色配置
                        if not role.validate():
                            raise ValueError(f'新角色 {role.name} 配置无效')
                        
                        db.session.add(role)
                        current_app.logger.info(
                            f'创建新角色成功:\n'
                            f'- 名称: {role.name}\n'
                            f'- 描述: {role.description}\n'
                            f'- 权限: {[p.name for p in role.get_permissions()]}\n'
                            f'- 是否默认: {role.is_default}'
                        )
                    else:
                        # 检查是否需要更新
                        updates_needed = [
                            ('permissions', role.permissions != role_data['permissions'].value),
                            ('description', role.description != role_data['description']),
                            ('is_default', role.is_default != role_data['is_default'])
                        ]
                        
                        if any(needed for _, needed in updates_needed):
                            # 保存原始值用于回滚
                            old_values = {
                                'permissions': role.permissions,
                                'description': role.description,
                                'is_default': role.is_default
                            }
                            
                            # 更新属性
                            role.permissions = role_data['permissions'].value
                            role.description = role_data['description']
                            role.is_default = role_data['is_default']
                            role.updated_at = now
                            
                            # 验证新配置
                            if not role.validate():
                                # 验证失败，回滚更改
                                role.permissions = old_values['permissions']
                                role.description = old_values['description']
                                role.is_default = old_values['is_default']
                                raise ValueError(f'角色 {role.name} 的新配置无效')
                            
                            # 记录变更
                            changes = []
                            if old_values['permissions'] != role.permissions:
                                old_perms = [p.name for p in Permission if old_values['permissions'] & p.value]
                                new_perms = [p.name for p in role.get_permissions()]
                                changes.append(f'- 权限: {old_perms} -> {new_perms}')
                            if old_values['description'] != role.description:
                                changes.append(f'- 描述: "{old_values["description"]}" -> "{role.description}"')
                            if old_values['is_default'] != role.is_default:
                                changes.append(f'- 默认状态: {old_values["is_default"]} -> {role.is_default}')
                            
                            current_app.logger.info(
                                f'更新角色 {role.name} 成功:\n'
                                + '\n'.join(changes)
                            )
                        else:
                            current_app.logger.info(f'角色 {role.name} 配置无变化，跳过更新')
                    
                    # 处理默认角色状态
                    if role.is_default:
                        if default_role_found:
                            current_app.logger.warning(
                                f'检测到多个默认角色:\n'
                                f'- 当前角色: {role.name}\n'
                                f'- 操作: 取消默认状态'
                            )
                            role.is_default = False
                        else:
                            default_role_found = True
                            current_app.logger.info(f'确认默认角色: {role.name}')
                    
                    db.session.flush()
                    success_count += 1
                    
                except Exception as e:
                    current_app.logger.error(
                        f'处理角色 {role_data["name"]} 时发生错误:\n'
                        f'- 错误类型: {type(e).__name__}\n'
                        f'- 错误信息: {str(e)}'
                    )
                    continue
            
            # 检查是否有默认角色
            if not default_role_found:
                current_app.logger.error('没有找到默认角色，请检查角色配置')
                return False
            
            # 提交事务
            db.session.commit()
            
            # 记录最终结果
            if success_count == total_count:
                current_app.logger.info('所有角色初始化成功')
                return True
            else:
                current_app.logger.warning(
                    f'角色初始化部分完成:\n'
                    f'- 成功: {success_count}/{total_count}\n'
                    f'- 失败: {total_count - success_count}/{total_count}'
                )
                return success_count > 0
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f'角色初始化过程发生错误:\n'
                f'- 错误类型: {type(e).__name__}\n'
                f'- 错误信息: {str(e)}'
            )
            return False
    
    @classmethod
    def get_default_role(cls):
        """获取默认角色
        
        返回:
            Role: 默认角色对象，如果未找到则返回None
            
        说明:
            1. 首先查找标记为默认的角色
            2. 如果未找到，尝试将普通用户角色设为默认
            3. 如果仍未找到合适的角色，返回None
        """
        try:
            # 查找标记为默认的角色
            role = cls.query.filter_by(is_default=True).first()
            if role:
                current_app.logger.debug(f'找到默认角色: {role.name}')
                return role
                
            # 尝试使用普通用户角色作为默认角色
            current_app.logger.warning('未找到默认角色，尝试使用普通用户角色')
            role = cls.query.filter_by(name='user').first()
            
            if role:
                # 验证该角色是否适合作为默认角色
                if role.validate_permissions():
                    current_app.logger.info(f'将角色 {role.name} 设置为默认角色')
                    if role.set_as_default():
                        return role
                    else:
                        current_app.logger.error('设置默认角色失败')
                else:
                    current_app.logger.error(f'角色 {role.name} 的权限配置不适合作为默认角色')
            else:
                current_app.logger.error('未找到合适的默认角色')
                
            return None
            
        except Exception as e:
            current_app.logger.error(f'获取默认角色失败: {str(e)}')
            return None
    
    def set_as_default(self):
        """将当前角色设置为默认角色
        
        返回:
            bool: 设置成功返回True，否则返回False
            
        说明:
            1. 验证当前角色是否适合作为默认角色
            2. 取消其他角色的默认状态
            3. 设置当前角色为默认角色
        """
        if not self.id:
            current_app.logger.error('无法将未保存的角色设置为默认角色')
            return False
            
        # 验证角色的权限设置是否适合作为默认角色
        if not self.validate_permissions():
            current_app.logger.error(f'角色 {self.name} 的权限配置不适合作为默认角色')
            return False
            
        try:
            # 开启事务
            db.session.begin_nested()
            
            # 先取消其他角色的默认状态
            cls = self.__class__
            affected = cls.query.filter_by(is_default=True).update({'is_default': False})
            if affected > 0:
                current_app.logger.info(f'取消了 {affected} 个角色的默认状态')
            
            # 设置当前角色为默认
            self.is_default = True
            self.updated_at = datetime.now(UTC)
            
            # 提交事务
            db.session.commit()
            current_app.logger.info(f'角色 {self.name} 已设置为默认角色')
            return True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'设置默认角色失败: {str(e)}')
            return False
    
    def unset_as_default(self):
        """取消当前角色的默认状态
        
        返回:
            bool: 取消成功返回True，否则返回False
            
        说明:
            1. 如果当前角色不是默认角色，直接返回True
            2. 确保系统中至少存在一个其他可用的角色
            3. 取消当前角色的默认状态
        """
        if not self.id:
            current_app.logger.error('无法操作未保存的角色')
            return False
            
        if not self.is_default:
            return True
            
        # 确保系统中存在其他可用的角色
        cls = self.__class__
        other_role = cls.query.filter(cls.id != self.id).first()
        if not other_role:
            current_app.logger.error('系统中没有其他可用的角色，无法取消唯一角色的默认状态')
            return False
            
        try:
            # 开启事务
            db.session.begin_nested()
            
            self.is_default = False
            self.updated_at = datetime.now(UTC)
            
            # 如果没有其他默认角色，将普通用户角色设为默认
            if not cls.query.filter_by(is_default=True).first():
                user_role = cls.query.filter_by(name='user').first()
                if user_role and user_role.id != self.id:
                    user_role.is_default = True
                    user_role.updated_at = datetime.now(UTC)
                    current_app.logger.info(f'将角色 {user_role.name} 设置为新的默认角色')
            
            # 提交事务
            db.session.commit()
            current_app.logger.info(f'角色 {self.name} 已取消默认状态')
            return True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'取消默认角色失败: {str(e)}')
            return False
    
    @classmethod
    def get_by_name(cls, name):
        """根据名称获取角色"""
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def get_by_permission(cls, permission):
        """获取具有指定权限的角色列表"""
        if isinstance(permission, Permission):
            permission = permission.value
        return cls.query.filter(cls.permissions.op('&')(permission) == permission).all()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'permissions': self.permissions,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'users_count': self.users.count(),
            'permissions_list': [p.name for p in self.get_permissions()]
        }
    
    def __repr__(self):
        return f'<Role {self.name}>'