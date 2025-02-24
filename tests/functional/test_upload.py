"""
文件名：test_upload.py
描述：上传功能测试
作者：denny
创建日期：2024-03-21
"""

import pytest
from io import BytesIO
from PIL import Image
import threading
import os
from datetime import datetime, UTC
import time
from app.utils.database import session_scope

def create_test_image(width=100, height=100, color='red'):
    """创建测试图片"""
    image = Image.new('RGB', (width, height), color=color)
    image_io = BytesIO()
    image.save(image_io, 'JPEG')
    image_io.seek(0)
    return image_io

def test_image_upload(authenticated_client):
    """测试图片上传"""
    data = {
        'file': (create_test_image(), 'test.jpg')
    }
    response = authenticated_client.post_with_token('/admin/upload/', data=data)
    assert response.status_code == 200

def test_invalid_file_upload(authenticated_client):
    """测试无效文件上传"""
    data = {}  # 没有文件
    response = authenticated_client.post_with_token('/admin/upload/', data=data)
    assert response.status_code == 400

def test_large_file_upload(authenticated_client):
    """测试大文件上传"""
    # 创建一个超过1MB的图片
    large_image = create_test_image(width=10000, height=10000)
    data = {
        'file': (large_image, 'large.jpg')
    }
    response = authenticated_client.post_with_token('/admin/upload/', data=data)
    assert response.status_code == 413

def test_image_delete(authenticated_client):
    """测试图片删除"""
    # 先上传一个图片
    data = {
        'file': (create_test_image(), 'test.jpg')
    }
    upload_response = authenticated_client.post_with_token('/admin/upload/', data=data)
    assert upload_response.status_code == 200
    
    # 从响应中获取上传的文件名
    filename = upload_response.json['url'].split('/')[-1]
    
    # 删除图片
    response = authenticated_client.post_with_token(f'/admin/upload/delete/{filename}')
    assert response.status_code == 200

def test_get_post_images(authenticated_client):
    """测试获取已上传的图片列表"""
    # 先上传一些图片
    for i in range(3):
        data = {
            'file': (create_test_image(color=f'rgb({i*50}, {i*50}, {i*50})'), f'test{i}.jpg')
        }
        response = authenticated_client.post_with_token('/admin/upload/', data=data)
        assert response.status_code == 200
    
    # 获取图片列表
    response = authenticated_client.get('/admin/upload/images')
    assert response.status_code == 200
    assert len(response.json['files']) >= 3

def test_concurrent_uploads(authenticated_client):
    """测试并发上传"""
    def upload_file():
        # 创建测试图片
        image = create_test_image()
        filename = f'test_{threading.get_ident()}.jpg'
        
        data = {
            'file': (image, filename)
        }
        
        # 使用 post_with_token 方法，它会自动处理 CSRF token 和会话
        response = authenticated_client.post_with_token('/admin/upload/', data=data)
        assert response.status_code == 200

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

def test_duplicate_filename(authenticated_client):
    """测试重复文件名上传"""
    data = {
        'file': (create_test_image(), 'test.jpg')
    }
    response1 = authenticated_client.post_with_token('/admin/upload/', data=data)
    assert response1.status_code == 200
    
    data = {
        'file': (create_test_image(), 'test.jpg')
    }
    response2 = authenticated_client.post_with_token('/admin/upload/', data=data)
    assert response2.status_code == 200
    assert response1.json['url'] != response2.json['url']

def test_image_resize(authenticated_client):
    """测试图片调整大小"""
    img_io = create_test_image(width=1200, height=1200)
    
    data = {
        'file': (img_io, 'large.jpg')
    }
    response = authenticated_client.post_with_token('/admin/upload/', data=data)
    assert response.status_code == 200

def test_image_format_conversion(authenticated_client):
    """测试图片格式转换"""
    # 创建PNG图片
    image = Image.new('RGB', (100, 100), color='blue')
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)

    data = {
        'file': (img_io, 'test.png')
    }
    response = authenticated_client.post_with_token('/admin/upload/', data=data)
    assert response.status_code == 200

def test_malformed_image(authenticated_client):
    """测试损坏的图片文件"""
    data = {
        'file': (BytesIO(b'malformed image content'), 'bad.jpg')
    }
    response = authenticated_client.post_with_token('/admin/upload/', data=data)
    assert response.status_code == 400

def test_upload_folder_creation(authenticated_client, app):
    """测试上传目录创建"""
    import shutil
    # 删除上传目录
    shutil.rmtree(app.config['UPLOAD_FOLDER'])
    
    data = {
        'file': (create_test_image(), 'test.jpg')
    }
    response = authenticated_client.post_with_token('/admin/upload/', data=data)
    assert response.status_code == 200
    assert os.path.exists(app.config['UPLOAD_FOLDER'])