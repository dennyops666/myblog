from flask import current_app
from app.models.category import Category
from app.models.tag import Tag

def register_context_processors(app):
    """注册全局上下文处理器"""
    
    @app.context_processor
    def inject_site_info():
        """注入网站基本信息"""
        return {
            'site_name': current_app.config.get('SITE_NAME', 'MyBlog'),
            'site_description': current_app.config.get('SITE_DESCRIPTION', '一个简单的博客系统')
        }
    
    @app.context_processor
    def inject_categories():
        """注入分类列表"""
        categories = Category.query.order_by(Category.name).all()
        return {'categories': categories}
    
    @app.context_processor
    def inject_tags():
        """注入标签列表"""
        tags = Tag.query.order_by(Tag.name).all()
        return {'tags': tags} 