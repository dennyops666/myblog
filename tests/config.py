"""
测试配置
"""

import os
import tempfile
from datetime import timedelta, datetime, UTC

# 测试配置
class TestingConfig:
    TESTING = True
    
    # 安全配置
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False  # 禁用 CSRF 保护，便于测试
    WTF_CSRF_SECRET_KEY = 'test-csrf-secret-key'
    
    # 会话配置
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(tempfile.gettempdir(), 'test_sessions')
    SESSION_FILE_THRESHOLD = 500
    SESSION_FILE_MODE = 0o600
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'myblog_test_'
    SESSION_COOKIE_NAME = 'myblog_session'
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # 与记住我 cookie 保持一致
    SESSION_REFRESH_EACH_REQUEST = True
    
    # 记住我 cookie 配置
    REMEMBER_COOKIE_NAME = 'remember_token'
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    
    # 数据库配置
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    TEST_DB = os.path.join(tempfile.gettempdir(), 'test.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{TEST_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True  # 在测试时显示SQL查询
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # 自动检测连接是否有效
        'pool_recycle': 3600,  # 每小时回收连接
        'connect_args': {
            'check_same_thread': False,  # 允许多线程访问
            'timeout': 30,  # 连接超时时间
            'isolation_level': None  # 使用自动提交模式
        }
    }
    SQLALCHEMY_POOL_SIZE = 1  # 单个连接池
    SQLALCHEMY_MAX_OVERFLOW = 0  # 不允许超出连接池大小
    
    # 上传配置
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'tests', 'test_uploads')
    IMAGE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    IMAGE_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    IMAGE_MAX_SIZE = 5 * 1024 * 1024  # 5MB
    IMAGE_MAX_DIMENSION = 2048  # 最大图片尺寸
    IMAGE_QUALITY = 85  # 图片质量
    IMAGE_FORMAT = 'JPEG'  # 默认保存格式
    
    # 文件上传配置
    UPLOADED_IMAGES_DEST = os.path.join(BASE_DIR, 'tests', 'test_uploads', 'images')
    UPLOADED_IMAGES_URL = '/uploads/images/'
    UPLOADED_IMAGES_ALLOW = ('jpg', 'jpeg', 'png', 'gif')
    UPLOADED_IMAGES_DENY = ('php', 'html', 'js', 'css')
    
    # 日志配置
    LOG_DIR = os.path.join(BASE_DIR, 'tests', 'logs')
    LOG_LEVEL = 'DEBUG'
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(module)s:%(lineno)d - %(message)s'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # 调试配置
    DEBUG = True
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_PROFILER_ENABLED = True
    PROPAGATE_EXCEPTIONS = True
    
    # 错误处理配置
    ERROR_404_HELP = False
    ERROR_INCLUDE_MESSAGE = True
    TRAP_HTTP_EXCEPTIONS = True
    TRAP_BAD_REQUEST_ERRORS = True
    PREFERRED_URL_SCHEME = 'http'
    
    # 异常配置
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    MAX_JSON_PACKET_LENGTH = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def init_app(cls, app):
        """初始化应用"""
        # 创建必要的目录
        os.makedirs(cls.LOG_DIR, exist_ok=True)
        os.makedirs(cls.SESSION_FILE_DIR, exist_ok=True)
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.IMAGE_UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.UPLOADED_IMAGES_DEST, exist_ok=True)
        
        # 创建测试数据库目录
        db_dir = os.path.dirname(cls.TEST_DB)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # 创建日志文件
        log_files = ['test.log', 'error.log', 'security.log', 'db.log']
        for log_file in log_files:
            open(os.path.join(cls.LOG_DIR, log_file), 'a').close()
        
        # 清理上传目录
        cls._clean_directory(cls.UPLOAD_FOLDER)
        
        # 清理会话文件
        cls._clean_directory(cls.SESSION_FILE_DIR)
        
        # 删除旧的测试数据库
        try:
            if os.path.exists(cls.TEST_DB):
                os.remove(cls.TEST_DB)
            # 确保数据库目录可写
            db_dir = os.path.dirname(cls.TEST_DB)
            os.chmod(db_dir, 0o777)
        except OSError as e:
            app.logger.error(f'删除旧数据库失败: {str(e)}')
        
        # 初始化数据库
        from app.extensions import db
        from app.models import Role, User, Permission
        from sqlalchemy.exc import SQLAlchemyError
        
        with app.app_context():
            try:
                # 初始化数据库
                # 先清理现有的表
                db.session.remove()
                db.drop_all()
                db.session.commit()
                
                # 创建新表
                db.create_all()
                db.session.commit()
                
                # 确保数据库表已创建
                inspector = db.inspect(db.engine)
                tables = ['roles', 'users', 'user_roles', 'categories', 'tags', 'posts', 'post_tags', 'comments']
                existing_tables = inspector.get_table_names()
                
                # 检查缺失的表
                missing_tables = [t for t in tables if t not in existing_tables]
                if missing_tables:
                    app.logger.warning(f'发现缺失的表: {missing_tables}')
                    raise Exception(f'无法创建表: {missing_tables}')
                
                # 验证数据库连接
                with db.engine.connect() as conn:
                    conn.execute(db.text('SELECT 1'))
                    conn.commit()
                
                app.logger.info('数据库初始化成功')
                app.logger.info('所有必需的表已创建')
                db.session.commit()
                
                # 从 Permission 类导入权限定义
                from app.models import Permission
                
                # 初始化角色
                roles = [
                    {
                        'name': 'super_admin',
                        'description': '超级管理员',
                        'permissions': Permission.SUPER_ADMIN.value | Permission.ADMIN.value | Permission.MODERATE.value | 
                                      Permission.POST.value | Permission.COMMENT.value | Permission.VIEW.value,
                        'is_default': False
                    },
                    {
                        'name': 'admin',
                        'description': '管理员',
                        'permissions': Permission.ADMIN.value | Permission.MODERATE.value | Permission.POST.value | 
                                      Permission.COMMENT.value | Permission.VIEW.value,
                        'is_default': False
                    },
                    {
                        'name': 'editor',
                        'description': '编辑者',
                        'permissions': Permission.POST.value | Permission.COMMENT.value | Permission.VIEW.value,
                        'is_default': False
                    },
                    {
                        'name': 'user',
                        'description': '普通用户',
                        'permissions': Permission.COMMENT.value | Permission.VIEW.value,
                        'is_default': True
                    }
                ]
                
                # 初始化角色
                # 先清理现有角色
                Role.query.delete()
                db.session.commit()
                
                # 创建所有角色
                for role_data in roles:
                    try:
                        role = Role(
                            name=role_data['name'],
                            description=role_data['description'],
                            permissions=role_data['permissions'],
                            is_default=role_data['is_default']
                        )
                        db.session.add(role)
                        db.session.flush()  # 立即执行但不提交
                        app.logger.info(f'创建新角色: {role_data["name"]}, 权限: {role_data["permissions"]}')
                    except SQLAlchemyError as e:
                        db.session.rollback()
                        app.logger.error(f'角色 {role_data["name"]} 初始化失败: {str(e)}')
                        raise
                
                # 提交所有变更
                db.session.commit()
                
                # 验证角色初始化
                all_roles = Role.query.all()
                if len(all_roles) != len(roles):
                    raise Exception(f'角色数量不匹配: 期望 {len(roles)}, 实际 {len(all_roles)}')
                
                # 验证每个角色
                for role_data in roles:
                    role = Role.query.filter_by(name=role_data['name']).first()
                    if not role:
                        raise Exception(f'角色未创建: {role_data["name"]}')
                    if role.permissions != role_data['permissions']:
                        raise Exception(f'角色权限错误: {role_data["name"]}, 期望 {role_data["permissions"]}, 实际 {role.permissions}')
                    if role.is_default != role_data['is_default']:
                        raise Exception(f'角色默认状态错误: {role_data["name"]}, 期望 {role_data["is_default"]}, 实际 {role.is_default}')
                
                db.session.commit()
                app.logger.info('数据库初始化成功')
            except Exception as e:
                db.session.rollback()
                app.logger.error(f'数据库初始化失败: {str(e)}')
                raise
    
    @staticmethod
    def _clean_directory(directory):
        """清理目录及其子目录中的所有文件"""
        for root, dirs, files in os.walk(directory, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except OSError:
                    pass
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except OSError:
                    pass