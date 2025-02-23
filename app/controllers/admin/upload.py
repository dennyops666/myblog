"""
文件名：upload.py
描述：文件上传控制器
作者：denny
创建日期：2024-03-21
"""

import os
import re
from flask import request, jsonify, current_app, Blueprint, url_for, render_template, send_from_directory, flash, redirect
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image
import uuid
from app.services.post import PostService
from datetime import datetime, UTC
from flask_wtf.csrf import generate_csrf

# 创建蓝图，设置url_prefix
upload_bp = Blueprint('upload', __name__, url_prefix='/upload')
post_service = PostService()

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def process_image(image, max_size=2048):
    """处理图片大小和格式"""
    if image.size[0] > max_size or image.size[1] > max_size:
        image.thumbnail((max_size, max_size))
    return image

@upload_bp.route('/', methods=['GET', 'POST'])
@login_required
def upload_file():
    """处理文件上传"""
    if request.method == 'GET':
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': True,
                'message': '准备上传',
                'csrf_token': generate_csrf()
            }), 200
        return render_template('admin/upload.html')

    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': '没有文件被上传'
        }), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': '没有选择文件'
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'message': '不支持的文件类型'
        }), 400

    try:
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        # 添加UUID前缀避免文件名冲突
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # 确保上传目录存在
        os.makedirs(current_app.config['IMAGE_UPLOAD_FOLDER'], exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(current_app.config['IMAGE_UPLOAD_FOLDER'], unique_filename)
        
        # 如果是图片，进行处理
        if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            image = Image.open(file)
            image = process_image(image)
            image.save(file_path, quality=85, optimize=True)
        else:
            file.save(file_path)

        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'url': url_for('uploaded_file', filename=unique_filename, _external=True)
        }), 200

    except Exception as e:
        current_app.logger.error(f"文件上传失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '文件上传失败'
        }), 500

@upload_bp.route('/<filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
    """删除文件"""
    try:
        file_path = os.path.join(current_app.config['IMAGE_UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({
                'success': True,
                'message': '文件删除成功'
            }), 200
        return jsonify({
            'success': False,
            'message': '文件不存在'
        }), 404
    except Exception as e:
        current_app.logger.error(f"文件删除失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '文件删除失败'
        }), 500

@upload_bp.route('/post/<int:post_id>/images', methods=['GET'])
@login_required
def get_post_images(post_id):
    """获取文章的图片列表"""
    try:
        images = post_service.get_post_images(post_id)
        return jsonify({
            'success': True,
            'images': images
        }), 200
    except Exception as e:
        current_app.logger.error(f"获取文章图片失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取文章图片失败'
        }), 500

@upload_bp.route('/list', methods=['GET'])
@login_required
def list_files():
    """列出上传的文件"""
    try:
        files = []
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        for filename in os.listdir(upload_folder):
            if allowed_file(filename):
                filepath = os.path.join(upload_folder, filename)
                files.append({
                    'name': filename,
                    'url': url_for('uploaded_file', filename=filename, _external=True),
                    'size': os.path.getsize(filepath),
                    'modified': os.path.getmtime(filepath)
                })
        return jsonify({
            'files': files,
            'csrf_token': generate_csrf()
        }), 200
    except Exception as e:
        current_app.logger.error(f"获取文件列表失败: {str(e)}")
        return jsonify({
            'error': str(e),
            'csrf_token': generate_csrf()
        }), 500 