"""
检查应用的路由脚本
"""
from flask import Flask

# 创建一个测试应用
def create_test_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/blog-dev.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 注册蓝图
    from app.views.blog import bp as blog_view
    from app.controllers.blog import blog_bp
    
    app.register_blueprint(blog_view, url_prefix='/blog_view')
    app.register_blueprint(blog_bp, url_prefix='/blog')
    
    return app

if __name__ == '__main__':
    try:
        app = create_test_app()
        
        print("应用路由列表:")
        print("=" * 50)
        for rule in app.url_map.iter_rules():
            print(f"{rule} -> {rule.endpoint}")
        
        print("\n包含'post'的路由:")
        print("=" * 50)
        for rule in app.url_map.iter_rules():
            if 'post' in str(rule):
                print(f"{rule} -> {rule.endpoint}")
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        print(traceback.format_exc()) 