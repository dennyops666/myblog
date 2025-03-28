"""
文件名：file.py
描述：文件处理工具函数
作者：denny
"""

import os
import datetime
import random
import string
from werkzeug.utils import secure_filename
from flask import current_app

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """检查文件扩展名是否在允许列表中"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    """保存上传的文件并返回保存后的文件名"""
    # 确保文件名安全
    filename = secure_filename(file.filename)
    
    # 创建带时间戳的唯一文件名
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    random_string = ''.join(random.choices(string.hexdigits, k=16))
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    new_filename = f"{timestamp}_{random_string}.{ext}"
    
    # 确保目标目录存在
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'images')
    os.makedirs(upload_dir, exist_ok=True)
    
    # 设置文件路径并保存
    file_path = os.path.join(upload_dir, new_filename)
    
    # 记录保存路径
    current_app.logger.info(f"保存文件到: {file_path}")
    
    # 保存文件
    file.save(file_path)
    
    # 设置文件权限
    try:
        os.chmod(file_path, 0o666)  # rw-rw-rw-
    except Exception as e:
        current_app.logger.warning(f"无法设置文件权限: {str(e)}")
    
    return new_filename 