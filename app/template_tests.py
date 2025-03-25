def register_template_tests(app):
    """注册模板测试器"""
    
    @app.template_test('admin')
    def is_admin(user):
        """检查用户是否是管理员"""
        if not user:
            return False
        return user.is_admin
    
    @app.template_test('moderator')
    def is_moderator(user):
        """检查用户是否是版主"""
        if not user:
            return False
        return user.is_moderator
    
    @app.template_test('author')
    def is_author(user):
        """检查用户是否是作者"""
        if not user:
            return False
        return user.is_author 