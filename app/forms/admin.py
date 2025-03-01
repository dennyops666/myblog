"""
文件名：admin.py
描述：管理后台表单
作者：denny
创建日期：2024-03-21
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, PasswordField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email, Optional, URL, EqualTo
from app.models.post import PostStatus

class PostForm(FlaskForm):
    """文章表单"""
    class Meta:
        csrf = False  # 禁用 CSRF 保护
        
    title = StringField('标题', validators=[DataRequired(), Length(1, 200)])
    content = TextAreaField('内容', validators=[DataRequired()])
    summary = TextAreaField('摘要', validators=[Optional(), Length(0, 500)])
    category_id = SelectField('分类', coerce=int, validators=[DataRequired()])
    status = SelectField('状态', choices=[(status.value, status.name) for status in PostStatus], default=PostStatus.DRAFT.value)
    tags = SelectMultipleField('标签', coerce=int)

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        from app.models import Category, Tag
        self.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
        self.tags.choices = [(t.id, t.name) for t in Tag.query.all()]

class CategoryForm(FlaskForm):
    """分类表单"""
    class Meta:
        csrf = False  # 禁用 CSRF 保护
        
    name = StringField('名称', validators=[DataRequired(), Length(1, 64)])
    slug = StringField('别名', validators=[DataRequired(), Length(1, 64)])
    description = TextAreaField('描述', validators=[Optional(), Length(0, 200)])

class TagForm(FlaskForm):
    """标签表单"""
    class Meta:
        csrf = False  # 禁用 CSRF 保护
        
    name = StringField('名称', validators=[DataRequired(), Length(1, 64)])
    slug = StringField('别名', validators=[DataRequired(), Length(1, 64)])
    description = TextAreaField('描述', validators=[Optional(), Length(0, 200)])

class ProfileForm(FlaskForm):
    """个人资料表单"""
    class Meta:
        csrf = False  # 禁用 CSRF 保护
        
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    email = StringField('邮箱', validators=[DataRequired(), Email(), Length(1, 120)])
    password = PasswordField('新密码', validators=[Optional(), Length(6, 128)])
    password_confirm = PasswordField('确认密码', validators=[
        Optional(),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    nickname = StringField('昵称', validators=[Optional(), Length(0, 64)])
    avatar = StringField('头像', validators=[Optional(), URL(), Length(0, 200)])
    bio = TextAreaField('个人简介', validators=[Optional(), Length(0, 500)])

class LoginForm(FlaskForm):
    """管理员登录表单"""
    class Meta:
        csrf = False  # 禁用 CSRF 保护
        
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired(), Length(6, 128)])
    remember_me = BooleanField('记住我') 