"""
文件名：upload.py
描述：文件上传控制器
作者：denny
创建日期：2024-03-21
"""

import os
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image
import secrets
from datetime import datetime
from flask_wtf.csrf import generate_csrf

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def process_image(image, max_size=2048):
    """处理图片（调整大小、优化质量）"""
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

@upload_bp.route('/', methods=['GET', 'POST'])
@login_required
def upload_file():
    """处理文件上传"""
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'csrf_token': generate_csrf()
        })

    if not request.form.get('csrf_token'):
        return jsonify({
            'success': False,
            'message': 'CSRF token 缺失',
            'csrf_token': generate_csrf()
        }), 400

    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': '没有文件被上传',
            'csrf_token': generate_csrf()
        }), 400
        
    file = request.files['file']
    
    # 检查文件名
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': '没有选择文件',
            'csrf_token': generate_csrf()
        }), 400
        
    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'message': '不支持的文件类型',
            'csrf_token': generate_csrf()
        }), 400

    # 检查文件大小
    file_content = file.read()
    file.seek(0)  # 重置文件指针
    if len(file_content) > current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024):
        return jsonify({
            'success': False,
            'message': '文件太大',
            'csrf_token': generate_csrf()
        }), 400
        
    try:
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_hex = secrets.token_hex(8)
        _, ext = os.path.splitext(filename)
        new_filename = f"{timestamp}_{random_hex}{ext}"
        
        # 确保上传目录存在
        os.makedirs(current_app.config['IMAGE_UPLOAD_FOLDER'], exist_ok=True)
        
        # 保存并处理图片
        filepath = os.path.join(current_app.config['IMAGE_UPLOAD_FOLDER'], new_filename)
        
        try:
            # 处理图片
            image = Image.open(file)
            processed_image = process_image(image)
            processed_image.save(filepath, quality=85, optimize=True)
        except Exception as e:
            current_app.logger.error(f"处理图片失败: {str(e)}")
            return jsonify({
                'success': False,
                'message': '图片处理失败',
                'error': str(e),
                'csrf_token': generate_csrf()
            }), 400
        
        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'url': f"/uploads/{new_filename}",
            'filename': new_filename,
            'csrf_token': generate_csrf()
        }), 200
            
    except Exception as e:
        current_app.logger.error(f"文件上传失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '文件上传失败',
            'error': str(e),
            'csrf_token': generate_csrf()
        }), 400

@upload_bp.route('/delete/<filename>', methods=['POST'])
@login_required
def delete_file(filename):
    """删除文件"""
    if not request.form.get('csrf_token'):
        return jsonify({
            'success': False,
            'message': 'CSRF token 缺失',
            'csrf_token': generate_csrf()
        }), 400

    try:
        file_path = os.path.join(current_app.config['IMAGE_UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({
                'success': True,
                'message': '文件删除成功',
                'csrf_token': generate_csrf()
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '文件不存在',
                'csrf_token': generate_csrf()
            }), 404
    except Exception as e:
        current_app.logger.error(f"删除文件失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '删除文件失败',
            'error': str(e),
            'csrf_token': generate_csrf()
        }), 400

@upload_bp.route('/images', methods=['GET'])
@login_required
def list_images():
    """获取图片列表"""
    try:
        files = []
        for filename in os.listdir(current_app.config['IMAGE_UPLOAD_FOLDER']):
            if allowed_file(filename):
                file_path = os.path.join(current_app.config['IMAGE_UPLOAD_FOLDER'], filename)
                files.append({
                    'name': filename,
                    'url': f"/uploads/{filename}",
                    'size': os.path.getsize(file_path),
                    'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                })
        return jsonify({
            'success': True,
            'files': files,
            'csrf_token': generate_csrf()
        }), 200
    except Exception as e:
        current_app.logger.error(f"获取图片列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取图片列表失败',
            'error': str(e),
            'csrf_token': generate_csrf()
        }), 400 