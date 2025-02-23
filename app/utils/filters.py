"""
文件名：filters.py
描述：自定义过滤器
作者：denny
创建日期：2024-03-21
"""

import hashlib

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