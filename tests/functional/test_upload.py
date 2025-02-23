"""
文件名：test_upload.py
描述：文件上传功能测试
作者：denny
创建日期：2024-03-21
"""

import os
import io
import shutil
import pytest
from io import BytesIO
from PIL import Image
from flask_sqlalchemy import SQLAlchemy
from markdown import markdown
from flask_wtf.csrf import generate_csrf
from flask import current_app
from datetime import datetime, UTC
from flask import url_for

db = SQLAlchemy()

def create_test_image(fmt='PNG', size=None, mode=None):
    """创建测试图片
    
    Args:
        fmt: 图片格式，默认为PNG
        size: 图片大小，默认为None
        mode: 图片模式，默认为None
        
    Returns:
        BytesIO: 图片文件对象
    """
    from PIL import Image
    from io import BytesIO
    
    # 创建一个100x100的红色图片
    image = Image.new('RGB', size or (100, 100), color='red')
    file = BytesIO()
    image.save(file, fmt)
    file.seek(0)
    return file

@pytest.fixture(autouse=True)
def setup_session(client, test_user):
    """设置会话变量"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
        sess['_permanent'] = True
        sess['user_agent'] = 'test'
        sess['last_active'] = datetime.now(UTC).isoformat()
        sess['is_authenticated'] = True
        sess['csrf_token'] = generate_csrf()
        sess['user'] = {
            'id': test_user.id,
            'username': test_user.username,
            'email': test_user.email
        }

def test_image_upload(authenticated_client, auth):
    """测试图片上传"""
    # 创建测试图片
    img = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    # 上传图片
    response = authenticated_client.post('/admin/upload/upload/', data={
        'file': (img_io, 'test.png'),
        'csrf_token': generate_csrf()
    }, content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'url' in data

def test_invalid_file_upload(authenticated_client, auth):
    """测试无效文件上传"""
    # 创建无效文件
    invalid_file = io.BytesIO(b'invalid file content')
    
    # 上传无效文件
    response = authenticated_client.post('/admin/upload/upload/', data={
        'file': (invalid_file, 'test.txt'),
        'csrf_token': generate_csrf()
    }, content_type='multipart/form-data')
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False

def test_large_file_upload(authenticated_client, auth):
    """测试大文件上传"""
    # 创建大图片
    img = Image.new('RGB', (3000, 3000), color='red')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    # 上传大图片
    response = authenticated_client.post('/admin/upload/upload/', data={
        'file': (img_io, 'large.png'),
        'csrf_token': generate_csrf()
    }, content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'url' in data

def test_image_delete(authenticated_client, auth):
    """测试图片删除"""
    # 先上传一个图片
    img = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    response = authenticated_client.post('/admin/upload/upload/', data={
        'file': (img_io, 'test.png'),
        'csrf_token': generate_csrf()
    }, content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = response.get_json()
    filename = data['url'].split('/')[-1]
    
    # 删除图片
    response = authenticated_client.delete(f'/admin/upload/delete/{filename}', headers={
        'X-CSRFToken': generate_csrf()
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

def test_get_post_images(authenticated_client, auth, test_post):
    """测试获取文章图片"""
    # 添加一些图片到文章内容中
    test_post.content = """# Test Post
    
![Image 1](/uploads/test1.png)
![Image 2](/uploads/test2.png)
"""
    db.session.commit()
    
    # 获取文章图片
    response = authenticated_client.get(f'/admin/upload/post/{test_post.id}/images')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'images' in data
    assert len(data['images']) == 2
    
    # 验证返回的图片URL
    images = data['images']
    assert any(img['url'] == '/uploads/test1.png' for img in images)
    assert any(img['url'] == '/uploads/test2.png' for img in images)

def test_concurrent_uploads(authenticated_client, auth):
    """测试并发上传"""
    # 创建多个图片并同时上传
    responses = []
    for i in range(3):
        img = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        response = authenticated_client.post('/admin/upload/upload/', data={
            'file': (img_io, f'test{i}.png'),
            'csrf_token': generate_csrf()
        }, content_type='multipart/form-data')
        responses.append(response)
    
    # 验证所有上传都成功
    for response in responses:
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'url' in data

def test_duplicate_filename(authenticated_client, auth):
    """测试重复文件名上传"""
    # 上传两个同名文件
    img1 = Image.new('RGB', (100, 100), color='red')
    img_io1 = io.BytesIO()
    img1.save(img_io1, 'PNG')
    img_io1.seek(0)

    response1 = authenticated_client.post('/admin/upload/upload/', data={
        'file': (img_io1, 'duplicate.png'),
        'csrf_token': generate_csrf()
    }, content_type='multipart/form-data')

    # 创建新的图片和IO对象
    img2 = Image.new('RGB', (100, 100), color='blue')
    img_io2 = io.BytesIO()
    img2.save(img_io2, 'PNG')
    img_io2.seek(0)

    response2 = authenticated_client.post('/admin/upload/upload/', data={
        'file': (img_io2, 'duplicate.png'),
        'csrf_token': generate_csrf()
    }, content_type='multipart/form-data')

    assert response1.status_code == 200
    assert response2.status_code == 200

def test_image_resize(authenticated_client, auth):
    """测试图片缩放"""
    # 创建大图片
    img = Image.new('RGB', (3000, 3000), color='red')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    # 上传图片
    response = authenticated_client.post('/admin/upload/upload/', data={
        'file': (img_io, 'large.png'),
        'csrf_token': generate_csrf()
    }, content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    
    # 验证图片已被缩放
    filename = data['url'].split('/')[-1]
    img_path = os.path.join(authenticated_client.application.config['IMAGE_UPLOAD_FOLDER'], filename)
    with Image.open(img_path) as img:
        assert max(img.size) <= 2048

def test_image_format_conversion(authenticated_client, auth):
    """测试图片格式转换"""
    # 创建JPEG图片
    img = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG')
    img_io.seek(0)
    
    # 上传为PNG
    response = authenticated_client.post('/admin/upload/upload/', data={
        'file': (img_io, 'test.png'),
        'csrf_token': generate_csrf()
    }, content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'url' in data

def test_malformed_image(authenticated_client, auth):
    """测试损坏的图片文件"""
    # 创建损坏的图片数据
    invalid_image = io.BytesIO(b'invalid image data')
    
    # 上传损坏的图片
    response = authenticated_client.post('/admin/upload/upload/', data={
        'file': (invalid_image, 'corrupt.png'),
        'csrf_token': generate_csrf()
    }, content_type='multipart/form-data')
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False

def test_upload_folder_creation(authenticated_client, auth):
    """测试上传文件夹创建"""
    # 确保上传文件夹不存在
    upload_folder = authenticated_client.application.config['IMAGE_UPLOAD_FOLDER']
    if os.path.exists(upload_folder):
        os.rmdir(upload_folder)
    
    # 上传图片
    img = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    response = authenticated_client.post('/admin/upload/upload/', data={
        'file': (img_io, 'test.png'),
        'csrf_token': generate_csrf()
    }, content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert os.path.exists(upload_folder) 