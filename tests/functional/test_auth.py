"""
文件名：test_auth.py
描述：认证功能测试
作者：denny
创建日期：2024-03-20
"""

def test_login(client, auth):
    """测试登录功能"""
    # 测试登录页面
    response = client.get('/admin/login')
    assert response.status_code == 200
    assert '管理员登录'.encode() in response.data
    
    # 测试登录成功
    response = auth.login()
    assert response.headers['Location'] == '/admin/'
    
    # 测试登录状态
    response = client.get('/admin/')
    assert '退出'.encode() in response.data
    
    # 测试使用错误密码登录
    response = auth.login('admin', 'wrong_password')
    assert '用户名或密码错误'.encode() in response.data
    
    # 测试使用错误用户名登录
    response = auth.login('wrong_user', 'password')
    assert '用户名或密码错误'.encode() in response.data

def test_logout(client, auth):
    """测试登出功能"""
    # 先登录
    auth.login()
    
    # 测试登出
    response = auth.logout()
    assert response.headers['Location'] == '/admin/login'
    
    # 测试登出后访问管理页面
    response = client.get('/admin/')
    assert response.headers['Location'].startswith('/admin/login') 