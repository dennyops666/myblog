"""
文件名：tag_form.py
描述：标签表单类
作者：denny
创建日期：2024-03-21
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length

class TagForm(FlaskForm):
    """标签表单"""
    class Meta:
        csrf = False  # 禁用 CSRF 保护
        
    name = StringField('名称', validators=[DataRequired(), Length(min=1, max=50)])
    slug = StringField('别名', validators=[DataRequired(), Length(min=1, max=50)])
    description = TextAreaField('描述', validators=[Length(max=200)]) 