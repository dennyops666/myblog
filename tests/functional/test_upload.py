"""
文件名：test_upload.py
描述：文件上传功能测试
作者：denny
创建日期：2024-03-21
"""

import os
import pytest
from io import BytesIO
from PIL import Image
import threading
import time
from flask import current_app

def create_test_image(width=100, height=100, color='rgb(255,0,0)'):
    """创建测试图片"""
    image = Image.new('RGB', (width, height), color=color)
    img_io = BytesIO()
    image.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return img_io

def test_image_upload(authenticated_client, app):
    """测试图片上传"""
    with app.app_context():
        data = {
            'file': (create_test_image(), 'test.jpg')
        }
        response = authenticated_client.post_with_token('/admin/upload/', data=data)
        assert response.status_code == 200
        assert response.json['success'] is True
        assert 'filename' in response.json
        assert 'url' in response.json
        assert os.path.exists(os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], response.json['filename']))

def test_invalid_file_upload(authenticated_client, app):
    """测试无效文件上传"""
    with app.app_context():
        data = {}  # 没有文件
        response = authenticated_client.post_with_token('/admin/upload/', data=data)
        assert response.status_code == 400
        assert response.json['success'] is False
        assert response.json['message'] == '没有文件被上传'

def test_large_file_upload(authenticated_client, app):
    """测试大文件上传"""
    with app.app_context():
        # 创建一个超过限制的图片
        large_image = create_test_image(width=10000, height=10000)
        data = {
            'file': (large_image, 'large.jpg')
        }
        response = authenticated_client.post_with_token('/admin/upload/', data=data)
        assert response.status_code in [400, 413]  # 接受 400 或 413
        assert not response.json.get('success', False)

def test_image_delete(authenticated_client, app):
    """测试图片删除"""
    with app.app_context():
        # 先上传一个图片
        data = {
            'file': (create_test_image(), 'test.jpg')
        }
        upload_response = authenticated_client.post_with_token('/admin/upload/', data=data)
        assert upload_response.status_code == 200
        filename = upload_response.json['filename']

        # 删除图片
        response = authenticated_client.post_with_token(f'/admin/upload/delete/{filename}', data={})
        assert response.status_code == 200
        assert response.json['success'] is True
        assert not os.path.exists(os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], filename))

def test_get_post_images(authenticated_client, app):
    """测试获取已上传的图片列表"""
    with app.app_context():
        # 先上传一些图片
        filenames = []
        for i in range(3):
            data = {
                'file': (create_test_image(color=f'rgb({i*50}, {i*50}, {i*50})'), f'test{i}.jpg')
            }
            response = authenticated_client.post_with_token('/admin/upload/', data=data)
            assert response.status_code == 200
            filenames.append(response.json['filename'])

        # 获取图片列表
        response = authenticated_client.get('/admin/upload/images')
        assert response.status_code == 200
        assert response.json['success'] is True
        assert len(response.json['files']) >= 3
        for file_info in response.json['files']:
            assert 'name' in file_info
            assert 'url' in file_info
            assert 'size' in file_info
            assert 'modified' in file_info

def test_concurrent_uploads(authenticated_client, app):
    """测试并发上传"""
    with app.app_context():
        def upload_file():
            # 创建测试图片
            image = create_test_image()
            filename = f'test_{threading.get_ident()}.jpg'

            data = {
                'file': (image, filename)
            }

            # 使用 post_with_token 方法，它会自动处理 CSRF token 和会话
            with app.app_context():
                response = authenticated_client.post_with_token('/admin/upload/', data=data)
                assert response.status_code == 200
                assert response.json['success'] is True
                assert 'filename' in response.json
                assert 'url' in response.json

        threads = []
        for _ in range(3):
            t = threading.Thread(target=upload_file)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 等待一小段时间确保所有文件都已处理完成
        time.sleep(1)

        # 验证上传结果
        response = authenticated_client.get('/admin/upload/images')
        assert response.status_code == 200
        assert len(response.json['files']) >= 3

def test_duplicate_filename(authenticated_client, app):
    """测试重复文件名上传"""
    with app.app_context():
        data = {
            'file': (create_test_image(), 'test.jpg')
        }
        response1 = authenticated_client.post_with_token('/admin/upload/', data=data)
        assert response1.status_code == 200
        filename1 = response1.json['filename']

        # 上传同名文件
        data = {
            'file': (create_test_image(), 'test.jpg')
        }
        response2 = authenticated_client.post_with_token('/admin/upload/', data=data)
        assert response2.status_code == 200
        filename2 = response2.json['filename']

        # 确保生成了不同的文件名
        assert filename1 != filename2
        assert 'url' in response1.json
        assert 'url' in response2.json

def test_image_resize(authenticated_client, app):
    """测试图片调整大小"""
    with app.app_context():
        img_io = create_test_image(width=3000, height=3000)

        data = {
            'file': (img_io, 'large.jpg')
        }
        response = authenticated_client.post_with_token('/admin/upload/', data=data)
        assert response.status_code == 200
        filename = response.json['filename']

        # 验证图片已被调整大小
        img_path = os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], filename)
        with Image.open(img_path) as img:
            width, height = img.size
            assert max(width, height) <= 2048  # 最大尺寸为2048

def test_image_format_conversion(authenticated_client, app):
    """测试图片格式转换"""
    with app.app_context():
        # 创建PNG图片
        image = Image.new('RGBA', (100, 100), color=(0, 0, 255, 128))
        img_io = BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)

        data = {
            'file': (img_io, 'test.png')
        }
        response = authenticated_client.post_with_token('/admin/upload/', data=data)
        assert response.status_code == 200
        filename = response.json['filename']

        # 验证图片已被转换为JPEG
        img_path = os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], filename)
        with Image.open(img_path) as img:
            assert img.mode == 'RGB'  # 确保已转换为RGB模式

def test_malformed_image(authenticated_client, app):
    """测试损坏的图片文件"""
    with app.app_context():
        data = {
            'file': (BytesIO(b'malformed image content'), 'bad.jpg')
        }
        response = authenticated_client.post_with_token('/admin/upload/', data=data)
        assert response.status_code == 400
        assert response.json['success'] is False
        assert '图片处理失败' in response.json['message']

def test_upload_folder_creation(authenticated_client, app):
    """测试上传目录创建"""
    with app.app_context():
        import shutil
        # 删除上传目录
        shutil.rmtree(app.config['IMAGE_UPLOAD_FOLDER'], ignore_errors=True)

        data = {
            'file': (create_test_image(), 'test.jpg')
        }
        response = authenticated_client.post_with_token('/admin/upload/', data=data)
        assert response.status_code == 200
        assert os.path.exists(app.config['IMAGE_UPLOAD_FOLDER'])
        assert 'filename' in response.json
        assert 'url' in response.json