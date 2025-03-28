"""
文件名：test.py
描述：测试控制器
作者：denny
"""

from flask import render_template, jsonify, current_app
from flask_login import login_required
from . import admin_bp
import datetime

# 定义一个测试路由，提供硬编码的测试数据
@admin_bp.route('/test')
@login_required
def test():
    """测试页面，显示硬编码的数据"""
    try:
        current_app.logger.info("加载测试页面...")
        
        # 创建测试文章数据类
        class TestPost:
            def __init__(self, id, title, created_at, status_name, view_count=0):
                self.id = id
                self.title = title
                self.created_at = created_at
                self.status = type('obj', (object,), {'name': status_name})
                self.view_count = view_count
        
        # 创建测试数据
        now = datetime.datetime.now()
        test_posts = [
            TestPost(1, "测试文章1", now, "PUBLISHED", 100),
            TestPost(2, "测试文章2", now, "DRAFT", 50),
            TestPost(3, "测试文章3", now, "ARCHIVED", 75),
            TestPost(4, "测试文章4", now, "PUBLISHED", 120),
            TestPost(5, "测试文章5", now, "DRAFT", 30)
        ]
        
        current_app.logger.info(f"创建了 {len(test_posts)} 篇测试文章")
        
        # 将测试数据传递给模板
        return render_template('admin/test.html',
                            post_count=5,
                            category_count=3,
                            published_count=2,
                            draft_count=2,
                            tag_count=10,
                            recent_posts=test_posts)
    except Exception as e:
        current_app.logger.error(f"加载测试页面失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'测试页面加载失败: {str(e)}'
        }) 