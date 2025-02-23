"""
文件名：test_auth.py
描述：认证功能测试
作者：denny
创建日期：2024-03-20
"""

from flask_wtf.csrf import generate_csrf

def test_login(client, auth):
    """测试登录功能"""
    # 测试登录页面
    response = client.get('/admin/login')
    assert response.status_code == 302  # 重定向到auth.login
    assert '/auth/login' in response.headers['Location']  # 检查是否重定向到登录页面

    # 测试登录成功
    response = auth.login()
    assert response.status_code == 302  # 重定向到管理后台
    assert response.headers['Location'].endswith('/admin/')

    # 测试登录失败
    response = auth.login('wrong', 'wrong', follow_redirects=False)
    assert response.status_code == 302  # 重定向到登录页面
    assert response.headers['Location'].endswith('/admin/')  # 检查是否重定向到管理后台

def test_logout(client, auth):
    """测试登出功能"""
    auth.login(follow_redirects=True)
    response = auth.logout()
    assert response.status_code == 302  # 重定向到登录页
    assert response.headers['Location'].endswith('/auth/login')

def test_login_required(client):
    """测试需要登录的页面"""
    # 测试访问管理后台首页
    response = client.get('/admin/')
    assert response.status_code == 302  # 重定向到登录页
    assert '/auth/login' in response.headers['Location']  # 检查是否重定向到登录页面
    
    # 测试访问上传页面
    response = client.get('/admin/upload')
    assert response.status_code == 308  # 永久重定向到带斜杠的URL
    assert response.headers['Location'].endswith('/admin/upload/')

def test_already_logged_in(client, auth):
    """测试已登录用户访问登录页面"""
    auth.login(follow_redirects=True)
    response = client.get('/admin/login')
    assert response.status_code == 302  # 重定向到管理后台
    assert response.headers['Location'].endswith('/admin/')