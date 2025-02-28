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

# 文章标签关联表
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
    extend_existing=True
)

class PostStatus(Enum):
    """文章状态枚举"""
    DRAFT = 'draft'  # 草稿
    PUBLISHED = 'published'  # 已发布
    ARCHIVED = 'archived'  # 已归档

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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC),
                          onupdate=lambda: datetime.now(UTC))
    is_private = db.Column(db.Boolean, default=False)
    published = db.Column(db.Boolean, default=True)
    
    # 关系
    category = db.relationship('Category', back_populates='posts')
    comments = db.relationship('Comment', back_populates='post', lazy='dynamic',
                             cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary=post_tags, back_populates='posts',
                          lazy='joined')
    
    @property
    def comment_count(self):
        """获取文章的评论数量"""
        return self.comments.count()
    
    def __init__(self, **kwargs):
        """初始化文章对象
        
        Args:
            **kwargs: 关键字参数，包括文章的各个属性
        """
        super(Post, self).__init__(**kwargs)
        if self.view_count is None:
            self.view_count = 0
        if self.is_private is None:
            self.is_private = False
        if self.content:
            try:
                extras = {
                    'fenced-code-blocks': None,
                    'tables': None,
                    'header-ids': None,
                    'toc': None,
                    'footnotes': None,
                    'metadata': None,
                    'code-friendly': None
                }
                self.html_content = markdown2.markdown(str(self.content), extras=extras)
                self._toc = '[]'
            except Exception as e:
                current_app.logger.error(f"初始化文章时渲染 Markdown 内容失败: {str(e)}")
                self.html_content = str(self.content)
                self._toc = '[]'
    
    @staticmethod
    def render_markdown(content):
        """将 Markdown 内容渲染为 HTML
        
        Args:
            content: Markdown 格式的内容
            
        Returns:
            str: 渲染后的 HTML 内容
        """
        if not content:
            return ''
            
        try:
            extras = {
                'fenced-code-blocks': None,
                'tables': None,
                'header-ids': None,
                'toc': None,
                'footnotes': None,
                'metadata': None,
                'code-friendly': None,
                'break-on-newline': True
            }
            html = markdown2.markdown(str(content), extras=extras)
            return html if html else ''
        except Exception as e:
            current_app.logger.error(f"渲染 Markdown 内容失败: {str(e)}")
            return str(content)

    def update_html_content(self):
        """更新文章的 HTML 内容"""
        if not self.content:
            self.html_content = ''
            self.summary = ''
            return
        
        try:
            # 渲染 Markdown 内容
            self.html_content = self.render_markdown(self.content)
            
            # 生成摘要
            if not self.summary:
                soup = BeautifulSoup(self.html_content, 'html.parser')
                text = soup.get_text()
                text = re.sub(r'\s+', ' ', text).strip()
                self.summary = text[:200] + '...' if len(text) > 200 else text
            
            # 生成目录结构
            soup = BeautifulSoup(self.html_content, 'html.parser')
            toc = []
            for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                level = int(header.name[1])
                text = header.get_text()
                header_id = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
                header['id'] = header_id
                toc.append({
                    'level': level,
                    'text': text,
                    'id': header_id
                })
            self._toc = json.dumps(toc)
            
        except Exception as e:
            current_app.logger.error(f"更新文章 HTML 内容时发生错误: {str(e)}")
            self.html_content = str(self.content)
            if not self.summary:
                self.summary = str(self.content)[:200] + '...' if len(str(self.content)) > 200 else str(self.content)
            self._toc = '[]'
    
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
    
    def __repr__(self):
        return f'<Post {self.title}>' 