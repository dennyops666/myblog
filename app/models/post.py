"""
文件名：post.py
描述：文章数据模型
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, UTC
from app.extensions import db
import json
from enum import Enum
import markdown2
import re
from bs4 import BeautifulSoup
from flask import current_app
from app.models.comment import Comment, CommentStatus
from sqlalchemy import func
from app.models.associations import post_tags
import traceback

class PostStatus(Enum):
    """文章状态枚举"""
    DRAFT = 'DRAFT'  # 草稿
    PUBLISHED = 'PUBLISHED'  # 已发布
    ARCHIVED = 'ARCHIVED'  # 已归档

class Post(db.Model):
    """文章模型"""
    __tablename__ = 'posts'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    html_content = db.Column(db.Text)
    _toc = db.Column('toc', db.Text, default='[]')
    highlight_css = db.Column(db.Text)  # 存储代码高亮样式
    summary = db.Column(db.String(500))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.Enum(PostStatus), default=PostStatus.DRAFT)
    is_sticky = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    _comments_count = db.Column('comments_count', db.Integer, default=0)  # 添加评论数字段
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC),
                          onupdate=lambda: datetime.now(UTC))
    is_private = db.Column(db.Boolean, default=False)
    published = db.Column(db.Boolean, default=True)
    can_comment = db.Column(db.Boolean, default=True)
    
    # 关系
    category = db.relationship('Category', back_populates='posts')
    comments = db.relationship('Comment', back_populates='post', lazy='dynamic',
                             cascade='all, delete-orphan')
    tags = db.relationship(
        'Tag',
        secondary=post_tags,
        back_populates='posts',
        lazy='joined',
        cascade='all, delete',
        passive_deletes=True
    )
    
    @property
    def total_comments_count(self):
        """获取文章的总评论数量"""
        return self.comments.count()
    
    @property
    def approved_comments_count(self):
        """获取已审核的评论数量"""
        return Comment.query.filter_by(
            post_id=self.id,
            status=CommentStatus.APPROVED
        ).count()
    
    def update_comments_count(self):
        """更新文章的评论数量"""
        self._comments_count = self.total_comments_count
    
    def __init__(self, **kwargs):
        """初始化文章对象
        
        Args:
            **kwargs: 关键字参数，包括文章的各个属性
        """
        super(Post, self).__init__(**kwargs)
        
        # 初始化计数器
        if self.view_count is None:
            self.view_count = 0
        if self._comments_count is None:
            self._comments_count = 0
        
        # 初始化布尔值
        if self.is_private is None:
            self.is_private = False
        if self.published is None:
            self.published = True
        if self.can_comment is None:
            self.can_comment = True
        if self.is_sticky is None:
            self.is_sticky = False
        
        # 渲染内容
        if self.content:
            try:
                # 检测内容是否为Markdown格式，如果不是，则进行基本格式化
                if not self._is_markdown_content(self.content):
                    formatted_content = self._format_plain_text(self.content)
                    self.html_content = formatted_content
                else:
                    from app.utils.markdown import markdown_to_html
                    self.html_content = markdown_to_html(self.content)
                self._toc = '[]'
            except Exception as e:
                current_app.logger.error(f"初始化文章时渲染内容失败: {str(e)}")
                self.html_content = f"<p>{str(self.content)}</p>"
                self._toc = '[]'
    
    def _is_markdown_content(self, text):
        """判断文本是否为Markdown格式
        
        检查文本是否包含常见的Markdown标记，如标题、列表、链接、图片等
        
        Args:
            text: 要检查的文本内容
            
        Returns:
            bool: 是否为Markdown格式
        """
        # 检查常见的Markdown标记
        markdown_patterns = [
            r'^#+\s',                # 标题
            r'^\s*[-*+]\s',          # 无序列表
            r'^\s*\d+\.\s',          # 有序列表
            r'\[.+?\]\(.+?\)',       # 链接
            r'!\[.+?\]\(.+?\)',      # 图片
            r'`{1,3}[\s\S]*?`{1,3}', # 代码块或行内代码
            r'^\s*>\s',              # 引用
            r'\*\*.*?\*\*',          # 粗体
            r'__.*?__',              # 另一种粗体
            r'\*.*?\*',              # 斜体
            r'^---+\s*$',            # 分隔线
            r'\|.*?\|.*?\|'          # 表格
        ]
        
        # 如果匹配到任何一种Markdown格式，返回True
        for pattern in markdown_patterns:
            if re.search(pattern, text, re.MULTILINE):
                return True
        
        return False

    def _format_plain_text(self, text):
        """对普通文本进行基本格式化处理
        
        将普通文本转换为基本的HTML格式，支持段落、换行和URL链接
        
        Args:
            text: 要格式化的文本内容
            
        Returns:
            str: 格式化后的HTML内容
        """
        # 处理特殊字符
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # 将URL转换为可点击的链接
        url_pattern = r'(https?://[^\s]+)'
        text = re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', text)
        
        # 处理段落和换行
        paragraphs = text.split('\n\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            if para.strip():
                # 处理段落内的换行
                para = para.replace('\n', '<br>')
                formatted_paragraphs.append(f'<p>{para}</p>')
        
        return '\n'.join(formatted_paragraphs)

    def update_html_content(self):
        """更新文章 HTML 内容，自动提交事务"""
        if not self.content:
            self.html_content = ''
            self._toc = '[]'
            current_app.logger.warning(f"文章 {self.id} 内容为空，设置HTML内容为空")
            try:
                db.session.add(self)
                db.session.commit()
                current_app.logger.info(f"空内容文章 {self.id} 提交成功")
            except Exception as e:
                current_app.logger.error(f"提交空内容文章 {self.id} 失败: {str(e)}")
                db.session.rollback()
            return
        
        try:
            current_app.logger.info(f"开始更新文章 {self.id} 的HTML内容...")
            current_app.logger.info(f"内容长度: {len(self.content)}")
            
            # 保存原始内容，用于日志对比
            old_content = self.html_content
            
            # 检测内容是否为Markdown格式
            if not self._is_markdown_content(self.content):
                self.html_content = self._format_plain_text(self.content)
                current_app.logger.info(f"使用普通文本格式化方法")
            else:
                from app.utils.markdown import markdown_to_html
                self.html_content = markdown_to_html(self.content)
                current_app.logger.info(f"使用Markdown格式化方法")
            
            # 提取目录
            try:
                soup = BeautifulSoup(self.html_content, 'html.parser')
                headings = []
                
                # 查找所有标题标签
                for level in range(1, 7):
                    for h in soup.find_all(f'h{level}'):
                        headings.append({
                            'id': h.get('id', ''),
                            'text': h.get_text(),
                            'level': level
                        })
                
                self._toc = json.dumps(headings)
            except Exception as e:
                current_app.logger.error(f"提取文章目录失败: {str(e)}")
                self._toc = '[]'
            
            # 设置更新时间
            self.updated_at = datetime.now(UTC)
            
            # 检查HTML内容是否生成成功
            if not self.html_content and self.content:
                current_app.logger.error(f"HTML内容生成失败，内容为空但原始内容不为空")
                # 应急方法
                self.html_content = f"<p>{self.content}</p>"
            
            # 记录更新结果
            if old_content != self.html_content:
                current_app.logger.info(f"文章 {self.id} HTML内容已更新，内容长度: {len(self.html_content or '')}")
                current_app.logger.info(f"HTML内容哈希值: {hash(self.html_content or '')}")
            else:
                current_app.logger.warning(f"文章 {self.id} HTML内容未变")
            
            # 显式添加和提交更改
            try:
                db.session.add(self)
                db.session.commit()
                current_app.logger.info(f"文章 {self.id} HTML内容更新并提交成功")
            except Exception as e:
                current_app.logger.error(f"提交文章 {self.id} HTML内容更新失败: {str(e)}")
                current_app.logger.error(traceback.format_exc())
                db.session.rollback()
            
        except Exception as e:
            current_app.logger.error(f"更新文章 HTML 内容失败: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            # 如果转换失败，直接使用纯文本作为内容
            self.html_content = f"<p>{self.content}</p>"
            self._toc = '[]'
            
            # 尝试保存错误后的应急内容
            try:
                db.session.add(self)
                db.session.commit()
                current_app.logger.info(f"文章 {self.id} 应急HTML内容保存成功")
            except Exception as save_err:
                current_app.logger.error(f"保存应急内容失败: {str(save_err)}")
                db.session.rollback()
    
    def update_counts(self):
        """更新文章的各种计数"""
        try:
            # 更新评论数量
            self._comments_count = self.total_comments_count
            
            # 更新时间戳
            self.updated_at = datetime.now(UTC)
            
            # 保存更改
            db.session.add(self)
            db.session.commit()
            
            current_app.logger.info(f"文章计数更新成功", extra={
                'post_id': self.id,
                'comments_count': self._comments_count,
                'view_count': self.view_count
            })
        except Exception as e:
            current_app.logger.error(f"更新文章计数时发生错误: {str(e)}")
            db.session.rollback()
    
    @property
    def toc(self):
        """获取目录结构"""
        try:
            return json.loads(self._toc or '[]')
        except Exception as e:
            current_app.logger.error(f"解析目录结构失败: {str(e)}")
            return []
    
    @toc.setter
    def toc(self, value):
        """设置目录结构"""
        try:
            self._toc = json.dumps(value or [])
        except Exception as e:
            current_app.logger.error(f"设置目录结构失败: {str(e)}")
            self._toc = '[]'
    
    @property
    def is_published(self):
        """检查文章是否已发布"""
        if self.status == PostStatus.PUBLISHED:
            # 确保published字段与status保持一致
            if not self.published:
                self.published = True
            return True
        else:
            # 确保published字段与status保持一致
            if self.published:
                self.published = False
            return False

    @property
    def is_archived(self):
        """检查文章是否已归档"""
        return self.status == PostStatus.ARCHIVED
    
    def update_status_consistency(self):
        """更新status和published字段的一致性"""
        if self.status == PostStatus.PUBLISHED and not self.published:
            self.published = True
        elif self.status != PostStatus.PUBLISHED and self.published:
            self.published = False
        return self
    
    def __repr__(self):
        """打印友好的对象表示"""
        return f'<Post {self.id}: {self.title}>'
        
    @staticmethod
    def render_markdown(content):
        """将Markdown内容渲染为HTML
        
        Args:
            content: Markdown格式的内容
            
        Returns:
            str: 渲染后的HTML内容
        """
        try:
            if not content:
                return ''
                
            from app.utils.markdown import markdown_to_html
            return markdown_to_html(content)
        except Exception as e:
            current_app.logger.error(f"渲染Markdown内容失败: {str(e)}")
            current_app.logger.exception(e)
            return f'<p>渲染失败: {str(e)}</p>' 