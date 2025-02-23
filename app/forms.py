from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email

class CommentForm(FlaskForm):
    """评论表单"""
    nickname = StringField('昵称', validators=[
        DataRequired(message='请输入昵称'),
        Length(min=2, max=20, message='昵称长度必须在2-20个字符之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(message='请输入邮箱'),
        Email(message='请输入有效的邮箱地址')
    ])
    content = TextAreaField('评论内容', validators=[
        DataRequired(message='请输入评论内容'),
        Length(min=2, max=1000, message='评论内容长度必须在2-1000个字符之间')
    ])
    submit = SubmitField('提交评论') 