"""
文件名：permission.py
描述：权限模型
作者：denny
创建日期：2024-03-21
"""

from enum import Flag, auto

class Permission(Flag):
    """权限枚举类"""
    NONE = 0  # 无权限
    VIEW = 1  # 查看权限
    COMMENT = 2  # 评论权限
    POST = 4  # 发文权限
    MODERATE = 8  # 管理评论权限
    ADMIN = 16  # 管理员权限
    SUPER_ADMIN = 32  # 超级管理员权限
    
    # 预定义的角色权限组合
    VIEWER = VIEW
    USER = VIEW | COMMENT
    EDITOR = VIEW | COMMENT | POST
    MODERATOR = VIEW | COMMENT | POST | MODERATE
    ADMINISTRATOR = VIEW | COMMENT | POST | MODERATE | ADMIN
    SUPER_ADMINISTRATOR = VIEW | COMMENT | POST | MODERATE | ADMIN | SUPER_ADMIN