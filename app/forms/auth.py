"""
文件名：auth.py
描述：认证表单
作者：denny
创建日期：2024-03-21
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    """登录表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class RegisterForm(FlaskForm):
    """注册表单"""
    username = StringField('用户名', validators=[
        DataRequired(),
        Length(1, 64, message='用户名长度必须在1到64个字符之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(),
        Email(message='请输入有效的邮箱地址'),
        Length(1, 120, message='邮箱长度必须在1到120个字符之间')
    ])
    nickname = StringField('昵称', validators=[
        DataRequired(),
        Length(1, 64, message='昵称长度必须在1到64个字符之间')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(),
        Length(6, 128, message='密码长度必须在6到128个字符之间')
    ])
    password2 = PasswordField('确认密码', validators=[
        DataRequired(),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    submit = SubmitField('注册')

    def validate_username(self, field):
        """验证用户名是否已存在"""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用')

    def validate_email(self, field):
        """验证邮箱是否已存在"""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册') 