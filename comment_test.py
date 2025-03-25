import os
import sys
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.curdir))

# 导入应用创建函数
from app import create_app
from app.models.comment import Comment, CommentStatus
from app.extensions import db

# 创建测试应用
app = create_app()

# 在应用上下文中执行测试
with app.app_context():
    try:
        # 创建一个匿名评论
        anonymous_comment = Comment(
            content="这是一个测试匿名评论内容",
            post_id=1,
            nickname="测试匿名用户",
            email="test_anon@example.com",
            status=CommentStatus.PENDING,  # 明确设置为待审核
            created_at=datetime.now()
        )
        
        # 打印初始状态
        print(f"初始评论状态: {anonymous_comment.status}")
        
        # 添加到数据库
        db.session.add(anonymous_comment)
        db.session.flush()
        
        # 打印flush后状态
        print(f"Flush后评论状态: {anonymous_comment.status}")
        
        # 提交事务
        db.session.commit()
        
        # 重新加载评论
        db.session.refresh(anonymous_comment)
        
        # 打印提交后的状态
        print(f"Commit后评论状态: {anonymous_comment.status}")
        print(f"评论ID: {anonymous_comment.id}")
        
        # 再次从数据库查询
        reloaded_comment = Comment.query.get(anonymous_comment.id)
        print(f"重新查询评论状态: {reloaded_comment.status}")
        
        print("测试完成")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        db.session.rollback() 