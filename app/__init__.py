"""
Flask应用程序工厂模块
包含创建应用实例的工厂函数
"""

import time
import uuid
import json
import pytz
import random
import sqlite3
import datetime
from operator import itemgetter
from datetime import datetime, timedelta
import os

from flask import Flask, render_template, redirect, url_for, current_app, request, flash, session, abort, jsonify, make_response, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy import or_, text
from werkzeug.exceptions import HTTPException

from app.extensions import init_app, db, migrate, login_manager, cache
from app.config import DevelopmentConfig
from app.models.user import User
from app.models.role import Role
from app.models.comment import Comment, CommentStatus
from app.models.post import Post, PostStatus
from app.models.tag import Tag
from app.services.post import PostService
from app.utils.filters import *
from app.utils.logging import setup_logging

def register_blueprints(app):
    """注册蓝图"""
    # 注册授权蓝图
    from app.views.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # 注册博客蓝图
    from app.controllers.blog import blog_bp
    app.register_blueprint(blog_bp, url_prefix='/blog')
    
    # 注册管理后台蓝图
    # 确保先加载user模型
    from app.models.user import User
    
    # 确保controllers/admin蓝图被正确注册，并设置URL前缀
    from app.controllers.admin import admin_bp as admin_dashboard
    
    # 显式设置URL前缀，以防蓝图定义中没有设置
    if 'admin_dashboard' not in app.blueprints:
        app.logger.info("正在注册controllers/admin中的admin_dashboard蓝图")
        app.register_blueprint(admin_dashboard, url_prefix='/admin')
        
        # 记录已注册的路由用于调试
        app.logger.info("已注册的controllers/admin路由:")
        for rule in app.url_map.iter_rules():
            if 'admin_dashboard' in rule.endpoint:
                app.logger.info(f"{rule.endpoint}: {rule}")
    
    # 注册上传文件蓝图
    from app.controllers.admin.upload import upload_bp
    app.register_blueprint(upload_bp, url_prefix='/admin/upload')
    app.logger.info("已注册上传文件蓝图: /admin/upload")
    
    # 为原始URL路径添加处理函数
    @app.route('/blog/post/<int:post_id>')
    def original_post_detail(post_id):
        """兼容原始URL路径"""
        from app.models.post import Post
        from flask import make_response
        try:
            # 直接查询文章
            post = Post.query.get(post_id)
            if not post:
                return f"文章不存在：ID={post_id}", 404
            
            # 增加浏览量
            post.view_count += 1
            db.session.commit()
            
            # 构建HTML响应，不使用模板
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://maxcdn.bootstrapcdn.com https://cdnjs.cloudflare.com; font-src 'self' https://cdn.jsdelivr.net https://maxcdn.bootstrapcdn.com https://cdnjs.cloudflare.com https://maxcdn.bootstrapcdn.com; img-src * 'self' data: https:; connect-src 'self'">
                <title>{post.title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                    .container {{ max-width: 800px; margin: 0 auto; }}
                    .header {{ border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 20px; }}
                    .content {{ line-height: 1.6; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{post.title}</h1>
                        <p>发布时间：{post.created_at.strftime('%Y-%m-%d %H:%M:%S') if post.created_at else '未知'}</p>
                        <p>浏览次数：{post.view_count}</p>
                    </div>
                    <div class="content">
                        {post.html_content or post.content or '无内容'}
                    </div>
                    <div class="footer">
                        <p><a href="/">返回首页</a></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            response = make_response(html)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response
            
        except Exception as e:
            import traceback
            error_msg = f"访问文章出错: {str(e)}\n{traceback.format_exc()}"
            app.logger.error(error_msg)
            return error_msg, 500
    
    # 添加一个直接访问文章的路由，绕过蓝图
    @app.route('/direct_article/<int:post_id>')
    def direct_article(post_id):
        """直接访问文章，不依赖于蓝图"""
        from app.models.post import Post
        from flask import make_response
        try:
            # 直接查询文章
            post = Post.query.get(post_id)
            if not post:
                return f"文章不存在：ID={post_id}", 404
            
            # 增加浏览量
            post.view_count += 1
            db.session.commit()
            
            # 构建HTML响应，不使用模板
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://maxcdn.bootstrapcdn.com https://cdnjs.cloudflare.com; font-src 'self' https://cdn.jsdelivr.net https://maxcdn.bootstrapcdn.com https://cdnjs.cloudflare.com https://maxcdn.bootstrapcdn.com; img-src * 'self' data: https:; connect-src 'self'">
                <title>{post.title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                    .container {{ max-width: 800px; margin: 0 auto; }}
                    .header {{ border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 20px; }}
                    .content {{ line-height: 1.6; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{post.title}</h1>
                        <p>发布时间：{post.created_at.strftime('%Y-%m-%d %H:%M:%S') if post.created_at else '未知'}</p>
                        <p>浏览次数：{post.view_count}</p>
                    </div>
                    <div class="content">
                        {post.html_content or post.content or '无内容'}
                    </div>
                    <div class="footer">
                        <p><a href="/">返回首页</a></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            response = make_response(html)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response
            
        except Exception as e:
            import traceback
            error_msg = f"访问文章出错: {str(e)}\n{traceback.format_exc()}"
            app.logger.error(error_msg)
            return error_msg, 500
            
    # 添加favicon.ico路由处理
    @app.route('/favicon.ico')
    def favicon():
        """处理favicon.ico请求"""
        # 如果static目录中存在favicon.ico文件，则提供它
        if os.path.exists(os.path.join(app.static_folder, 'favicon.ico')):
            return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')
        
        # 否则返回204状态码（无内容）
        return '', 204
    
    # 添加旧的/admin/post/edit/<post_id>重定向到新的/admin/post/<post_id>/edit路由
    @app.route('/admin/post/edit/<int:post_id>')
    def admin_post_edit_format_redirect(post_id):
        """将错误格式的编辑文章URL重定向到正确的URL格式"""
        return redirect(url_for('admin_dashboard.post.edit', post_id=post_id))
    
    @app.route("/")
    def index():
        """主页重定向到博客首页"""
        return redirect(url_for("blog.index"))
    
    # 预览文章的路由
    @app.route("/admin/post/preview", methods=["POST"])
    @login_required
    def post_preview():
        """预览文章内容"""
        try:
            # 直接从请求中获取内容并预览
            from app.models.post import Post
            content = request.json.get('content', '')
            if not content:
                return jsonify({
                    'success': True,
                    'html': ''
                })
            
            html_content = Post.render_markdown(content)
            current_app.logger.debug(f"预览内容长度: {len(html_content)}")
            
            return jsonify({
                'success': True,
                'html': html_content
            })
        except Exception as e:
            current_app.logger.error(f"预览文章内容时发生错误: {str(e)}")
            current_app.logger.exception(e)
            return jsonify({
                'success': False,
                'message': f'预览失败: {str(e)}',
                'html': ''
            }), 500
    
    # 添加旧的admin/posts重定向到新的admin/post路由
    @app.route('/admin/posts')
    @login_required
    def admin_posts_redirect():
        """将旧的文章列表URL重定向到新的URL"""
        return redirect(url_for('admin_dashboard.post.index'))
    
    # 添加旧的admin/posts/new重定向到新的admin/post/create路由
    @app.route('/admin/posts/new')
    @login_required
    def admin_posts_new_redirect():
        """将旧的创建文章URL重定向到新的URL"""
        return redirect(url_for('admin_dashboard.post.create'))
    
    # 添加旧的admin/posts/<id>/edit重定向到新的admin/post/<id>/edit路由
    @app.route('/admin/posts/<int:post_id>/edit')
    @login_required
    def admin_posts_edit_redirect(post_id):
        """将旧的编辑文章URL重定向到新的URL"""
        return redirect(url_for('admin_dashboard.post.edit', post_id=post_id))
    
    # 添加旧的/admin/settings重定向
    @app.route('/admin/settings')
    @login_required
    def admin_settings_redirect():
        """将旧的设置URL重定向到新的URL"""
        return redirect(url_for('admin_dashboard.settings'))
    
    # 添加旧的/admin/categories重定向
    @app.route('/admin/categories')
    @login_required
    def admin_categories_redirect():
        """将旧的分类URL重定向到新的URL"""
        return redirect(url_for('admin_dashboard.category.index'))
    
    # 添加旧的/admin/tags重定向
    @app.route('/admin/tags')
    @login_required
    def admin_tags_redirect():
        """将旧的标签URL重定向到新的URL"""
        return redirect(url_for('admin_dashboard.tag.index'))
    
    # 添加旧的/admin/users重定向
    @app.route('/admin/users')
    @login_required
    def admin_users_redirect():
        """将旧的用户URL重定向到新的URL"""
        return redirect('/admin/user')
    
    # 添加旧的/admin/comments重定向
    @app.route('/admin/comments')
    @login_required
    def admin_comments_redirect():
        """将旧的评论URL重定向到新的URL"""
        return redirect(url_for('admin_dashboard.comment.index'))
    
    @app.route('/admin/profile')
    @login_required
    def admin_profile_redirect():
        """将旧的个人资料页面重定向到新的URL"""
        return redirect(url_for('admin_dashboard.profile'))
    
    # 添加调试路由，列出所有路由
    @app.route('/debug/routes')
    def list_routes():
        import urllib.parse
        output = []
        for rule in app.url_map.iter_rules():
            options = {}
            for arg in rule.arguments:
                options[arg] = f"[{arg}]"
            methods = ','.join(rule.methods)
            url = url_for(rule.endpoint, **options)
            line = urllib.parse.unquote(f"{rule.endpoint:<30s} {methods:<20s} {url}")
            output.append(line)
        
        # 排序以便于阅读
        output.sort()
        
        return "<pre>" + "\n".join(output) + "</pre>"

    # 添加一个特定的路由来访问文章ID 6
    @app.route('/article_6_test')
    def article_6_test():
        """测试访问文章ID 6的专用路由"""
        from app.models.post import Post
        from flask import make_response
        try:
            # 直接查询文章
            post = Post.query.get(6)
            if not post:
                return f"文章不存在：ID=6", 404
            
            # 增加浏览量
            post.view_count += 1
            db.session.commit()
            
            # 构建HTML响应，不使用模板
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://maxcdn.bootstrapcdn.com https://cdnjs.cloudflare.com; font-src 'self' https://cdn.jsdelivr.net https://maxcdn.bootstrapcdn.com https://cdnjs.cloudflare.com https://maxcdn.bootstrapcdn.com; img-src * 'self' data: https:; connect-src 'self'">
                <title>{post.title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                    .container {{ max-width: 800px; margin: 0 auto; }}
                    .header {{ border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 20px; }}
                    .content {{ line-height: 1.6; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{post.title}</h1>
                        <p>发布时间：{post.created_at.strftime('%Y-%m-%d %H:%M:%S') if post.created_at else '未知'}</p>
                        <p>浏览次数：{post.view_count}</p>
                    </div>
                    <div class="content">
                        {post.html_content or post.content or '无内容'}
                    </div>
                    <div class="footer">
                        <p><a href="/">返回首页</a></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            response = make_response(html)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response
            
        except Exception as e:
            import traceback
            error_msg = f"访问文章出错: {str(e)}\n{traceback.format_exc()}"
            app.logger.error(error_msg)
            return error_msg, 500

    # 添加一个路由来提供上传的图片文件
    @app.route('/uploads/images/<filename>')
    def uploaded_images(filename):
        """提供上传的图片文件"""
        try:
            # 从配置的目录中提供文件
            upload_folder = app.config.get('IMAGE_UPLOAD_FOLDER')
            return send_from_directory(upload_folder, filename)
        except Exception as e:
            app.logger.error(f"访问上传图片出错: {str(e)}")
            return f"图片不存在或无法访问: {filename}", 404
            
    # 兼容旧版上传路径
    @app.route('/uploads/<filename>')
    def uploaded_files(filename):
        """提供旧版上传路径的文件访问"""
        try:
            # 检查是否为图片文件
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'}):
                # 尝试从图片上传目录提供文件
                return send_from_directory(app.config.get('IMAGE_UPLOAD_FOLDER'), filename)
            
            # 从通用上传目录提供文件
            return send_from_directory(app.config.get('UPLOAD_FOLDER'), filename)
        except Exception as e:
            app.logger.error(f"访问上传文件出错: {str(e)}")
            return f"文件不存在或无法访问: {filename}", 404

def create_app(config_class=DevelopmentConfig):
    """创建并返回一个Flask应用实例"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化扩展
    init_app(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册模板过滤器
    init_filters(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册Hook函数 - 这个函数似乎不存在
    # register_hooks(app)
    
    # 设置日志 - 不接受参数
    setup_logging()
    
    # 应用安全中间件
    from app.middleware.security import secure_headers
    app.after_request(secure_headers()(lambda r: r))
    
    # 另一种方法：直接添加一个处理函数来专门处理CSP
    @app.after_request
    def update_csp_header(response):
        # 直接设置完整的CSP头
        csp = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://maxcdn.bootstrapcdn.com https://cdnjs.cloudflare.com; font-src 'self' https://cdn.jsdelivr.net https://maxcdn.bootstrapcdn.com https://cdnjs.cloudflare.com; img-src * 'self' data: https:; connect-src 'self'"
        response.headers['Content-Security-Policy'] = csp
        return response
    
    # 添加兼容性路由重定向
    # 添加 /admin/category/ID/edit 路由重定向到 /admin/categories/ID/edit
    @app.route('/admin/category/<int:category_id>/edit', methods=['GET', 'POST'])
    def category_edit_redirect(category_id):
        if request.method == 'POST':
            # 对于POST请求，调用category模块的edit函数处理，保持原始响应
            from app.controllers.admin.category import edit
            return edit(category_id)
        # 对于GET请求，重定向到正确的URL
        return redirect(url_for('admin_dashboard.category.edit', category_id=category_id))
    
    # 添加 /admin/tag/create 路由重定向到 /admin/tags/create
    @app.route('/admin/tag/create', methods=['GET', 'POST'])
    def tag_create_redirect():
        return redirect(url_for('admin_dashboard.tag.create'))
    
    # 添加 /admin/comment/reject/ID 路由重定向到 /admin/comments/ID/reject
    @app.route('/admin/comment/reject/<int:comment_id>', methods=['POST'])
    def comment_reject_redirect(comment_id):
        return redirect(url_for('admin_dashboard.comment.reject', comment_id=comment_id))
    
    # 修正：/admin/users/ID/edit 路由重定向到 /admin/user/ID/edit
    @app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
    def user_edit_redirect(user_id):
        return redirect(url_for('admin_dashboard.user.edit', user_id=user_id))
    
    # 初始化数据库
    with app.app_context():
        db.create_all()
        # 初始化角色
        Role.insert_roles()
        # 确保超级管理员用户存在
        User.create_admin_user_if_not_exists()
        
        # 设置默认首页
        from app.utils.site import ensure_default_settings
        ensure_default_settings()
    
    return app

def fix_anonymous_comments_status():
    """修复匿名评论的状态"""
    try:
        # 直接使用SQL更新状态
        connection = sqlite3.connect(current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        cursor = connection.cursor()
        cursor.execute("UPDATE comments SET status = ? WHERE status = ?", (CommentStatus.APPROVED.value, 0))
        fixed_count = cursor.rowcount
        connection.commit()
        connection.close()
        
        if fixed_count > 0:
            current_app.logger.info(f"已自动修正 {fixed_count} 条匿名评论的状态")
    except Exception as e:
        current_app.logger.error(f"修复匿名评论状态失败: {str(e)}")

def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return render_template('errors/generic.html', error=e), e.code

