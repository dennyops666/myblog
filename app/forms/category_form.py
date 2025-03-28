"""
文件名：category_form.py
描述：分类表单
作者：denny
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from app.forms import BaseForm

class CategoryForm(BaseForm):
    """分类表单"""
    name = StringField('分类名称', validators=[DataRequired(), Length(1, 64)])
    slug = StringField('别名', validators=[Optional(), Length(0, 64)])
    description = TextAreaField('描述', validators=[Optional(), Length(0, 256)])
    submit = SubmitField('保存')
    
    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs) 