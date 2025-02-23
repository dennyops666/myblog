"""
文件名：post_form.py
描述：文章表单类
作者：denny
创建日期：2024-03-21
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, HiddenField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Optional
from app.models.post import PostStatus
from app.models.category import Category
from app.models.tag import Tag

class PostForm(FlaskForm):
    """文章表单"""
    csrf_token = HiddenField()
    title = StringField('标题', validators=[
        DataRequired(message='标题不能为空'),
        Length(min=1, max=200, message='标题长度必须在1-200个字符之间')
    ])
    content = TextAreaField('内容', validators=[
        DataRequired(message='内容不能为空')
    ])
    summary = TextAreaField('摘要', validators=[
        Length(max=500, message='摘要长度不能超过500个字符')
    ])
    category_id = IntegerField('分类', validators=[
        DataRequired(message='请选择分类')
    ])
    tags = SelectMultipleField('标签', coerce=int)
    status = SelectField('状态', choices=[
        (str(PostStatus.DRAFT.value), '草稿'),
        (str(PostStatus.PUBLISHED.value), '发布')
    ], validators=[DataRequired(message='请选择状态')])

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
        self.tags.choices = [(t.id, t.name) for t in Tag.query.order_by(Tag.name).all()] 