"""
文件名：auth.py
描述：认证表单
作者：denny
创建日期：2025-02-16
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class LoginForm(FlaskForm):
    """登录表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')

class RegisterForm(FlaskForm):
    """注册表单"""
    username = StringField('用户名', validators=[
        DataRequired(),
        Length(1, 64)
    ])
    email = StringField('电子邮箱', validators=[
        DataRequired(),
        Length(1, 120),
        Email()
    ])
    password = PasswordField('密码', validators=[
        DataRequired(),
        Length(min=6),
        EqualTo('confirm_password', message='两次输入的密码不一致')
    ])
    confirm_password = PasswordField('确认密码', validators=[DataRequired()]) 