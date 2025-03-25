"""
文件名：__init__.py
描述：服务模块初始化文件
作者：denny
创建日期：2024-03-21
"""

# 避免循环导入，将导入语句移到函数内部
def get_user_service():
    from .user import UserService
    return UserService()

def get_operation_log_service():
    from .operation_log import operation_log_service
    return operation_log_service

def get_comment_service():
    from .comment import CommentService
    return CommentService()

def get_post_service():
    from .post import PostService
    return PostService()

def get_category_service():
    from .category import CategoryService
    return CategoryService()

def get_tag_service():
    from .tag import TagService
    return TagService()

def get_security_service():
    from .security import SecurityService
    return SecurityService()

def get_role_service():
    from .role_service import RoleService
    return RoleService()

# 导出服务工厂函数
__all__ = [
    'get_user_service',
    'get_operation_log_service',
    'get_comment_service',
    'get_post_service',
    'get_category_service',
    'get_tag_service',
    'get_security_service',
    'get_role_service'
]

