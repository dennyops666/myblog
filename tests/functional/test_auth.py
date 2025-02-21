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
    csrf_token = response.headers.get('X-CSRF-Token')
    
    # 测试登录成功
    response = client.post('/admin/login', data={
        'username': 'test_user',
        'password': 'password',
        'csrf_token': csrf_token
    }, headers={
        'X-CSRF-Token': csrf_token
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'] == '/admin/'
    
    # 测试登录状态
    response = client.get('/admin/')
    assert '退出'.encode() in response.data
    
    # 测试使用错误密码登录
    response = client.get('/admin/login')
    csrf_token = response.headers.get('X-CSRF-Token')
    response = client.post('/admin/login', data={
        'username': 'test_user',
        'password': 'wrong_password',
        'csrf_token': csrf_token
    }, headers={
        'X-CSRF-Token': csrf_token
    })
    assert response.status_code == 200
    assert '用户名或密码错误'.encode() in response.data
    
    # 测试使用错误用户名登录
    response = client.get('/admin/login')
    csrf_token = response.headers.get('X-CSRF-Token')
    response = client.post('/admin/login', data={
        'username': 'wrong_user',
        'password': 'password',
        'csrf_token': csrf_token
    }, headers={
        'X-CSRF-Token': csrf_token
    })
    assert response.status_code == 200
    assert '用户名或密码错误'.encode() in response.data

def test_logout(client, auth):
    """测试登出功能"""
    auth.login()
    response = auth.logout()
    assert response.status_code == 302
    assert response.headers['Location'] == '/admin/login' 