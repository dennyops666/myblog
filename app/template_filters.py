import re
from datetime import datetime
from markupsafe import Markup
import markdown
import bleach

def register_template_filters(app):
    """注册模板过滤器"""
    
    @app.template_filter('datetime')
    def format_datetime(value, format='%Y-%m-%d %H:%M'):
        """格式化日期时间"""
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value.strftime(format)
    
    @app.template_filter('markdown')
    def markdown_to_html(text):
        """将Markdown转换为HTML"""
        allowed_tags = [
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
            'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'hr',
            'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
        ]
        
        allowed_attrs = {
            'a': ['href', 'title'],
            'abbr': ['title'],
            'acronym': ['title'],
            'img': ['src', 'alt', 'title']
        }
        
        html = markdown.markdown(
            text,
            extensions=[
                'markdown.extensions.fenced_code',
                'markdown.extensions.codehilite',
                'markdown.extensions.tables',
                'markdown.extensions.toc'
            ]
        )
        
        clean_html = bleach.clean(
            html,
            tags=allowed_tags,
            attributes=allowed_attrs,
            strip=True
        )
        
        return Markup(clean_html)
    
    @app.template_filter('truncate')
    def truncate_text(text, length=200, suffix='...'):
        """截断文本"""
        if not text:
            return ''
            
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        if len(text) <= length:
            return text
        return text[:length].rstrip() + suffix 