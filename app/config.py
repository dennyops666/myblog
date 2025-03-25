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
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 禁用 SERVER_NAME 和 PREFERRED_URL_SCHEME
    SERVER_NAME = None
    PREFERRED_URL_SCHEME = None
    
    # 禁用CSRF保护
    WTF_CSRF_ENABLED = False
    WTF_CSRF_CHECK_DEFAULT = False
    WTF_CSRF_METHODS = []  # 空列表表示不检查任何方法
    
    # 日志配置
    LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    LOG_FILE = os.path.join(LOGS_DIR, 'myblog.log')
    ERROR_LOG_FILE = os.path.join(LOGS_DIR, 'error.log')
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    LOG_FORMAT = '%(asctime)s [%(levelname)s] [PID:%(process_id)d] %(module)s:%(lineno)d - %(message)s\n'\
                'Context: {\n'\
                '    URL: %(url)s\n'\
                '    Method: %(method)s\n'\
                '    IP: %(remote_addr)s\n'\
                '    User-Agent: %(user_agent)s\n'\
                '    Data: %(data)s\n'\
                '}'
    LOG_LEVEL = 'INFO'
    
    # 数据库配置
    INSTANCE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///:memory:'
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
    
    # Flask-Uploads配置
    UPLOADED_IMAGES_DEST = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'uploads', 'images')
    UPLOADED_IMAGES_URL = '/uploads/images/'
    UPLOADED_IMAGES_ALLOW = ALLOWED_EXTENSIONS
    UPLOADED_IMAGES_DENY = set()
    
    # 图片上传配置
    IMAGE_UPLOAD_FOLDER = UPLOADED_IMAGES_DEST
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
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'flask_session')
    SESSION_FILE_THRESHOLD = 500
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'myblog_'
    SESSION_COOKIE_NAME = 'myblog_session'
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_REFRESH_EACH_REQUEST = True
    
    # 记住我 cookie 配置
    REMEMBER_COOKIE_NAME = 'remember_token'
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    
    # 登录配置
    LOGIN_DISABLED = False
    
    @staticmethod
    def init_app(app):
        """初始化应用"""
        # 创建上传目录和日志目录
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['IMAGE_UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['LOGS_DIR'], exist_ok=True)
        
        # 配置日志格式化器
        import logging
        from flask import request, has_request_context
        
        class RequestFormatter(logging.Formatter):
            def format(self, record):
                if has_request_context():
                    # 请求基本信息
                    record.url = request.url
                    record.method = request.method
                    record.remote_addr = request.remote_addr
                    record.user_agent = request.headers.get('User-Agent', '-')
                    record.referrer = request.referrer or '-'
                    record.endpoint = request.endpoint or '-'
                    
                    # 用户信息
                    from flask_login import current_user
                    record.user_id = str(current_user.id) if current_user.is_authenticated else '-'
                    record.username = current_user.username if current_user.is_authenticated else '-'
                    
                    # 请求数据
                    try:
                        data = {}
                        # JSON 数据
                        if request.is_json:
                            data.update(request.get_json(silent=True) or {})
                        # 表单数据
                        if request.form:
                            data.update(request.form.to_dict())
                        # URL 参数
                        if request.args:
                            data.update(request.args.to_dict())
                        # 文件上传
                        if request.files:
                            data['files'] = [
                                {'name': f.filename, 'type': f.content_type}
                                for f in request.files.values()
                            ]
                        
                        # 移除敏感信息
                        sensitive_fields = ['password', 'token', 'secret', 'key', 'auth']
                        for field in sensitive_fields:
                            if field in data:
                                data[field] = '******'
                        
                        record.data = str(data)
                    except Exception as e:
                        record.data = f'Error parsing request data: {str(e)}'
                    
                    # 响应信息
                    response = getattr(request, '_response', None)
                    if response:
                        record.response = {
                            'status_code': response.status_code,
                            'content_type': response.content_type,
                            'content_length': response.content_length
                        }
                    else:
                        record.response = '-'
                else:
                    # 非请求上下文
                    record.url = '-'
                    record.method = '-'
                    record.remote_addr = '-'
                    record.user_agent = '-'
                    record.referrer = '-'
                    record.endpoint = '-'
                    record.user_id = '-'
                    record.username = '-'
                    record.data = '-'
                    record.response = '-'
                
                if record.exc_info:
                    record.exc_info = '\n'.join(
                        logging.Formatter().formatException(record.exc_info).split('\n')
                    )
                else:
                    record.exc_info = ''
                
                # 添加进程 ID
                import os
                record.process_id = os.getpid()
                
                return super().format(record)
        
        # 创建应用日志处理器
        from logging.handlers import RotatingFileHandler
        
        # 创建应用日志处理器
        app_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_SIZE'],
            backupCount=app.config['LOG_BACKUP_COUNT'],
            encoding='utf-8'
        )
        app_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app_handler.setFormatter(RequestFormatter(app.config['LOG_FORMAT']))
        
        # 创建错误日志处理器
        error_handler = RotatingFileHandler(
            app.config['ERROR_LOG_FILE'],
            maxBytes=app.config['LOG_MAX_SIZE'],
            backupCount=app.config['LOG_BACKUP_COUNT'],
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(RequestFormatter(
            '%(asctime)s [%(levelname)s] %(module)s:%(lineno)d - %(message)s\n'
            'Error Details: {\n'
            '    Exception: %(exc_info)s\n'
            '    Request: %(url)s %(method)s\n'
            '    IP: %(remote_addr)s\n'
            '    Data: %(data)s\n'
            '}'
        ))
        
        # 添加处理器到应用
        app.logger.addHandler(app_handler)
        app.logger.addHandler(error_handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        
        # 记录应用启动日志
        env_type = 'production' if not app.debug else 'development'
        app.logger.info('应用启动 - 环境: %s', env_type)
        
        # 设置 SESSION_SQLALCHEMY
        from app.extensions import db
        app.config['SESSION_SQLALCHEMY'] = db

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:////data/myblog/instance/blog-dev.db'
    SQLALCHEMY_ECHO = True  # 输出 SQL 语句
    
    # 开发环境日志配置
    LOG_LEVEL = 'DEBUG'
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(module)s:%(lineno)d - %(message)s\n'\
                'Debug Info: {\n'\
                '    Request: %(url)s %(method)s\n'\
                '    Data: %(data)s\n'\
                '    Response: %(response)s\n'\
                '}'
    
    # 开发环境使用不同的上传目录
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dev_uploads')
    IMAGE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
    
    # 开发环境缓存配置
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 0  # 禁用缓存
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 配置日志
        import logging
        import sys
        from logging.handlers import RotatingFileHandler
        
        # 确保日志目录存在
        os.makedirs(Config.LOGS_DIR, exist_ok=True)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))
        
        # 创建文件处理器
        file_handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=Config.LOG_MAX_SIZE,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))
        
        # 创建错误日志处理器
        error_handler = RotatingFileHandler(
            Config.ERROR_LOG_FILE,
            maxBytes=Config.LOG_MAX_SIZE,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(module)s:%(lineno)d - %(message)s\n'
            'Exception: %(exc_info)s\n'
            'Request: %(url)s %(method)s\n'
            'IP: %(remote_addr)s\n'
            'Data: %(data)s'
        ))
        
        # 添加处理器到应用
        app.logger.addHandler(console_handler)
        app.logger.addHandler(file_handler)
        app.logger.addHandler(error_handler)
        app.logger.setLevel(logging.DEBUG)
        
        # 记录开发环境启动日志
        app.logger.debug('开发环境启动 - 调试模式已启用')

