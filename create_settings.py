"""
创建settings表并添加初始数据
"""

from app import create_app
from app.extensions import db
from app.models.settings import Settings
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    # 检查表是否存在
    inspector = inspect(db.engine)
    if not inspector.has_table('settings'):
        # 创建表
        db.create_all()
        print("创建settings表成功")
    
    try:
        # 检查是否已有数据
        settings = Settings.query.first()
        if not settings:
            # 添加初始数据
            settings = Settings(
                blog_name='MyBlog',
                blog_description='这是一个使用Flask开发的个人博客系统',
                posts_per_page=10,
                allow_registration=True,
                allow_comments=True
            )
            db.session.add(settings)
            db.session.commit()
            print("添加初始设置数据成功")
        else:
            print("设置数据已存在")
    except Exception as e:
        print(f"发生错误: {e}")
        db.session.rollback()

print("操作完成") 