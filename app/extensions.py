"""
文件名：extensions.py
描述：Flask扩展实例
作者：denny
创建日期：2025-02-16
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect

# 数据库
db = SQLAlchemy()

# 数据库迁移
migrate = Migrate()

# 登录管理
login_manager = LoginManager()
login_manager.login_view = 'admin.login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'warning'

# 密码加密
bcrypt = Bcrypt()

# 缓存
cache = Cache()

# CSRF保护
csrf = CSRFProtect() 