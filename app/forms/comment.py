"""
文件名：comment.py
描述：评论表单
作者：denny
创建日期：2024-03-21
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length, Email, Optional

class CommentForm(FlaskForm):
    """评论表单"""
    class Meta:
        csrf = False  # 禁用 CSRF 保护
        
    content = TextAreaField('评论内容', validators=[DataRequired(), Length(1, 1000)])
    author_name = StringField('昵称', validators=[DataRequired(), Length(1, 64)])
    author_email = StringField('邮箱', validators=[DataRequired(), Email(), Length(1, 120)])
    author_website = StringField('网站', validators=[Optional(), Length(0, 200)])
    parent_id = HiddenField('父评论ID', validators=[Optional()]) 