from flask_wtf import FlaskForm
from wtforms import StringField, ValidationError
from wtforms.validators import DataRequired, Length, Optional, Regexp
from app.models import Tag

class TagForm(FlaskForm):
    name = StringField('名称', validators=[
        DataRequired(message='标签名称不能为空'),
        Length(min=1, max=50, message='标签名称长度必须在1-50个字符之间')
    ])
    
    slug = StringField('别名', validators=[
        Optional(),
        Length(max=50, message='别名长度不能超过50个字符'),
        Regexp(r'^[a-z0-9\-]+$', message='别名只能包含小写字母、数字和连字符')
    ])
    
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

class TagCreateForm(TagForm):
    pass

class TagEditForm(TagForm):
    def __init__(self, tag_id, *args, **kwargs):
        super(TagEditForm, self).__init__(*args, **kwargs)
        self.tag_id = tag_id 