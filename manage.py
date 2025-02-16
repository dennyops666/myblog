#!/usr/bin/env python
import click
from app import create_app, db
from app.models import User, Post, Category, Tag, Comment, Role

app = create_app()

@click.group()
def cli():
    """管理脚本命令组"""
    pass

@cli.command(name='init_test_db')
def init_test_db():
    """初始化测试数据库"""
    click.echo('正在初始化测试数据库...')
    
    with app.app_context():
        # 删除所有表
        db.drop_all()
        # 创建所有表
        db.create_all()
        
        # 创建角色
        admin_role = Role(name='admin', description='管理员')
        user_role = Role(name='user', description='普通用户')
        db.session.add(admin_role)
        db.session.add(user_role)
        db.session.commit()
        
        # 创建测试用户
        admin = User(
            username='admin',
            email='admin@example.com',
            role_id=admin_role.id
        )
        admin.set_password('admin123')
        
        test_user = User(
            username='test',
            email='test@example.com',
            role_id=user_role.id
        )
        test_user.set_password('test123')
        
        db.session.add(admin)
        db.session.add(test_user)
        db.session.commit()
        
        # 创建测试分类
        categories = [
            Category(name='技术', description='技术相关文章'),
            Category(name='生活', description='生活随笔'),
            Category(name='项目', description='项目展示')
        ]
        db.session.add_all(categories)
        db.session.commit()
        
        # 创建测试标签
        tags = [
            Tag(name='Python'),
            Tag(name='Flask'),
            Tag(name='测试'),
            Tag(name='安全')
        ]
        db.session.add_all(tags)
        db.session.commit()
        
        # 创建测试文章
        posts = [
            Post(
                title='测试文章1',
                content='这是测试文章1的内容',
                author=admin,
                category=categories[0],
                tags=[tags[0], tags[1]]
            ),
            Post(
                title='测试文章2',
                content='这是测试文章2的内容',
                author=test_user,
                category=categories[1],
                tags=[tags[2], tags[3]]
            )
        ]
        db.session.add_all(posts)
        db.session.commit()
        
        # 创建测试评论
        comments = [
            Comment(
                content='测试评论1',
                post=posts[0],
                author_id=test_user.id,
                author_name=test_user.username,
                author_email=test_user.email,
                status=1
            ),
            Comment(
                content='测试评论2',
                post=posts[0],
                author_id=admin.id,
                author_name=admin.username,
                author_email=admin.email,
                status=1
            ),
            Comment(
                content='测试评论3',
                post=posts[1],
                author_id=admin.id,
                author_name=admin.username,
                author_email=admin.email,
                status=1
            )
        ]
        db.session.add_all(comments)
        db.session.commit()
        
        click.echo('测试数据库初始化完成！')

if __name__ == '__main__':
    cli() 