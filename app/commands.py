"""
文件名：commands.py
描述：命令行工具
作者：denny
创建日期：2025-02-16
"""

import click
from flask.cli import with_appcontext
from app.models import User, db

@click.command('create-admin')
@click.option('--username', prompt='管理员用户名', help='管理员用户名')
@click.option('--email', prompt='管理员邮箱', help='管理员邮箱')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='管理员密码')
@with_appcontext
def create_admin(username, email, password):
    """创建管理员账户"""
    try:
        user = User(username=username, email=email)
        user.password = password
        db.session.add(user)
        db.session.commit()
        click.echo('管理员账户创建成功！')
    except Exception as e:
        click.echo(f'创建失败：{str(e)}')

@click.command('init-db')
@with_appcontext
def init_db():
    """初始化数据库"""
    try:
        db.create_all()
        click.echo('数据库初始化成功！')
    except Exception as e:
        click.echo(f'初始化失败：{str(e)}') 