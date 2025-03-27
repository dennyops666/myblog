import sys
print("正在导入所需模块...")
from app import create_app
from app.models.user import User
from flask import url_for
import traceback

print("正在创建测试应用...")
app = create_app('test')

with app.app_context():
    with app.test_client() as client:
        print("正在尝试访问管理后台首页...")
        # 先登录
        from app.extensions import db
        
        # 确保admin用户存在
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("错误：找不到admin用户！")
            sys.exit(1)
        
        print(f"找到admin用户: {admin.username}")
        
        # 登录
        print("正在尝试登录...")
        response = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin'  # 假设admin密码为admin
        }, follow_redirects=True)
        
        if response.status_code != 200:
            print(f"错误：登录失败，状态码: {response.status_code}")
            print(response.data.decode('utf-8'))
            sys.exit(1)
        
        print("登录成功，尝试访问仪表板...")
        
        # 访问仪表板
        try:
            response = client.get('/admin/', follow_redirects=True)
            print(f"仪表板访问状态码: {response.status_code}")
            
            if response.status_code != 200:
                print("错误：访问仪表板失败")
                print(response.data.decode('utf-8'))
            else:
                print("成功访问仪表板页面")
                
        except Exception as e:
            print(f"访问仪表板时发生错误: {str(e)}")
            print(traceback.format_exc()) 