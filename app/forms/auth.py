"""
文件名：auth.py
描述：认证表单
作者：denny
创建日期：2024-03-21
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp
from app.models.user import User
import re

def password_complexity(form, field):
    """验证密码复杂度"""
    password = field.data
    if not password:  # 如果是编辑用户时，密码可以为空
        return True
    
    # 检查密码长度和复杂度
    if len(password) < 6 or not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
        # 不抛出ValidationError，而是设置一个标志
        form._password_invalid = True
        return False
    return True

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
        Length(1, 64, message='用户名长度必须在1到64个字符之间'),
        Regexp(r'^[A-Za-z0-9_]+$', message='用户名只能包含字母、数字和下划线')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(),
        Email(message='请输入有效的邮箱地址'),
        Length(1, 120, message='邮箱长度必须在1到120个字符之间')
    ])
    nickname = StringField('昵称', validators=[
        Length(0, 64, message='昵称长度不能超过64个字符')  # 昵称可选
    ])
    password = PasswordField('密码')  # 移除所有验证器
    password2 = PasswordField('确认密码')  # 移除所有验证器
    is_active = BooleanField('启用账号', default=True)
    submit = SubmitField('注册')

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.edit_user = kwargs.get('obj')  # 获取编辑的用户对象

    def validate_username(self, field):
        """验证用户名是否已存在"""
        if User.query.filter_by(username=field.data).first() and (not self.edit_user or field.data != self.edit_user.username):
            raise ValidationError('该用户名已被使用')

    def validate_email(self, field):
        """验证邮箱是否已存在"""
        if User.query.filter_by(email=field.data).first() and (not self.edit_user or field.data != self.edit_user.email):
            raise ValidationError('该邮箱已被注册')

    def validate(self):
        """重写验证方法"""
        # 保存原始密码值
        password = self.password.data
        password2 = self.password2.data
        
        # 临时清空密码字段，防止验证
        self.password.data = None
        self.password2.data = None
        
        # 验证其他字段
        valid = super(RegisterForm, self).validate()
        
        # 恢复密码值
        self.password.data = password
        self.password2.data = password2
        
        # 手动验证密码
        if not self.edit_user and not password:  # 创建用户时密码必填
            valid = False
            self._password_invalid = True
        elif password:  # 如果有密码，验证复杂度
            if not password_complexity(self, self.password):
                valid = False
            elif password != password2:  # 验证两次密码是否一致
                valid = False
                self._password_mismatch = True
        
        return valid 