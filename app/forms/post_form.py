"""
文件名：post_form.py
描述：文章表单
作者：denny
创建日期：2024-03-21
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models.post import Post, PostStatus
from app.models.category import Category
from app.models.tag import Tag
from flask import current_app
from app.extensions import db

class PostForm(FlaskForm):
    """文章表单类"""
    title = StringField('标题', validators=[
        DataRequired(message='标题不能为空'),
        Length(min=2, max=100, message='标题长度必须在2-100个字符之间')
    ])
    
    content = TextAreaField('内容', validators=[
        DataRequired(message='内容不能为空')
    ])
    
    summary = TextAreaField('摘要')
    
    category_id = SelectField('分类', 
        validators=[DataRequired(message='请选择分类')],
        coerce=int
    )
    
    tags = SelectMultipleField('标签',
        coerce=str,  # 使用字符串类型，因为前端传递的是字符串
        choices=[],   # 选项将在初始化时设置
        render_kw={
            'class': 'form-control select2',
            'multiple': 'multiple',
            'data-placeholder': '选择标签'
        }
    )
    
    status = SelectField('状态',
        validators=[DataRequired(message='请选择状态')],
        choices=[(status.value, status.value) for status in PostStatus],
        default=PostStatus.DRAFT.value
    )
    
    def __init__(self, *args, **kwargs):
        """初始化表单"""
        self.edit_post = kwargs.pop('obj', None)  # 保存正在编辑的文章对象
        super(PostForm, self).__init__(*args, **kwargs)
        
        # 设置自定义错误处理，禁用字段标签前缀
        for field in self._fields.values():
            field.render_kw = field.render_kw or {}
            field.render_kw['data-error-prefix'] = 'false'
        
        # 设置状态选项
        self.status.choices = [
            (status.value, {'DRAFT': '草稿', 'PUBLISHED': '已发布', 'ARCHIVED': '已归档'}[status.value])
            for status in PostStatus
        ]
        
        # 加载所有分类
        try:
            current_app.logger.info("开始加载分类选项...")
            categories = Category.query.order_by(Category.name).all()
            current_app.logger.info(f"成功获取到 {len(categories)} 个分类")
            
            # 设置分类选项
            self.category_id.choices = [(c.id, c.name) for c in categories]
            
            # 只在非POST请求（即GET请求）时设置默认分类
            if not args or not args[0]:  # 如果没有表单数据（非POST请求）
                if self.edit_post and self.edit_post.category_id:
                    self.category_id.data = self.edit_post.category_id
                    current_app.logger.debug(f"设置默认分类ID: {self.edit_post.category_id}")
                
        except Exception as e:
            current_app.logger.error(f"加载分类失败: {str(e)}")
            current_app.logger.exception(e)
            self.category_id.choices = []

        # 加载所有标签
        try:
            current_app.logger.info("开始加载标签选项...")
            # 获取现有标签
            tags = Tag.query.order_by(Tag.name).all()
            self.available_tags = [(str(t.id), t.name) for t in tags]
            # 设置标签选项
            self.tags.choices = self.available_tags
            current_app.logger.info(f"成功获取到 {len(self.available_tags)} 个标签")
            
            # 如果是编辑模式，设置默认标签
            if self.edit_post and not args:
                current_tags = [(str(tag.id), tag.name) for tag in self.edit_post.tags]
                # 合并现有标签和文章标签，确保不重复
                self.available_tags = list(set(self.available_tags) | set(current_tags))
                # 设置默认选中的标签
                self.tags.data = [str(tag.id) for tag in self.edit_post.tags]
                current_app.logger.debug(f"设置默认标签: {self.tags.data}")
                
        except Exception as e:
            current_app.logger.error(f"加载标签失败: {str(e)}")
            current_app.logger.exception(e)
            self.available_tags = []
            self.tags.choices = []

    def validate_title(self, field):
        """验证标题唯一性"""
        try:
            # 检查标题是否已存在
            post = Post.query.filter(Post.title == field.data).first()
            if post:
                # 如果是编辑模式，且标题未改变，则跳过验证
                if self.edit_post and self.edit_post.id == post.id:
                    return
                raise ValidationError('文章标题已存在，请使用其他标题')
        except Exception as e:
            current_app.logger.error(f"验证文章标题时发生错误: {str(e)}")
            raise ValidationError('系统在验证文章标题时遇到问题，请刷新页面重试')

    def process_tags(self):
        """处理标签数据，返回标签对象列表"""
        try:
            if not self.tags.data:
                current_app.logger.info("没有选择标签")
                return []
            
            # 记录接收到的标签数据
            current_app.logger.info(f"接收到的标签数据: {self.tags.data}")
            
            # 将标签ID转换为整数
            tag_ids = [int(tag_id) for tag_id in self.tags.data]
            current_app.logger.info(f"处理后的标签ID列表: {tag_ids}")
            
            # 获取标签对象
            tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
            current_app.logger.info(f"找到的标签对象: {[tag.name for tag in tags]}")
            
            return tags
            
        except Exception as e:
            current_app.logger.error(f"处理标签数据时发生错误: {str(e)}")
            current_app.logger.exception(e)
            return [] 