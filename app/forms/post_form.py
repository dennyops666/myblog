"""
文件名：post_form.py
描述：文章表单类
作者：denny
创建日期：2024-03-21
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, HiddenField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models.post import PostStatus, Post
from app.models.category import Category
from app.models.tag import Tag
from app.extensions import db
from flask import current_app

class PostForm(FlaskForm):
    """文章表单"""
    class Meta:
        csrf = False  # 禁用 CSRF 保护
        # 禁用在错误消息前添加字段标签
        strip_string_fields = True
        render_kw = {'strip': True}

    csrf_token = HiddenField()
    title = StringField('标题', validators=[
        DataRequired(message='文章标题不能为空'),
        Length(min=1, max=200, message='文章标题长度必须在1-200个字符之间')
    ])
    content = TextAreaField('内容', validators=[
        DataRequired(message='内容不能为空')
    ])
    summary = TextAreaField('摘要', validators=[
        Length(max=500, message='摘要长度不能超过500个字符')
    ])
    category_id = SelectField('分类', validators=[
        DataRequired(message='请选择分类')
    ], coerce=int, validate_choice=False)
    tags = SelectMultipleField('标签', coerce=int, validate_choice=False)
    status = SelectField('状态', choices=[
        (str(PostStatus.DRAFT.value), '草稿'),
        (str(PostStatus.PUBLISHED.value), '发布')
    ], validators=[DataRequired(message='请选择状态')])

    def __init__(self, *args, **kwargs):
        """初始化表单"""
        super(PostForm, self).__init__(*args, **kwargs)
        
        # 设置自定义错误处理，禁用字段标签前缀
        for field in self._fields.values():
            field.render_kw = field.render_kw or {}
            field.render_kw['data-error-prefix'] = 'false'
        
        # 加载所有分类
        try:
            current_app.logger.info("开始加载分类选项...")
            categories = Category.query.order_by(Category.name).all()
            current_app.logger.info(f"成功获取到 {len(categories)} 个分类")
            
            # 设置分类选项
            self.category_id.choices = [(c.id, c.name) for c in categories]
            
            # 只在非POST请求（即GET请求）时设置默认分类
            if not args or not args[0]:  # 如果没有表单数据（非POST请求）
                if 'obj' in kwargs and kwargs['obj'] and hasattr(kwargs['obj'], 'category_id'):
                    if kwargs['obj'].category_id:
                        self.category_id.data = kwargs['obj'].category_id
                        current_app.logger.debug(f"设置默认分类ID: {kwargs['obj'].category_id}")
                
        except Exception as e:
            current_app.logger.error(f"加载分类失败: {str(e)}")
            current_app.logger.exception(e)
            self.category_id.choices = []
            
        # 加载所有标签
        try:
            # 获取现有标签
            tags = Tag.query.order_by(Tag.name).all()
            self.tags.choices = [(t.id, t.name) for t in tags]
            
            # 如果是编辑模式，添加文章当前的标签
            if 'obj' in kwargs and kwargs['obj']:
                post = kwargs['obj']
                # 确保所有当前标签都在选项中
                current_tags = {(tag.id, tag.name) for tag in post.tags}
                self.tags.choices = list(set(self.tags.choices) | current_tags)
                
                # 只在非POST请求时设置默认标签
                if not args or not args[0]:
                    self.tags.data = [tag.id for tag in post.tags]
                    
        except Exception as e:
            current_app.logger.error(f"加载标签失败: {str(e)}")
            current_app.logger.exception(e)
            self.tags.choices = []

    def validate_title(self, field):
        """验证标题唯一性"""
        try:
            # 检查标题是否已存在
            post = Post.query.filter(Post.title == field.data).first()
            if post:
                # 如果是编辑模式，且标题未改变，则跳过验证
                if hasattr(self, 'obj') and self.obj and self.obj.id == post.id:
                    return
                raise ValidationError('文章标题已存在，请使用其他标题')
        except Exception as e:
            current_app.logger.error(f"验证文章标题时发生错误: {str(e)}")
            raise ValidationError('系统在验证文章标题时遇到问题，请刷新页面重试') 