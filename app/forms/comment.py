"""
文件名：comment.py
描述：评论表单
作者：denny
创建日期：2025-02-16
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length

class CommentForm(FlaskForm):
    """评论表单"""
    author_name = StringField('昵称', validators=[
        DataRequired(message='请输入昵称'),
        Length(min=2, max=20, message='昵称长度必须在2-20个字符之间')
    ])
    
    author_email = StringField('邮箱', validators=[
        DataRequired(message='请输入邮箱'),
        Email(message='请输入有效的邮箱地址'),
        Length(max=50, message='邮箱长度不能超过50个字符')
    ])
    
    content = TextAreaField('评论内容', validators=[
        DataRequired(message='请输入评论内容'),
        Length(min=2, max=500, message='评论内容长度必须在2-500个字符之间')
    ]) 