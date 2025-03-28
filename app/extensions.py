"""
文件名：extensions.py
描述：Flask扩展初始化
作者：denny
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from flask_session import Session
# from flask_mail import Mail  # 注释掉flask_mail导入
from flask import request, jsonify, redirect, url_for, current_app, session, g, flash, render_template, make_response
from datetime import datetime, UTC
import secrets
import os
import json
import logging
from logging.handlers import RotatingFileHandler
from app.config import Config
# from flask_moment import Moment  # 注释掉moment导入
# from flask_ckeditor import CKEditor  # 注释掉ckeditor导入
# from flask_cors import CORS  # 注释掉CORS导入
# from flask_babel import Babel  # 注释掉babel导入
# from flask_limiter import Limiter  # 注释掉limiter导入
# from flask_limiter.util import get_remote_address  # 注释掉get_remote_address导入
# from flask_compress import Compress  # 注释掉compress导入
# from flask_debugtoolbar import DebugToolbarExtension  # 注释掉debugtoolbar导入
# from flask_assets import Environment  # 注释掉assets导入
# from flask_marshmallow import Marshmallow  # 注释掉marshmallow导入
# from flask_socketio import SocketIO  # 注释掉socketio导入
# from flask_apscheduler import APScheduler  # 注释掉apscheduler导入
# from flask_uploads import UploadSet, IMAGES, configure_uploads  # 注释掉uploads导入
# from flask_avatars import Avatars  # 注释掉avatars导入
# from flask_sitemap import Sitemap  # 注释掉sitemap导入
# from flask_whooshee import Whooshee  # 注释掉whooshee导入
# from flask_dropzone import Dropzone  # 注释掉dropzone导入
# from flask_admin import Admin  # 注释掉admin导入
# from flask_principal import Principal  # 注释掉principal导入
# from flask_jwt_extended import JWTManager  # 注释掉jwt导入
# from authlib.integrations.flask_client import OAuth  # 注释掉oauth导入
# from flask_restful import Api  # 注释掉restful导入
# from flask_graphql import GraphQLView  # 注释掉graphql导入
# from flask_swagger import swagger  # 注释掉swagger导入
# from flask_swagger_ui import get_swaggerui_blueprint  # 注释掉swagger_ui导入
# from flask_talisman import Talisman  # 注释掉talisman导入
# from flask_htmlmin import HTMLMIN  # 注释掉htmlmin导入
# from flask_redis import FlaskRedis  # 注释掉redis导入

# 创建扩展实例
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
session = Session()
# mail = Mail()  # 注释掉mail实例
# moment = Moment()  # 注释掉moment实例
# babel = Babel()  # 注释掉babel实例
# cors = CORS()  # 注释掉CORS实例
# limiter = Limiter(key_func=get_remote_address)  # 注释掉limiter实例
# compress = Compress()  # 注释掉compress实例
# debug_toolbar = DebugToolbarExtension()  # 注释掉debug_toolbar实例
# assets = Environment()  # 注释掉assets实例
# ma = Marshmallow()  # 注释掉ma实例
# socketio = SocketIO()  # 注释掉socketio实例
# scheduler = APScheduler()  # 注释掉scheduler实例
# ckeditor = CKEditor()  # 注释掉ckeditor实例
# avatars = Avatars()  # 注释掉avatars实例
# sitemap = Sitemap()  # 注释掉sitemap实例
# whooshee = Whooshee()  # 注释掉whooshee实例
# dropzone = Dropzone()  # 注释掉dropzone实例
# admin = Admin()  # 注释掉admin实例
# principal = Principal()  # 注释掉principal实例
# jwt = JWTManager()  # 注释掉jwt实例
# oauth = OAuth()  # 注释掉oauth实例
# api = Api()  # 注释掉api实例
# talisman = Talisman()  # 注释掉talisman实例
# htmlmin = HTMLMIN()  # 注释掉htmlmin实例
# redis_client = FlaskRedis()  # 注释掉redis_client实例
# images = UploadSet('images', IMAGES)  # 注释掉images实例

def init_app(app):
    """初始化所有扩展"""
    # 配置日志
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/myblog.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('MyBlog startup')

    # 初始化数据库
    if app.config['TESTING']:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    # 初始化数据库相关扩展
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 初始化登录管理器
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = None  # 禁用会话保护，以便测试
    
    # 初始化会话
    session.init_app(app)
    
    # 初始化缓存
    cache.init_app(app)
    
    # 初始化Redis客户端
    # redis_client.init_app(app)  # 注释掉redis_client初始化
    
    # 初始化其他扩展
    # mail.init_app(app)  # 注释掉mail初始化
    # moment.init_app(app)  # 注释掉moment初始化
    # babel.init_app(app)  # 注释掉babel初始化
    # cors.init_app(app)  # 注释掉CORS初始化
    # limiter.init_app(app)  # 注释掉limiter初始化
    # compress.init_app(app)  # 注释掉compress初始化
    # assets.init_app(app)  # 注释掉assets初始化
    # ma.init_app(app)  # 注释掉ma初始化
    # socketio.init_app(app)  # 注释掉socketio初始化
    # scheduler.init_app(app)  # 注释掉scheduler初始化
    # ckeditor.init_app(app)  # 注释掉ckeditor初始化
    # avatars.init_app(app)  # 注释掉avatars初始化
    # sitemap.init_app(app)  # 注释掉sitemap初始化
    # whooshee.init_app(app)  # 注释掉whooshee初始化
    # dropzone.init_app(app)  # 注释掉dropzone初始化
    # admin.init_app(app)  # 注释掉admin初始化
    # principal.init_app(app)  # 注释掉principal初始化
    # jwt.init_app(app)  # 注释掉jwt初始化
    # oauth.init_app(app)  # 注释掉oauth初始化
    # api.init_app(app)  # 注释掉api初始化

    # 配置Talisman CSP
    csp = {
        'default-src': ['\'self\''],
        'script-src': ['\'self\'', '\'unsafe-inline\'', '\'unsafe-eval\'', 'https://cdn.jsdelivr.net', 'https://code.jquery.com'],
        'style-src': ['\'self\'', '\'unsafe-inline\'', 'https://cdn.jsdelivr.net', 'https://maxcdn.bootstrapcdn.com', 'https://cdnjs.cloudflare.com'],
        'font-src': ['\'self\'', 'https://cdn.jsdelivr.net', 'https://maxcdn.bootstrapcdn.com', 'https://cdnjs.cloudflare.com', 'https://maxcdn.bootstrapcdn.com'],
        'img-src': ['\'self\'', 'data:'],
    }
    # talisman.init_app(
    #     app,
    #     content_security_policy=csp,
    #     force_https=False,
    #     content_security_policy_report_only=False  # 不使用report-only模式
    # )  # 注释掉talisman初始化
    
    # htmlmin.init_app(app)  # 注释掉htmlmin初始化
    # configure_uploads(app, images)  # 注释掉configure_uploads初始化
    
    # 注册用户加载函数
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        """加载用户
        
        Args:
            user_id: 用户ID（字符串类型）
            
        Returns:
            User | None: 如果用户存在且激活则返回用户对象，否则返回None
        """
        if not user_id:
            current_app.logger.warning('load_user: user_id is empty')
            return None
            
        try:
            # 尝试将user_id转换为整数
            id_value = int(user_id)
            user = User.query.get(id_value)
            
            if user is None:
                current_app.logger.warning(f'load_user: User not found for id {id_value}')
                return None
                
            if not user.is_active:
                current_app.logger.warning(f'load_user: User {id_value} is not active')
                return None
                
            return user
            
        except (ValueError, TypeError) as e:
            current_app.logger.error(f'load_user: Failed to convert user_id {user_id} to int: {str(e)}')
            return None
        except Exception as e:
            current_app.logger.error(f'load_user: Unexpected error: {str(e)}')
            return None

    # 确保 session目录存在
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    @app.after_request
    def add_security_headers(response):
        """添加安全相关的响应头"""
        # 设置安全头
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    # 注册错误处理器
    @app.errorhandler(400)
    def bad_request(e):
        """处理400错误"""
        current_app.logger.warning(f'Bad Request: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

    @app.errorhandler(401)
    def unauthorized(e):
        """处理401错误"""
        current_app.logger.warning(f'Unauthorized: {str(e)}')
        return jsonify({
            'success': False,
            'message': '未授权访问'
        }), 401

    @app.errorhandler(403)
    def forbidden(e):
        """处理403错误"""
        current_app.logger.warning(f'Forbidden: {str(e)}')
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': False,
                'message': '禁止访问'
            }), 403
        # 判断是否来自管理后台
        is_admin = request.path.startswith('/admin')
        return render_template('errors/403.html', 
                             message=str(e), 
                             is_admin=is_admin), 403

    @app.errorhandler(404)
    def not_found(e):
        """处理404错误"""
        current_app.logger.warning(f'Not Found: {str(e)}')
        return jsonify({
            'success': False,
            'message': '页面不存在'
        }), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        """处理500错误"""
        current_app.logger.error(f'Server Error: {str(e)}')
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '服务器内部错误'
        }), 500

    # 添加数据库会话清理
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if exception:
            current_app.logger.error(f'Exception during request: {str(exception)}')
        db.session.remove()

    app.logger.info('扩展初始化完成')