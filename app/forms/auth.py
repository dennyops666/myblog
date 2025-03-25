"""
文件名：auth.py
描述：认证表单
作者：denny
创建日期：2024-03-21
"""

from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp
from app.models.user import User
from app.utils.security import generate_token, verify_token
from . import BaseForm
import re

def password_complexity(form, field):
    """验证密码复杂度"""
    password = field.data
    if not password:  # 如果是编辑用户时，密码可以为空
        return True
    
    # 检查密码长度和复杂度
    errors = []
    if len(password) < 6:
        errors.append('密码长度必须至少6个字符')
    if not re.search(r'[A-Za-z]', password):
        errors.append('密码必须包含至少一个字母')
    if not re.search(r'[0-9]', password):
        errors.append('密码必须包含至少一个数字')
    if errors:
        raise ValidationError('\n'.join(errors))
    return True

class LoginForm(BaseForm):
    """登录表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate(self, **kwargs):
        """重写验证方法，接受任意关键字参数"""
        if not super(LoginForm, self).validate():
            return False
        return True

class RegisterForm(BaseForm):
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
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码'),
        password_complexity
    ])
    password2 = PasswordField('确认密码', validators=[
        DataRequired(message='请再次输入密码'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    is_active = BooleanField('启用账号', default=True)
    submit = SubmitField('注册')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        if not super(RegisterForm, self).validate():
            return False
            
        if self.edit_user:
            # 编辑用户时，如果密码为空，则不修改密码
            if not self.password.data and not self.password2.data:
                return True
            # 如果只填写了一个密码字段，报错
            if bool(self.password.data) != bool(self.password2.data):
                self.password2.errors.append('如果要修改密码，请填写两个密码字段')
                return False
        else:
            # 创建用户时，密码必填
            if not self.password.data:
                self.password.errors.append('创建用户时密码不能为空')
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
        """重写验证方法"""
        if not super(PasswordResetForm, self).validate():
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