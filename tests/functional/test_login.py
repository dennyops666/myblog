import requests
from bs4 import BeautifulSoup

def test_login():
    # 创建会话对象
    session = requests.Session()
    
    # 第一步：获取登录页面
    print("1. 获取登录页面...")
    response = session.get('http://localhost:5000/auth/login')
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 第二步：提交登录表单
    print("\n2. 提交登录表单...")
    login_data = {
        'username': 'admin',
        'password': 'admin123',
        'remember_me': 'y'
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    response = session.post(
        'http://localhost:5000/auth/login',
        data=login_data,
        headers=headers,
        allow_redirects=True
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应内容: {response.text[:500]}...")  # 只打印前500个字符
    
    # 第三步：检查是否成功登录
    print("\n3. 检查登录状态...")
    response = session.get('http://localhost:5000/admin/')
    print(f"访问管理页面状态码: {response.status_code}")
    print(f"最终URL: {response.url}")

if __name__ == '__main__':
    test_login() 