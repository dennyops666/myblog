"""
文件名：filters.py
描述：自定义过滤器
作者：denny
创建日期：2025-02-16
"""

import hashlib

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