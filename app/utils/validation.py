"""
文件名：validation.py
描述：数据验证工具模块
作者：denny
"""
import re
from typing import Tuple

def validate_username(username: str) -> Tuple[bool, str]:
    """
    验证用户名是否合法
    
    Args:
        username: 用户名
        
    Returns:
        Tuple[bool, str]: (是否合法, 错误信息)
    """
    if not username:
        return False, "用户名不能为空"
        
    if len(username) < 3:
        return False, "用户名长度不能小于3个字符"
        
    if len(username) > 20:
        return False, "用户名长度不能超过20个字符"
        
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "用户名只能包含字母、数字、下划线和连字符"
        
    return True, ""

def validate_email(email: str) -> Tuple[bool, str]:
    """
    验证邮箱地址是否合法
    
    Args:
        email: 邮箱地址
        
    Returns:
        Tuple[bool, str]: (是否合法, 错误信息)
    """
    if not email:
        return False, "邮箱地址不能为空"
        
    if len(email) > 254:
        return False, "邮箱地址长度不能超过254个字符"
        
    # 使用更严格的邮箱验证正则表达式
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "邮箱地址格式不正确"
        
    return True, ""

def validate_password(password: str) -> Tuple[bool, str]:
    """
    验证密码是否合法
    
    Args:
        password: 密码
        
    Returns:
        Tuple[bool, str]: (是否合法, 错误信息)
    """
    if not password:
        return False, "密码不能为空"
        
    if len(password) < 8:
        return False, "密码长度不能小于8个字符"
        
    if len(password) > 72:
        return False, "密码长度不能超过72个字符"
        
    if not re.search(r'[A-Z]', password):
        return False, "密码必须包含至少一个大写字母"
        
    if not re.search(r'[a-z]', password):
        return False, "密码必须包含至少一个小写字母"
        
    if not re.search(r'[0-9]', password):
        return False, "密码必须包含至少一个数字"
        
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "密码必须包含至少一个特殊字符"
        
    return True, ""
