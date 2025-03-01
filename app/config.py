"""
文件名：config.py
描述：应用配置文件
作者：denny
创建日期：2025-02-16
"""

import os
import tempfile
from datetime import timedelta

class Config:
    """基础配置类"""
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 安全配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # CSRF 令牌有效期（秒）
    WTF_CSRF_SSL_STRICT = False  # 开发环境不强制 HTTPS
    WTF_CSRF_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}  # 需要 CSRF 保护的方法
    SESSION_COOKIE_SECURE = False  # 开发环境不强制 HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'blog.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # 缓存配置
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # 图片上传配置
    IMAGE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
    IMAGE_ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS
    IMAGE_MAX_SIZE = 5 * 1024 * 1024  # 5MB
    IMAGE_MAX_DIMENSION = 1024  # 最大图片尺寸
    IMAGE_QUALITY = 85  # 图片质量
    IMAGE_FORMAT = 'JPEG'  # 默认保存格式
    
    # 分页配置
    POSTS_PER_PAGE = 10
    COMMENTS_PER_PAGE = 20
    ADMIN_POSTS_PER_PAGE = 15
    
    # 博客配置
    BLOG_TITLE = 'MyBlog'
    BLOG_SUBTITLE = '分享技术，记录生活'
    BLOG_AUTHOR = 'Denny'
    BLOG_EMAIL = 'admin@example.com'
    
    # 会话配置
    SESSION_TYPE = 'sqlalchemy'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_SQLALCHEMY_TABLE = 'sessions'
    SESSION_REFRESH_EACH_REQUEST = True
    
    # 登录配置
    LOGIN_DISABLED = False
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    
    @staticmethod
    def init_app(app):
        """初始化应用"""
        # 创建上传目录
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['IMAGE_UPLOAD_FOLDER'], exist_ok=True)
        
        # 设置 SESSION_SQLALCHEMY
        from app.extensions import db
        app.config['SESSION_SQLALCHEMY'] = db

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False
    WTF_CSRF_SSL_STRICT = False  # 开发环境不强制 HTTPS
    SESSION_COOKIE_SECURE = False  # 开发环境不强制 HTTPS
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'blog-dev.db')
    SQLALCHEMY_ECHO = True  # 输出 SQL 语句
    
    # 开发环境使用不同的上传目录
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dev_uploads')
    IMAGE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
    
    # 开发环境缓存配置
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 0  # 禁用缓存
    
    # 开发环境会话配置
    SESSION_COOKIE_SAMESITE = None  # 开发环境禁用 SameSite
    
    @classmethod
    def init_app(cls, app):
        """初始化开发环境应用"""
        Config.init_app(app)
        app.config['EXPLAIN_TEMPLATE_LOADING'] = True  # 显示模板加载信息

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False  # 在测试环境中禁用 CSRF 保护
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SERVER_NAME = 'localhost'
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB for testing
    
    # 会话配置
    SESSION_TYPE = 'sqlalchemy'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    @classmethod
    def init_app(cls, app):
        """初始化测试应用"""
        Config.init_app(app)
        
        # 确保测试上传目录存在
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['IMAGE_UPLOAD_FOLDER'], exist_ok=True)

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    WTF_CSRF_SSL_STRICT = True
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'blog.db')
    
    # 生产环境图片配置
    IMAGE_MAX_DIMENSION = 1920  # 更大的最大尺寸
    IMAGE_QUALITY = 90  # 更高的图片质量
    
    # 生产环境安全配置
    SESSION_COOKIE_SAMESITE = 'Strict'  # 生产环境使用严格模式
    WTF_CSRF_TIME_LIMIT = 1800  # 生产环境缩短 CSRF 令牌有效期
    
    @classmethod
    def init_app(cls, app):
        """初始化生产环境应用"""
        Config.init_app(app)
        
        # 在生产环境中使用安全的会话配置
        app.config.update(
            SESSION_COOKIE_SECURE=True,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Strict',
            PERMANENT_SESSION_LIFETIME=timedelta(days=1)
        )

# 配置字典
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
