class CommentForm(FlaskForm):
    """评论表单"""
    content = TextAreaField('评论内容', validators=[
        DataRequired(message='请输入评论内容'),
        Length(min=2, max=1000, message='评论内容长度必须在2-1000个字符之间')
    ])
    submit = SubmitField('提交评论') 