"""
文件名：auth.py
描述：认证表单
作者：denny
创建日期：2024-03-21
"""

from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp, Optional
from app.models import User
from app.utils.security import generate_token, verify_token
from . import BaseForm
import re

def password_complexity(form, field):
    """验证密码复杂度 - 简化版"""
    password = field.data
    if not password:  # 如果是编辑用户时，密码可以为空
        return True
    
    # 只检查密码长度，移除复杂度要求
    if len(password) < 6:  # 降低最小长度要求
        raise ValidationError('密码长度必须至少6个字符')
    return True

class OptionalPasswordEqualTo(EqualTo):
    """自定义的EqualTo验证器，当两个字段都为空时不进行验证"""
    def __call__(self, form, field):
        if not field.data and not form[self.fieldname].data:
            return True
        return super().__call__(form, field)

class LoginForm(BaseForm):
    """登录表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate(self, extra_validators=None):
        """重写验证方法，支持extra_validators参数"""
        if not super(LoginForm, self).validate(extra_validators=extra_validators):
            return False
        return True

class RegisterForm(BaseForm):
    """注册表单"""
    username = StringField('用户名', validators=[
        DataRequired(message='用户名不能为空'),
        Length(1, 64, message='用户名长度必须在1到64个字符之间'),
        Regexp(r'^[A-Za-z0-9_]+$', message='用户名只能包含字母、数字和下划线')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(message='邮箱不能为空'),
        Email(message='请输入有效的邮箱地址'),
        Length(1, 120, message='邮箱长度必须在1到120个字符之间')
    ])
    nickname = StringField('昵称', validators=[
        Optional(),
        Length(0, 64, message='昵称长度不能超过64个字符')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='密码不能为空'),
        password_complexity
    ])
    password2 = PasswordField('确认密码', validators=[
        DataRequired(message='确认密码不能为空'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    is_active = BooleanField('启用账号', default=True)
    submit = SubmitField('保存')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.edit_user = kwargs.get('obj')  # 获取编辑的用户对象

    def validate_username(self, field):
        """验证用户名是否已存在"""
        if field.data.lower() == 'admin':
            raise ValidationError('不能使用保留的用户名')
        user = User.query.filter(User.username == field.data).first()
        if user and (not self.edit_user or user.id != self.edit_user.id):
            raise ValidationError('该用户名已被使用')

    def validate_email(self, field):
        """验证邮箱是否已存在"""
        user = User.query.filter(User.email == field.data).first()
        if user and (not self.edit_user or user.id != self.edit_user.id):
            raise ValidationError('该邮箱已被注册')

    def validate(self, extra_validators=None):
        """重写验证方法，支持extra_validators参数"""
        if not super(RegisterForm, self).validate(extra_validators=extra_validators):
            return False
            
        if self.edit_user:
            # 编辑用户时的密码验证逻辑
            has_password = bool(self.password.data)
            has_password2 = bool(self.password2.data)
            
            # 如果两个密码字段都为空，表示不修改密码
            if not has_password and not has_password2:
                return True
                
            # 如果只填写了一个密码字段，报错
            if has_password != has_password2:
                if not has_password:
                    self.password.errors.append('如果要修改密码，请填写新密码')
                if not has_password2:
                    self.password2.errors.append('如果要修改密码，请填写确认密码')
                return False
                
            # 如果两个密码字段都有值，进行密码复杂度和一致性验证
            if has_password and has_password2:
                if self.password.data != self.password2.data:
                    self.password2.errors.append('两次输入的密码不一致')
                    return False
                try:
                    password_complexity(self, self.password)
                except ValidationError as e:
                    self.password.errors.append(str(e))
                    return False
        else:
            # 创建用户时的密码验证逻辑
            if not self.password.data:
                self.password.errors.append('创建用户时密码不能为空')
                return False
            if not self.password2.data:
                self.password2.errors.append('创建用户时确认密码不能为空')
                return False
            if self.password.data != self.password2.data:
                self.password2.errors.append('两次输入的密码不一致')
                return False
        
        return True

class PasswordResetRequestForm(BaseForm):
    """密码重置请求表单"""
    email = StringField('邮箱', validators=[
        DataRequired(),
        Email(message='请输入有效的邮箱地址'),
        Length(1, 120, message='邮箱长度必须在1到120个字符之间')
    ])
    submit = SubmitField('发送重置邮件')
    
    def generate_reset_token(self):
        """生成密码重置令牌"""
        user = User.get_by_email(self.email.data)
        if not user:
            return None
        return generate_token(
            {'user_id': user.id, 'action': 'reset_password'},
            expiration=3600  # 1小时过期
        )

class PasswordResetForm(BaseForm):
    """密码重置表单"""
    token = StringField('令牌', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[
        DataRequired(message='请输入新密码'),
        password_complexity
    ])
    password2 = PasswordField('确认新密码', validators=[
        DataRequired(message='请再次输入新密码'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    submit = SubmitField('重置密码')
    
    def validate(self, extra_validators=None):
        """重写验证方法，支持extra_validators参数"""
        if not super(PasswordResetForm, self).validate(extra_validators=extra_validators):
            return False
        return True

class PasswordChangeForm(BaseForm):
    """密码修改表单"""
    old_password = PasswordField('原密码', validators=[
        DataRequired(message='请输入原密码')
    ])
    new_password = PasswordField('新密码', validators=[
        DataRequired(message='请输入新密码'),
        password_complexity
    ])
    new_password2 = PasswordField('确认新密码', validators=[
        DataRequired(message='请再次输入新密码'),
        EqualTo('new_password', message='两次输入的密码不一致')
    ])
    submit = SubmitField('修改密码')