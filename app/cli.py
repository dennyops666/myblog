"""
文件名：cli.py
描述：CLI命令
作者：denny
创建日期：2024-03-21
"""

import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.user import User
from app.models.role import Role
from werkzeug.security import generate_password_hash

@click.command('init-db')
@with_appcontext
def init_db_command():
    """清空数据库并创建新表"""
    db.drop_all()
    db.create_all()
    click.echo('数据库已初始化.')

@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """添加初始数据"""
    # 创建角色
    admin_role = Role(name='admin', description='管理员')
    user_role = Role(name='user', description='普通用户')
    db.session.add(admin_role)
    db.session.add(user_role)
    
    # 创建管理员用户
    admin = User(
        username='admin',
        email='admin@example.com',
        password_hash=generate_password_hash('admin123'),
        is_admin=True
    )
    admin.roles.append(admin_role)
    
    # 创建测试用户
    user = User(
        username='user',
        email='user@example.com',
        password_hash=generate_password_hash('user123'),
        is_admin=False
    )
    user.roles.append(user_role)
    
    db.session.add(admin)
    db.session.add(user)
    db.session.commit()
    
    click.echo('初始数据已添加.')

@click.command('create-admin')
@click.option('--username', required=True, help='管理员用户名')
@click.option('--email', required=True, help='管理员邮箱')
@click.option('--password', required=True, help='管理员密码')
@with_appcontext
def create_admin_command(username, email, password):
    """创建管理员用户"""
    # 检查用户是否存在
    if User.query.filter((User.username == username) | (User.email == email)).first():
        click.echo('用户名或邮箱已存在.')
        return
    
    # 检查admin角色是否存在
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='管理员')
        db.session.add(admin_role)
    
    # 创建管理员用户
    admin = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        is_admin=True
    )
    admin.roles.append(admin_role)
    
    db.session.add(admin)
    db.session.commit()
    
    click.echo(f'管理员 {username} 已创建.')

@click.command('fix-comment-status')
@with_appcontext
def fix_comment_status():
    """修复所有评论的状态，确保已登录用户的评论状态为已审核，匿名用户的评论状态为待审核"""
    from app.services.comment import CommentService
    from flask import current_app
    
    current_app.logger.info("开始修复评论状态...")
    comment_service = CommentService()
    result = comment_service.ensure_user_comment_status()
    
    if result['status'] == 'success':
        click.echo(f"评论状态修复完成: {result['message']}")
    else:
        click.echo(f"评论状态修复失败: {result['message']}")

def register_commands(app):
    """注册命令行命令"""
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_db_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(fix_comment_status) 