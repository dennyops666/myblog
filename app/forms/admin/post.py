"""
文件名：post.py
描述：文章表单
作者：denny
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models.post import PostStatus
from app.forms import BaseForm
from app.extensions import db

# 安全地将值转换为整数，如果失败则返回None
def safe_int_coerce(value):
    if not value:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        # 不抛出验证错误，而是返回None
        return None 

class PostForm(BaseForm):
    """文章表单"""
    title = StringField('标题', validators=[DataRequired(), Length(1, 255)])
    content = TextAreaField('内容', validators=[DataRequired(message='文章内容不能为空')])
    summary = TextAreaField('摘要', validators=[Optional(), 
                                              Length(0, 500, message='摘要长度必须在0到500个字符之间')])
    category_id = SelectField('分类', coerce=int, validators=[Optional()])
    status = SelectField('状态', choices=[
        (PostStatus.DRAFT.name, '草稿'),
        (PostStatus.PUBLISHED.name, '已发布'),
        (PostStatus.ARCHIVED.name, '已归档')
    ], validators=[DataRequired()])
    tags = SelectMultipleField('标签', coerce=safe_int_coerce)
    is_sticky = BooleanField('置顶')
    is_private = BooleanField('私密')
    can_comment = BooleanField('允许评论', default=True)
    submit = SubmitField('保存')
    
    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        from app.models.category import Category
        from app.models.tag import Tag
        
        # 动态加载分类选项
        categories = Category.query.order_by(Category.name).all()
        self.category_id.choices = [(0, '-- 无分类 --')] + [(c.id, c.name) for c in categories]
        
        # 动态加载标签选项
        tags = Tag.query.order_by(Tag.name).all()
        self.tags.choices = [(t.id, t.name) for t in tags]

    def process_tags(self):
        """处理标签数据"""
        from app.models.tag import Tag
        
        tag_ids = self.tags.data
        if not tag_ids:
            return []
            
        # 过滤掉None值
        tag_ids = [tag_id for tag_id in tag_ids if tag_id is not None]
        if not tag_ids:
            return []
        
        # 查询所有标签对象
        tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
        
        # 验证是否所有标签都存在
        found_ids = {tag.id for tag in tags}
        missing_ids = set(tag_ids) - found_ids
        if missing_ids:
            raise ValueError(f"标签ID {', '.join(map(str, missing_ids))} 不存在")
        
        # 确保所有标签都在当前会话中
        for tag in tags:
            db.session.add(tag)
            db.session.refresh(tag)
        db.session.flush()
            
        return tags
        
    def get_status(self):
        """获取状态枚举值"""
        status_map = {
            'DRAFT': PostStatus.DRAFT,
            'PUBLISHED': PostStatus.PUBLISHED,
            'ARCHIVED': PostStatus.ARCHIVED
        }
        return status_map.get(self.status.data, PostStatus.DRAFT)
        
    def validate_status(self, field):
        """验证状态值"""
        valid_statuses = ['DRAFT', 'PUBLISHED', 'ARCHIVED']
        if field.data not in valid_statuses:
            raise ValidationError('无效的状态值')
            
    def validate_title(self, field):
        """验证标题唯一性"""
        from app.models.post import Post
        from flask import request
        
        # 获取当前正在编辑的文章ID
        post_id = None
        if request.view_args and 'post_id' in request.view_args:
            post_id = request.view_args['post_id']
        
        # 检查标题是否已存在（不包括当前文章）
        query = Post.query.filter(Post.title == field.data)
        
        if post_id:
            # 编辑模式，排除当前文章
            query = query.filter(Post.id != post_id)
        
        # 检查是否存在同名文章
        existing_post = query.first()
        if existing_post:
            raise ValidationError('该标题已存在，请使用其他标题') 