class TestingConfig(Config):
    """测试环境配置"""
    # 基本配置
    TESTING = True
    DEBUG = False
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'test.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'pool_timeout': 10,
        'pool_recycle': 60,
        'connect_args': {'check_same_thread': False}
    }
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB for testing
    
    @classmethod
    def init_app(cls, app):
        """初始化测试应用"""
        Config.init_app(app)
        
        # 确保测试目录存在
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['IMAGE_UPLOAD_FOLDER'], exist_ok=True)
        
        # 导入所有模型以确保它们被正确注册
        from app.models.role import Role
        from app.models.user import User
        from app.models.category import Category
        from app.models.tag import Tag
        from app.models.post import Post
        from app.models.comment import Comment
        from app.models.notification import Notification

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'blog.db')
    
    # 生产环境图片配置
    IMAGE_MAX_DIMENSION = 1920  # 更大的最大尺寸
    IMAGE_QUALITY = 90  # 更高的图片质量
    
    @classmethod
    def init_app(cls, app):
        """初始化生产环境应用"""
        Config.init_app(app)
        
        # 配置日志
        import logging
        from logging.handlers import RotatingFileHandler
        
        # 确保日志目录存在
        os.makedirs(Config.LOGS_DIR, exist_ok=True)
        
        # 创建应用日志处理器
        app_handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=Config.LOG_MAX_SIZE,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
        
        # 创建错误日志处理器
        error_handler = RotatingFileHandler(
            Config.ERROR_LOG_FILE,
            maxBytes=Config.LOG_MAX_SIZE,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(module)s:%(lineno)d - %(message)s\n'
            'Exception: %(exc_info)s\n'
            'Request: %(url)s %(method)s\n'
            'IP: %(remote_addr)s'
        ))
        
        # 添加处理器到应用
        app.logger.addHandler(app_handler)
        app.logger.addHandler(error_handler)
        app.logger.setLevel(logging.INFO)
        
        # 记录应用启动日志
        app.logger.info('生产环境启动 - 安全模式已启用')

# 配置字典
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
