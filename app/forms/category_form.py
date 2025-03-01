"""
文件名：category_form.py
描述：分类表单类
作者：denny
创建日期：2024-03-21
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

class CategoryForm(FlaskForm):
    """分类表单"""
    class Meta:
        csrf = False  # 禁用 CSRF 保护
        
    name = StringField('名称', validators=[
        DataRequired(message='名称不能为空'),
        Length(min=1, max=50, message='名称长度必须在1-50个字符之间')
    ])
    
    # 修改别名字段的验证规则，允许为空或空字符串
    slug = StringField('别名', validators=[
        Optional(),  # 允许为空
        Length(max=50, message='别名长度不能超过50个字符')
    ])
    
    description = TextAreaField('描述', validators=[
        Optional(),  # 允许为空
        Length(max=200, message='描述长度不能超过200个字符')
    ])
    
    def validate_name(self, field):
        """验证名称是否包含特殊字符"""
        import re
        if re.search(r'[<>"\'/]', field.data):
            raise ValidationError('名称不能包含特殊字符')
            
    def validate_slug(self, field):
        """验证别名格式"""
        # 如果字段为空或只包含空白字符，直接返回True
        if not field.data or not field.data.strip():
            return True
            
        # 验证别名格式
        import re
        if not re.match(r'^[a-z0-9-]+$', field.data):
            raise ValidationError('别名只能包含小写字母、数字和连字符')
        return True 