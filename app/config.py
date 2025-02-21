"""
文件名：config.py
描述：应用配置文件
作者：denny
创建日期：2025-02-16
"""

import os
from datetime import timedelta

class Config:
    """基础配置类"""
    # 基本配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 安全配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_SSL_STRICT = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:////' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'blog.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 缓存配置
    CACHE_TYPE = 'simple'
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
    
    @staticmethod
    def init_app(app):
        """初始化应用"""
        # 确保上传目录存在
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.IMAGE_UPLOAD_FOLDER, exist_ok=True)

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # 安全配置
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # 安全配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_SSL_STRICT = False
    WTF_CSRF_TIME_LIMIT = None  # 禁用CSRF令牌过期
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    
    # 认证配置
    LOGIN_DISABLED = False
    LOGIN_VIEW = 'auth.login'
    SESSION_PROTECTION = 'basic'
    
    # API配置
    API_TOKEN_ENABLED = True
    API_TOKEN_HEADER = 'X-CSRF-Token'
    
    # 上传配置
    UPLOAD_FOLDER = '/tmp/test_uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    @staticmethod
    def init_app(app):
        """初始化应用"""
        Config.init_app(app)
        
        # 确保测试上传目录存在
        os.makedirs(TestingConfig.UPLOAD_FOLDER, exist_ok=True)

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
