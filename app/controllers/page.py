"""
文件名：page.py
描述：页面控制器
作者：denny
"""

from flask import Blueprint, render_template, request, jsonify
from app.services import PostService
from app.utils.markdown import markdown_to_html

page_bp = Blueprint('page', __name__)
post_service = PostService()

@page_bp.route('/about')
def about():
    """关于页面"""
    # 从配置文件中读取关于页面内容
    content = """
# 关于我

这是一个使用 Flask 开发的个人博客系统。

## 主要功能

- 文章管理
- 分类管理
- 标签管理
- Markdown 支持
- 图片上传
- 评论系统
- 搜索功能
- 归档功能

## 技术栈

- Python
- Flask
- SQLAlchemy
- Bootstrap
- jQuery
"""
    html = markdown_to_html(content)
    return render_template('page/about.html', content=html)

@page_bp.route('/links')
def links():
    """友情链接"""
    links = [
        {
            'name': 'Flask',
            'url': 'https://flask.palletsprojects.com/',
            'description': 'Python Web 开发框架'
        },
        {
            'name': 'SQLAlchemy',
            'url': 'https://www.sqlalchemy.org/',
            'description': 'Python SQL 工具包和 ORM'
        },
        {
            'name': 'Bootstrap',
            'url': 'https://getbootstrap.com/',
            'description': '前端开发框架'
        }
    ]
    return render_template('page/links.html', links=links) 