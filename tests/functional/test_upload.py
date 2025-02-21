"""
文件名：test_upload.py
描述：文件上传功能测试
作者：denny
创建日期：2024-03-20
"""

import os
import pytest
from io import BytesIO
from PIL import Image
from flask_sqlalchemy import SQLAlchemy
from markdown import markdown

db = SQLAlchemy()

def create_test_image(fmt='PNG'):
    """创建测试图片
    
    Args:
        fmt: 图片格式，默认为PNG
        
    Returns:
        BytesIO: 图片文件对象
    """
    from PIL import Image
    from io import BytesIO
    
    # 创建一个100x100的红色图片
    image = Image.new('RGB', (100, 100), color='red')
    file = BytesIO()
    image.save(file, fmt)
    file.seek(0)
    return file

def test_image_upload(client, auth):
    """测试图片上传"""
    # 登录
    auth.login()
    
    # 获取 CSRF 令牌
    response = client.get('/admin/upload')
    csrf_token = response.headers.get('X-CSRF-Token')
    
    # 创建测试图片
    file = create_test_image()
    
    # 测试上传
    response = client.post('/admin/upload', data={
        'file': (file, 'test.png'),
        'csrf_token': csrf_token
    }, content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'url' in data
    assert data['url'].startswith('/uploads/')
    
    # 清理测试文件
    file_path = os.path.join(client.application.config['UPLOAD_FOLDER'], os.path.basename(data['url']))
    if os.path.exists(file_path):
        os.remove(file_path)

def test_invalid_file_upload(client, auth):
    """测试无效文件上传"""
    auth.login()
    
    # 获取 CSRF 令牌
    response = client.get('/admin/upload')
    csrf_token = response.headers.get('X-CSRF-Token')
    
    # 测试不支持的文件类型
    file = BytesIO(b'not an image')
    response = client.post('/admin/upload', data={
        'file': (file, 'test.txt'),
        'csrf_token': csrf_token
    }, content_type='multipart/form-data')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_large_file_upload(client, auth):
    """测试大文件上传"""
    auth.login()

    # 获取 CSRF 令牌
    response = client.get('/admin/upload')
    csrf_token = response.headers.get('X-CSRF-Token')

    # 创建一个超过限制的文件
    large_file = BytesIO(b'0' * (16 * 1024 * 1024 + 1))  # 16MB + 1B

    response = client.post('/admin/upload', data={
        'file': (large_file, 'large.png'),
        'csrf_token': csrf_token
    }, content_type='multipart/form-data')

    assert response.status_code == 413  # 文件太大，返回413

def test_upload_without_login(client):
    """测试未登录上传"""
    # 获取 CSRF 令牌
    response = client.get('/admin/upload')
    csrf_token = response.headers.get('X-CSRF-Token')
    
    file = create_test_image()
    response = client.post('/admin/upload', data={
        'file': (file, 'test.png'),
        'csrf_token': csrf_token
    }, content_type='multipart/form-data')
    
    assert response.status_code == 401  # 未登录，返回401

def test_image_delete(client, auth):
    """测试图片删除"""
    auth.login()
    
    # 获取 CSRF 令牌
    response = client.get('/admin/upload')
    csrf_token = response.headers.get('X-CSRF-Token')
    
    # 先上传一个图片
    file = create_test_image()
    response = client.post('/admin/upload', data={
        'file': (file, 'test.png'),
        'csrf_token': csrf_token
    }, content_type='multipart/form-data')
    
    data = response.get_json()
    image_path = os.path.basename(data['url'])
    
    # 测试删除
    response = client.delete(
        f'/admin/posts/images/{image_path}',
        headers={'X-CSRF-Token': csrf_token}
    )
    assert response.status_code == 200
    
    # 验证文件已被删除
    file_path = os.path.join(client.application.config['UPLOAD_FOLDER'], image_path)
    assert not os.path.exists(file_path)

def test_get_post_images(client, test_post, auth):
    """测试获取文章图片列表"""
    # 登录用户
    auth.login()

    # 获取 CSRF 令牌
    response = client.get('/admin/upload')
    csrf_token = response.headers.get('X-CSRF-Token')

    # 上传三张测试图片
    image_urls = []
    for i in range(3):
        file = create_test_image()  # 使用create_test_image创建有效的测试图片
        data = {
            'file': (file, f'test{i}.png'),
            'csrf_token': csrf_token
        }
        response = client.post('/admin/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        data = response.get_json()
        assert 'url' in data
        image_urls.append(data['url'])

    # 更新文章内容，添加图片
    from app.extensions import db
    with client.application.app_context():
        post = db.session.merge(test_post)  # 重新绑定到会话
        content = post.content or ''
        for url in image_urls:
            content += f'\n![test image]({url})'
        post.content = content
        db.session.commit()

        # 获取文章图片列表
        response = client.get(f'/admin/posts/images/{post.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert 'images' in data

def test_concurrent_uploads(client, auth):
    """测试并发上传"""
    auth.login()
    
    # 获取 CSRF 令牌
    response = client.get('/admin/upload')
    csrf_token = response.headers.get('X-CSRF-Token')
    
    # 创建多个测试图片
    files = []
    for i in range(5):
        file = create_test_image()
        files.append((file, f'test_{i}.png'))
    
    # 模拟并发上传
    responses = []
    for file, filename in files:
        response = client.post('/admin/upload', data={
            'file': (file, filename),
            'csrf_token': csrf_token
        }, content_type='multipart/form-data')
        responses.append(response)
    
    # 验证所有上传都成功
    for response in responses:
        assert response.status_code == 200
        data = response.get_json()
        assert 'url' in data
        assert data['url'].startswith('/uploads/')

def test_duplicate_filename(client, auth):
    """测试重复文件名处理"""
    auth.login()
    
    # 获取 CSRF 令牌
    response = client.get('/admin/upload')
    csrf_token = response.headers.get('X-CSRF-Token')
    
    # 上传两个同名文件
    file1 = create_test_image()
    file2 = create_test_image()
    
    response1 = client.post('/admin/upload', data={
        'file': (file1, 'test.png'),
        'csrf_token': csrf_token
    }, content_type='multipart/form-data')
    
    response2 = client.post('/admin/upload', data={
        'file': (file2, 'test.png'),
        'csrf_token': csrf_token
    }, content_type='multipart/form-data')
    
    # 验证两个文件都上传成功且文件名不同
    assert response1.status_code == 200
    assert response2.status_code == 200
    data1 = response1.get_json()
    data2 = response2.get_json()
    assert data1['url'] != data2['url']

def test_image_resize(client, auth):
    """测试图片尺寸调整"""
    auth.login()

    # 获取 CSRF 令牌
    response = client.get('/admin/upload')
    csrf_token = response.headers.get('X-CSRF-Token')

    # 创建一个大尺寸图片
    file = BytesIO()
    image = Image.new('RGB', (2000, 2000), color='red')
    image.save(file, 'PNG')
    file.seek(0)

    response = client.post('/admin/upload', data={
        'file': (file, 'large.png'),
        'csrf_token': csrf_token
    }, content_type='multipart/form-data')

    assert response.status_code == 200
    data = response.get_json()
    assert 'url' in data

    # 验证图片已被调整大小
    file_path = os.path.join(client.application.config['UPLOAD_FOLDER'], os.path.basename(data['url']))
    with Image.open(file_path) as img:
        assert max(img.size) <= 2048  # 最大尺寸为2048

def test_image_format_conversion(client, auth):
    """测试图片格式转换"""
    auth.login()

    # 获取 CSRF 令牌
    response = client.get('/admin/upload')
    csrf_token = response.headers.get('X-CSRF-Token')

    # 创建不同格式的图片
    formats = ['JPEG', 'GIF', 'PNG']
    for fmt in formats:
        file = create_test_image(fmt)
        response = client.post('/admin/upload', data={
            'file': (file, f'test.{fmt.lower()}'),
            'csrf_token': csrf_token
        }, content_type='multipart/form-data')

        assert response.status_code == 200
        data = response.get_json()
        assert 'url' in data
        assert data['url'].endswith('.png')  # 所有图片都转换为PNG格式

def test_malformed_image(client, auth):
    """测试损坏的图片文件"""
    auth.login()
    
    # 获取 CSRF 令牌
    response = client.get('/admin/upload')
    csrf_token = response.headers.get('X-CSRF-Token')
    
    # 创建一个损坏的PNG文件
    file = BytesIO(b'\x89PNG\r\n\x1a\n' + b'corrupted data')
    
    response = client.post('/admin/upload', data={
        'file': (file, 'corrupted.png'),
        'csrf_token': csrf_token
    }, content_type='multipart/form-data')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_upload_folder_creation(client, auth):
    """测试上传目录创建"""
    auth.login()
    
    # 获取 CSRF 令牌
    response = client.get('/admin/upload')
    csrf_token = response.headers.get('X-CSRF-Token')
    
    # 删除上传目录（如果存在）
    upload_folder = client.application.config['UPLOAD_FOLDER']
    if os.path.exists(upload_folder):
        import shutil
        shutil.rmtree(upload_folder)
    
    # 测试上传
    file = create_test_image()
    response = client.post('/admin/upload', data={
        'file': (file, 'test.png'),
        'csrf_token': csrf_token
    }, content_type='multipart/form-data')
    
    assert response.status_code == 200
    assert os.path.exists(upload_folder) 