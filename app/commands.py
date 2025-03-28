"""
文件名：commands.py
描述：Flask CLI 命令
作者：denny
"""

import click
from flask.cli import with_appcontext
from app.models import User, Role
from app.models.permission import Permission
from app.extensions import db

def register_commands(app):
    """注册命令行命令"""

    @app.cli.command('init-db')
    @with_appcontext
    def init_db():
        """初始化数据库"""
        click.echo('正在初始化数据库...')
        db.create_all()
        click.echo('数据库初始化完成。')

    @app.cli.command('create-admin')
    @click.argument('username')
    @click.argument('email')
    @click.argument('password')
    @with_appcontext
    def create_admin(username, email, password):
        """创建管理员用户"""
        click.echo('正在创建管理员用户...')
        
        # 检查用户是否已存在
        if User.query.filter_by(username=username).first():
            click.echo('错误：用户名已存在。')
            return
        if User.query.filter_by(email=email).first():
            click.echo('错误：邮箱已存在。')
            return

        # 创建管理员角色
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            click.echo('错误：管理员角色不存在。')
            return

        # 创建管理员用户
        admin = User(
            username=username,
            email=email,
            password=password,
            is_active=True
        )
        admin.roles.append(admin_role)
        db.session.add(admin)
        db.session.commit()
        click.echo('管理员用户创建成功。')

    @app.cli.command('create-roles')
    @with_appcontext
    def create_roles():
        """创建角色"""
        click.echo('正在创建角色...')
        
        # 检查角色是否已存在
        if Role.query.first():
            click.echo('错误：角色已存在。')
            return

        # 创建角色
        roles = [
            ('super_admin', '超级管理员', 0xFFFF, False),
            ('admin', '管理员', 0x7FFF, False),
            ('editor', '编辑', 0x3FFF, False),
            ('user', '普通用户', 0x1FFF, True)
        ]

        for name, description, permissions, is_default in roles:
            role = Role(
                name=name,
                description=description,
                permissions=permissions,
                is_default=is_default
            )
            db.session.add(role)

        db.session.commit()
        click.echo('角色创建成功。')

    return app 