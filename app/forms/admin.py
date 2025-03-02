"""
文件名：admin.py
描述：管理后台表单
作者：denny
创建日期：2024-03-21
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, PasswordField, SelectMultipleField, FileField
from wtforms.validators import DataRequired, Length, Email, Optional, URL, EqualTo
from app.models.post import PostStatus
from app.forms import BaseForm

class PostForm(BaseForm):
    """文章表单"""
    title = StringField('标题', validators=[DataRequired(), Length(min=1, max=200)])
    content = TextAreaField('内容', validators=[DataRequired()])
    summary = TextAreaField('摘要', validators=[Optional(), Length(max=500)])
    category_id = SelectField('分类', coerce=int, validators=[Optional()])
    tag_ids = SelectMultipleField('标签', coerce=int, validators=[Optional()])
    status = SelectField('状态', choices=[('DRAFT', '草稿'), ('PUBLISHED', '发布')])

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        from app.models import Category, Tag
        self.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
        self.tag_ids.choices = [(t.id, t.name) for t in Tag.query.all()]

class CategoryForm(BaseForm):
    """分类表单"""
    name = StringField('名称', validators=[DataRequired(), Length(min=1, max=50)])
    slug = StringField('别名', validators=[DataRequired(), Length(min=1, max=50)])
    description = TextAreaField('描述', validators=[Optional(), Length(max=200)])

class TagForm(BaseForm):
    """标签表单"""
    name = StringField('名称', validators=[DataRequired(), Length(min=1, max=50)])
    slug = StringField('别名', validators=[DataRequired(), Length(min=1, max=50)])
    description = TextAreaField('描述', validators=[Optional(), Length(max=200)])

class ProfileForm(BaseForm):
    """个人资料表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Length(max=120)])
    nickname = StringField('昵称', validators=[Optional(), Length(max=20)])
    bio = TextAreaField('个人简介', validators=[Optional(), Length(max=500)])

class LoginForm(BaseForm):
    """管理员登录表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired(), Length(6, 128)])
    remember_me = BooleanField('记住我') 