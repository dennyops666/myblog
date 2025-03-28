"""
文件名：settings.py
描述：系统设置表单
作者：denny
"""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class SettingsForm(FlaskForm):
    """系统设置表单"""
    blog_name = StringField('博客名称', validators=[DataRequired(), Length(max=100)])
    blog_description = TextAreaField('博客描述', validators=[Optional(), Length(max=500)])
    posts_per_page = IntegerField('每页文章数', validators=[DataRequired(), NumberRange(min=1, max=50)])
    allow_registration = BooleanField('允许注册')
    allow_comments = BooleanField('允许评论')
    submit = SubmitField('保存')
    
    class Meta:
        csrf = False 