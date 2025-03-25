"""
评论功能调试脚本
"""
from flask import Flask, jsonify
from app.extensions import db
from app.services.comment import CommentService

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/blog-dev.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'debug-secret-key'
    
    # 初始化扩展
    db.init_app(app)
    
    return app

def test_create_comment():
    """测试创建评论功能"""
    # 创建评论的参数
    post_id = 20
    content = "测试评论内容"
    author_id = 1
    nickname = "admin"
    email = None
    parent_id = None
    
    print(f"正在测试创建评论: post_id={post_id}, author_id={author_id}")
    
    # 调用评论服务创建评论
    result = CommentService.create_comment(
        post_id=post_id,
        content=content,
        author_id=author_id,
        nickname=nickname,
        email=email,
        parent_id=parent_id
    )
    
    # 输出结果
    print(f"创建评论结果: {result}")
    return result

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        test_create_comment() 