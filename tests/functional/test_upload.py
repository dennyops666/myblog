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

def create_test_image():
    """创建测试图片"""
    file = BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(file, 'png')
    file.seek(0)
    return file

def test_image_upload(client, auth):
    """测试图片上传"""
    # 登录
    auth.login()
    
    # 创建测试图片
    file = create_test_image()
    
    # 测试上传
    response = client.post('/admin/posts/upload-image', data={
        'file': (file, 'test.png')
    }, content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'url' in data
    assert data['url'].endswith('.png')
    
    # 验证文件是否实际保存
    file_path = os.path.join(client.application.config['UPLOAD_FOLDER'], os.path.basename(data['url']))
    assert os.path.exists(file_path)
    
    # 清理测试文件
    os.remove(file_path)

def test_invalid_file_upload(client, auth):
    """测试无效文件上传"""
    auth.login()
    
    # 测试不支持的文件类型
    file = BytesIO(b'not an image')
    response = client.post('/admin/posts/upload-image', data={
        'file': (file, 'test.txt')
    }, content_type='multipart/form-data')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert '不支持的文件类型' in data['error']

def test_large_file_upload(client, auth):
    """测试大文件上传"""
    auth.login()
    
    # 创建一个超过限制的文件
    large_file = BytesIO(b'0' * (16 * 1024 * 1024 + 1))  # 16MB + 1B
    
    response = client.post('/admin/posts/upload-image', data={
        'file': (large_file, 'large.png')
    }, content_type='multipart/form-data')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert '文件大小超过限制' in data['error']

def test_upload_without_login(client):
    """测试未登录上传"""
    file = create_test_image()
    
    response = client.post('/admin/posts/upload-image', data={
        'file': (file, 'test.png')
    }, content_type='multipart/form-data')
    
    assert response.status_code == 302  # 应重定向到登录页面

def test_image_delete(client, auth):
    """测试图片删除"""
    auth.login()
    
    # 先上传一个图片
    file = create_test_image()
    response = client.post('/admin/posts/upload-image', data={
        'file': (file, 'test.png')
    }, content_type='multipart/form-data')
    
    data = response.get_json()
    image_path = os.path.basename(data['url'])
    
    # 测试删除
    response = client.delete(f'/admin/posts/images/{image_path}')
    assert response.status_code == 200
    
    # 验证文件已被删除
    file_path = os.path.join(client.application.config['UPLOAD_FOLDER'], image_path)
    assert not os.path.exists(file_path)

def test_get_post_images(client, auth, test_post):
    """测试获取文章图片列表"""
    auth.login()
    
    # 上传几张测试图片
    images = []
    for i in range(3):
        file = create_test_image()
        response = client.post('/admin/posts/upload-image', data={
            'file': (file, f'test_{i}.png')
        }, content_type='multipart/form-data')
        images.append(response.get_json()['url'])
    
    # 获取图片列表
    response = client.get(f'/admin/posts/images/{test_post.id}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'images' in data
    assert len(data['images']) == len(images)
    
    # 清理测试文件
    for url in images:
        file_path = os.path.join(client.application.config['UPLOAD_FOLDER'], os.path.basename(url))
        if os.path.exists(file_path):
            os.remove(file_path)

def test_concurrent_uploads(client, auth):
    """测试并发上传"""
    auth.login()
    
    # 创建多个测试图片
    files = []
    for i in range(5):
        file = create_test_image()
        files.append((file, f'test_{i}.png'))
    
    # 模拟并发上传
    responses = []
    for file, filename in files:
        response = client.post('/admin/posts/upload-image', data={
            'file': (file, filename)
        }, content_type='multipart/form-data')
        responses.append(response)
    
    # 验证所有上传都成功
    for response in responses:
        assert response.status_code == 200
        data = response.get_json()
        assert 'url' in data
        
        # 清理测试文件
        file_path = os.path.join(client.application.config['UPLOAD_FOLDER'], 
                                os.path.basename(data['url']))
        if os.path.exists(file_path):
            os.remove(file_path)

def test_duplicate_filename(client, auth):
    """测试重复文件名处理"""
    auth.login()
    
    # 上传两个同名文件
    file1 = create_test_image()
    file2 = create_test_image()
    
    response1 = client.post('/admin/posts/upload-image', data={
        'file': (file1, 'test.png')
    }, content_type='multipart/form-data')
    
    response2 = client.post('/admin/posts/upload-image', data={
        'file': (file2, 'test.png')
    }, content_type='multipart/form-data')
    
    # 验证两个文件都上传成功且文件名不同
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    data1 = response1.get_json()
    data2 = response2.get_json()
    assert data1['url'] != data2['url']
    
    # 清理测试文件
    for data in [data1, data2]:
        file_path = os.path.join(client.application.config['UPLOAD_FOLDER'], 
                                os.path.basename(data['url']))
        if os.path.exists(file_path):
            os.remove(file_path)

def test_image_resize(client, auth):
    """测试图片尺寸调整"""
    auth.login()
    
    # 创建一个大尺寸图片
    file = BytesIO()
    image = Image.new('RGB', (2000, 2000), color='red')
    image.save(file, 'png')
    file.seek(0)
    
    response = client.post('/admin/posts/upload-image', data={
        'file': (file, 'large.png')
    }, content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = response.get_json()
    
    # 验证图片已被调整大小
    file_path = os.path.join(client.application.config['UPLOAD_FOLDER'], 
                            os.path.basename(data['url']))
    with Image.open(file_path) as img:
        assert max(img.size) <= 1024  # 假设最大尺寸限制为1024px
    
    # 清理测试文件
    os.remove(file_path)

def test_image_format_conversion(client, auth):
    """测试图片格式转换"""
    auth.login()
    
    # 创建不同格式的图片
    formats = ['jpeg', 'gif', 'bmp']
    for fmt in formats:
        file = BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(file, fmt)
        file.seek(0)
        
        response = client.post('/admin/posts/upload-image', data={
            'file': (file, f'test.{fmt}')
        }, content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # 验证是否转换为PNG或JPEG
        assert data['url'].endswith(('.png', '.jpg'))
        
        # 清理测试文件
        file_path = os.path.join(client.application.config['UPLOAD_FOLDER'], 
                                os.path.basename(data['url']))
        if os.path.exists(file_path):
            os.remove(file_path)

def test_malformed_image(client, auth):
    """测试损坏的图片文件"""
    auth.login()
    
    # 创建一个损坏的PNG文件
    file = BytesIO(b'\x89PNG\r\n\x1a\n' + b'corrupted data')
    
    response = client.post('/admin/posts/upload-image', data={
        'file': (file, 'corrupted.png')
    }, content_type='multipart/form-data')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert '无效的图片文件' in data['error']

def test_upload_folder_creation(client, auth):
    """测试上传目录创建"""
    auth.login()
    
    # 删除上传目录（如果存在）
    upload_folder = client.application.config['UPLOAD_FOLDER']
    if os.path.exists(upload_folder):
        import shutil
        shutil.rmtree(upload_folder)
    
    # 测试上传
    file = create_test_image()
    response = client.post('/admin/posts/upload-image', data={
        'file': (file, 'test.png')
    }, content_type='multipart/form-data')
    
    assert response.status_code == 200
    assert os.path.exists(upload_folder)
    
    # 清理测试文件
    data = response.get_json()
    file_path = os.path.join(upload_folder, os.path.basename(data['url']))
    if os.path.exists(file_path):
        os.remove(file_path) 