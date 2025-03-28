"""
文件名：logger.py
描述：日志工具模块
作者：denny
"""

import logging
from logging.handlers import RotatingFileHandler
import os

# 创建日志目录
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 创建日志记录器
logger = logging.getLogger('app')
logger.setLevel(logging.INFO)

# 创建日志格式化器
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(module)s:%(lineno)d - %(message)s'
)

# 创建文件处理器
file_handler = RotatingFileHandler(
    os.path.join(log_dir, 'app.log'),
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=10
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler) 