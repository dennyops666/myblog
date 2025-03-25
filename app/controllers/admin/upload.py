"""
文件名：upload.py
描述：文件上传控制器
作者：denny
创建日期：2024-03-21
"""

import os
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from app.utils.file import allowed_file, save_file
from app.decorators import admin_required
from datetime import datetime, UTC

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/', methods=['GET', 'POST'])
@admin_required
def upload_file():
    """处理文件上传"""
    if request.method == 'GET':
        return jsonify({
            'success': True
        })

    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': '没有文件被上传'
        }), 400
        
    file = request.files['file']
    
    # 检查文件名
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

    # 检查文件大小
    file_content = file.read()
    file.seek(0)  # 重置文件指针
    if len(file_content) > current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024):
        return jsonify({
            'success': False,
            'message': '文件太大'
        }), 400

    # 保存文件
    try:
        filename = save_file(file)
        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'data': {
                'filename': filename,
                'url': f'/uploads/{filename}'
            }
        })
    except Exception as e:
        current_app.logger.error(f'文件上传失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': '文件上传失败'
        }), 500

@upload_bp.route('/delete/<filename>', methods=['POST'])
@admin_required
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
        else:
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
    except Exception as e:
        current_app.logger.error(f"删除文件失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '删除文件失败'
        }), 400

@upload_bp.route('/images', methods=['GET'])
@admin_required
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
            'files': files
        }), 200
    except Exception as e:
        current_app.logger.error(f"获取图片列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取图片列表失败'
        }), 400 