"""
文件名：file.py
描述：文件处理工具
作者：denny
创建日期：2024-03-21
"""

import os
import secrets
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename
from PIL import Image

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_file(file):
    """保存文件
    
    Args:
        file: 要保存的文件对象
        
    Returns:
        str: 保存后的文件名
    """
    # 生成安全的文件名
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_hex = secrets.token_hex(8)
    _, ext = os.path.splitext(filename)
    new_filename = f"{timestamp}_{random_hex}{ext}"
    
    # 确保上传目录存在
    os.makedirs(current_app.config['IMAGE_UPLOAD_FOLDER'], exist_ok=True)
    
    # 保存文件
    filepath = os.path.join(current_app.config['IMAGE_UPLOAD_FOLDER'], new_filename)
    
    # 如果是图片，进行处理
    if ext.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
        image = Image.open(file)
        processed_image = process_image(image)
        processed_image.save(filepath, quality=85, optimize=True)
    else:
        file.save(filepath)
    
    return new_filename

def process_image(image, max_size=2048):
    """处理图片（调整大小、优化质量）
    
    Args:
        image: PIL Image对象
        max_size: 最大尺寸
        
    Returns:
        PIL Image: 处理后的图片
    """
    # 转换RGBA图片为RGB
    if image.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', image.size, 'white')
        background.paste(image, mask=image.split()[-1])
        image = background
    
    # 调整图片大小
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = tuple(int(dim * ratio) for dim in image.size)
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    return image 