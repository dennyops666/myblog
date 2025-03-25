"""
文件名：filters.py
描述：自定义过滤器
作者：denny
创建日期：2024-03-21
"""

import hashlib
from datetime import datetime, UTC

def gravatar(email, size=100, default='mp', rating='g'):
    """生成 Gravatar URL
    
    Args:
        email: 邮箱地址
        size: 图片大小（像素）
        default: 默认图片类型
        rating: 图片分级
        
    Returns:
        str: Gravatar URL
    """
    if not email:
        return f"https://www.gravatar.com/avatar/?s={size}&d={default}&r={rating}"
        
    email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d={default}&r={rating}"

def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    """格式化日期时间
    
    Args:
        value: 日期时间对象或字符串
        format: 格式化字符串
        
    Returns:
        str: 格式化后的日期时间字符串
    """
    if not value:
        return ''
        
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
            
    return value.strftime(format)

def format_date(value, format='%Y-%m-%d'):
    """格式化日期
    
    Args:
        value: 日期时间对象或字符串
        format: 格式化字符串
        
    Returns:
        str: 格式化后的日期字符串
    """
    return format_datetime(value, format)

def format_time(value, format='%H:%M:%S'):
    """格式化时间
    
    Args:
        value: 日期时间对象或字符串
        format: 格式化字符串
        
    Returns:
        str: 格式化后的时间字符串
    """
    return format_datetime(value, format)

def init_filters(app):
    """初始化自定义过滤器"""
    
    @app.template_filter('gravatar')
    def gravatar_filter(email, size=100, default='mp'):
        """生成 Gravatar 头像 URL
        
        Args:
            email: 用户邮箱
            size: 头像大小(像素)
            default: 默认头像样式(mp/identicon/monsterid/wavatar/retro/robohash/blank)
            
        Returns:
            str: Gravatar URL
        """
        email = email.lower().encode('utf-8')
        email_hash = hashlib.md5(email).hexdigest()
        url = f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d={default}"
        return url
        
    @app.template_filter('datetime')
    def datetime_filter(value, format='%Y-%m-%d %H:%M:%S'):
        """日期时间过滤器"""
        return format_datetime(value, format)
        
    @app.template_filter('date')
    def date_filter(value, format='%Y-%m-%d'):
        """日期过滤器"""
        return format_date(value, format)
        
    @app.template_filter('time')
    def time_filter(value, format='%H:%M:%S'):
        """时间过滤器"""
        return format_time(value, format) 