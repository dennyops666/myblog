"""
文件名：tag_form.py
描述：标签表单
作者：denny
创建日期：2024-03-21
"""

from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Regexp, ValidationError
from . import BaseForm
from app.models import Tag

class TagForm(BaseForm):
    """标签表单"""
    name = StringField('名称', validators=[
        DataRequired(message='请输入标签名称'),
        Length(min=1, max=50, message='标签名称长度必须在1-50个字符之间')
    ])
    slug = StringField('别名', validators=[
        Optional(),
        Length(max=50, message='别名长度不能超过50个字符'),
        Regexp(r'^[a-z0-9-]+$', message='别名只能包含小写字母、数字和连字符')
    ])
    description = TextAreaField('描述', validators=[
        Optional(),
        Length(max=200, message='描述长度不能超过200个字符')
    ])
    submit = SubmitField('保存')
    
    def validate_name(self, field):
        # 检查标签名称是否已存在
        tag = Tag.query.filter(Tag.name == field.data).first()
        if tag and (not hasattr(self, 'tag_id') or tag.id != self.tag_id):
            raise ValidationError('标签名称已存在')
    
    def validate_slug(self, field):
        # 如果提供了别名，检查是否已存在
        if field.data:
            tag = Tag.query.filter(Tag.slug == field.data).first()
            if tag and (not hasattr(self, 'tag_id') or tag.id != self.tag_id):
                raise ValidationError('别名已存在') 