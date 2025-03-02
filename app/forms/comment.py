"""
文件名：comment.py
描述：评论表单
作者：denny
创建日期：2024-03-21
"""

from wtforms import StringField, TextAreaField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Optional
from . import BaseForm

class CommentForm(BaseForm):
    """评论表单"""
    content = TextAreaField('评论内容', validators=[
        DataRequired(message='请输入评论内容'),
        Length(min=1, max=1000, message='评论内容长度必须在1-1000个字符之间')
    ])
    author = StringField('昵称', validators=[
        DataRequired(message='请输入昵称'),
        Length(min=1, max=50, message='昵称长度必须在1-50个字符之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(message='请输入邮箱'),
        Email(message='请输入有效的邮箱地址'),
        Length(max=100, message='邮箱长度不能超过100个字符')
    ])
    website = StringField('网站', validators=[
        Optional(),
        Length(max=200, message='网站地址长度不能超过200个字符')
    ])
    parent_id = HiddenField('父评论ID')
    post_id = HiddenField('文章ID', validators=[
        DataRequired(message='文章ID不能为空')
    ])
    submit = SubmitField('提交评论') 