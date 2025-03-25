"""
文件名：test_user_model.py
描述：User 模型测试
作者：denny
创建日期：2024-03-10
"""

def test_user_model_methods(app):
    """测试 User 模型的方法"""
    from app.models.user import User
    from app.models.role import Role
    from app.extensions import db
    
    # 初始化数据库
    with app.app_context():
        db.create_all()
        
        # 创建测试用户
        user = User(username='testuser', email='test_user_model@example.com', is_active=True)
        user.set_password('password123')
        
        # 测试密码相关方法
        assert user.verify_password('password123')
        assert not user.verify_password('wrongpassword')
        
        # 测试密码验证错误
        try:
            user.verify_password('')
            assert False, '应该抛出 ValueError'
        except ValueError:
            pass
        
        try:
            user.verify_password(None)
            assert False, '应该抛出 ValueError'
        except ValueError:
            pass
        
        # 测试角色相关方法
        test_role = Role(name='test_role', description='测试角色')
        db.session.add(test_role)
        db.session.commit()
        
        # 测试添加角色
        user.add_role(test_role)
        assert user.has_role('test_role')
        
        # 测试移除角色
        user.remove_role(test_role)
        assert not user.has_role('test_role')
        
        # 测试角色验证错误
        try:
            user.has_role('')
            assert False, '应该抛出 ValueError'
        except ValueError:
            pass
        
        try:
            user.add_role(None)
            assert False, '应该抛出 ValueError'
        except ValueError:
            pass
        
        try:
            user.add_role('not_a_role')
            assert False, '应该抛出 TypeError'
        except TypeError:
            pass
        
        # 测试状态相关方法
        assert user.status == 'active'  # 默认状态
        
        user.deactivate()
        assert user.status == 'inactive'
        assert not user.is_active
        
        user.activate()
        assert user.status == 'active'
        assert user.is_active
        
        # 测试属性方法
        assert user.display_name == 'testuser'  # 没有昵称时返回用户名
        
        user.nickname = 'Test User'
        assert user.display_name == 'Test User'  # 有昵称时返回昵称
        
        assert user.avatar_url == '/static/images/default-avatar.png'  # 默认头像
        
        # 测试序列化方法
        db.session.add(user)
        db.session.commit()
        
        user_dict = user.to_dict()
        assert user_dict['username'] == 'testuser'
        assert user_dict['email'] == 'test_user_model@example.com'
        assert user_dict['nickname'] == 'Test User'
        assert user_dict['avatar'] == '/static/images/default-avatar.png'
        assert user_dict['is_active'] == True
        assert user_dict['is_admin'] == False
        assert user_dict['is_super_admin'] == False
        assert 'stats' in user_dict
        assert user_dict['stats']['posts']['total'] == 0
        assert user_dict['stats']['comments']['total'] == 0
        assert user_dict['stats']['roles']['total'] == 0
        
        # 测试简单序列化方法
        simple_dict = user.to_simple_dict()
        assert simple_dict['username'] == 'testuser'
        assert simple_dict['email'] == 'test_user_model@example.com'
        assert simple_dict['nickname'] == 'Test User'
        assert simple_dict['avatar'] == '/static/images/default-avatar.png'
        assert simple_dict['is_active'] == True
        assert simple_dict['is_admin'] == False
        assert simple_dict['is_super_admin'] == False
        assert 'stats' not in simple_dict
        
        # 清理数据
        db.session.delete(user)
        db.session.delete(test_role)
        db.session.commit()
