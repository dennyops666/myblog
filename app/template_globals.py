"""
文件名：template_globals.py
描述：模板全局函数
作者：denny
创建日期：2024-03-21
"""

from flask import url_for, current_app
from app.models.post import Post
from app.models.tag import Tag
from app.models.category import Category
from app.models.user import User
from app.models.post import PostStatus
from app.utils.filters import init_filters

def register_template_globals(app):
    """注册模板全局函数和过滤器"""
    
    # 初始化过滤器
    init_filters(app)
    
    @app.template_global()
    def get_recent_posts(limit=5):
        """获取最近的文章"""
        return Post.query.filter(
            (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
        ).order_by(Post.created_at.desc()).limit(limit).all()
    
    @app.template_global()
    def get_popular_tags(limit=10):
        """获取热门标签"""
        return Tag.query.order_by(Tag.posts.any()).limit(limit).all()
    
    @app.template_global()
    def get_categories():
        """获取所有分类"""
        return Category.query.order_by(Category.name).all()
    
    @app.template_global()
    def get_user_by_id(user_id):
        """根据ID获取用户"""
        return User.query.get(user_id)
    
    @app.template_global()
    def static_file_url(filename):
        """生成静态文件URL"""
        return url_for('static', filename=filename, _external=True)
    
    @app.template_global()
    def get_site_config(key, default=None):
        """获取网站配置"""
        return current_app.config.get(key, default) 