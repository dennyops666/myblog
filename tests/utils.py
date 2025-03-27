"""
文件名：utils.py
描述：测试辅助工具函数
创建日期：2025-03-26
"""

def login(client, username, password):
    """辅助函数：登录用户"""
    return client.post('/auth/login', data={
        'username': username,
        'password': password,
        'remember_me': 'y'
    }, follow_redirects=True)

def logout(client):
    """辅助函数：登出用户"""
    return client.get('/auth/logout', follow_redirects=True) 