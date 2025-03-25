"""
文件名：config.py
描述：应用配置
作者：denny
创建日期：2024-03-21
"""

import os
import secrets
from datetime import timedelta

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BLOG_TITLE = 'My Blog'
    POSTS_PER_PAGE = int(os.getenv('POSTS_PER_PAGE', 10))
    
    # 禁用CSRF保护
    WTF_CSRF_ENABLED = False
    WTF_CSRF_CHECK_DEFAULT = False
    WTF_CSRF_METHODS = []  # 空列表表示不检查任何方法
    
    # 基础路径配置
    BASE_DIR = '/data/myblog'
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')
    
    # 上传配置
    UPLOAD_FOLDER = os.path.join(INSTANCE_DIR, 'uploads')
    IMAGE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    IMAGE_MAX_DIMENSION = 2048  # 图片最大尺寸
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 安全配置
    SESSION_PROTECTION = 'strong'
    
    # 日志配置
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(module)s:%(lineno)d - %(message)s'
    LOG_LEVEL = 'INFO'
    LOG_FILE = os.path.join(LOGS_DIR, 'app.log')
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保必要的目录存在
        os.makedirs(Config.INSTANCE_DIR, exist_ok=True)
        os.makedirs(Config.LOGS_DIR, exist_ok=True)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.IMAGE_UPLOAD_FOLDER, exist_ok=True)
        
        # 配置日志
        import logging
        from logging.handlers import RotatingFileHandler
        
        # 创建日志处理器
        file_handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=Config.LOG_MAX_SIZE,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        
        # 设置日志格式
        formatter = logging.Formatter(Config.LOG_FORMAT)
        file_handler.setFormatter(formatter)
        
        # 设置日志级别
        file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # 添加处理器到应用
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # 记录应用启动日志
        app.logger.info('应用启动 - 环境: %s', app.config['ENV'])

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///instance/blog-dev.db'
    
    # 开发环境特定的日志配置
    LOG_LEVEL = 'DEBUG'
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(module)s:%(lineno)d - %(message)s\n    Request: %(url)s %(method)s\n    Data: %(data)s\n    Response: %(response)s'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 添加控制台日志处理器
        import logging
        import sys
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, cls.LOG_LEVEL))
        console_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))
        
        app.logger.addHandler(console_handler)
        app.logger.setLevel(getattr(logging, cls.LOG_LEVEL))
        
        # 记录开发环境启动日志
        app.logger.debug('开发环境启动 - 调试模式已启用')

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(Config.INSTANCE_DIR, 'blog-test.db')
    
    # 测试环境上传配置
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'test_uploads')
    IMAGE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
    
    @staticmethod
    def init_app(app):
        """初始化测试环境配置"""
        Config.init_app(app)
        
        # 确保测试上传目录存在
        os.makedirs(TestingConfig.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(TestingConfig.IMAGE_UPLOAD_FOLDER, exist_ok=True)

class ProductionConfig(Config):
    """生产环境配置"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(Config.INSTANCE_DIR, 'blog.db')
    
    @classmethod
    def init_app(cls, app):
        """生产环境特定的初始化"""
        Config.init_app(app)
        
        # 日志处理
        import logging
        from logging.handlers import RotatingFileHandler
            
        file_handler = RotatingFileHandler(
            os.path.join(Config.LOGS_DIR, 'myblog.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('MyBlog 启动')
        app.logger.info('配置模式: production')
        app.logger.info('调试模式: %s', app.debug)
        app.logger.info('日志目录: %s', Config.LOGS_DIR)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 