"""
文件名：commands.py
描述：Flask CLI 命令
作者：denny
创建日期：2024-03-21
"""

import click
from flask.cli import with_appcontext
from app.models import User, Role
from app.models.permission import Permission
from app.extensions import db

@click.command('create-admin')
@with_appcontext
def create_admin():
    """创建管理员用户"""
    username = click.prompt('请输入管理员用户名', type=str)
    email = click.prompt('请输入管理员邮箱', type=str)
    password = click.prompt('请输入管理员密码', type=str, hide_input=True)
    
    # 获取管理员角色
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        click.echo('错误：管理员角色不存在，请先运行 init-roles 命令')
        return
    
    user = User(
        username=username,
        email=email,
        role=admin_role,
        is_active=True
    )
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        click.echo(f'管理员用户 {username} 创建成功！')
    except Exception as e:
        db.session.rollback()
        click.echo(f'创建管理员用户失败：{str(e)}')

@click.command('init-roles')
@with_appcontext
def init_roles():
    """初始化角色"""
    # 创建角色
    roles = {
        'user': (Permission.FOLLOW |
                Permission.COMMENT |
                Permission.WRITE, True),
        'moderator': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE |
                     Permission.MODERATE, False),
        'admin': (0xff, False)  # 所有权限
    }
    
    for role_name, (permissions, is_default) in roles.items():
        role = Role.query.filter_by(name=role_name).first()
        if role is None:
            role = Role(name=role_name)
        role.permissions = permissions
        role.default = is_default
        db.session.add(role)
    
    try:
        db.session.commit()
        click.echo('角色初始化成功！')
    except Exception as e:
        db.session.rollback()
        click.echo(f'角色初始化失败：{str(e)}')

@click.command('init-db')
@with_appcontext
def init_db():
    """初始化数据库"""
    db.create_all()
    click.echo('数据库初始化成功！') 