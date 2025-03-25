"""
文件名：user.py
描述：用户表单
作者：denny
创建日期：2024-03-21
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional

class UserForm(FlaskForm):
    """用户创建表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    nickname = StringField('昵称', validators=[Optional(), Length(max=50)])
    role_id = SelectField('角色', coerce=int)
    is_active = BooleanField('启用账户')
    
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        from app.models.role import Role
        self.role_id.choices = [(role.id, role.name) for role in Role.query.all()]

class UserEditForm(FlaskForm):
    """用户编辑表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[EqualTo('password')])
    nickname = StringField('昵称', validators=[Optional(), Length(max=50)])
    role_id = SelectField('角色', coerce=int)
    is_active = BooleanField('启用账户')
    
    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        from app.models.role import Role
        self.role_id.choices = [(role.id, role.name) for role in Role.query.all()]

class ProfileForm(FlaskForm):
    """个人资料表单"""
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('新密码', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[EqualTo('password')])
    nickname = StringField('昵称', validators=[Optional(), Length(max=50)])
    bio = TextAreaField('个人简介', validators=[Optional(), Length(max=500)]) 