"""
文件名：category_form.py
描述：分类表单类
作者：denny
创建日期：2024-03-21
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length, Optional

class CategoryForm(FlaskForm):
    """分类表单"""
    csrf_token = HiddenField()
    name = StringField('名称', validators=[DataRequired(), Length(min=1, max=50)])
    slug = StringField('别名', validators=[Optional(), Length(min=1, max=50)])
    description = TextAreaField('描述', validators=[Length(max=200)]) 