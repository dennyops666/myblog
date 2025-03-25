"""
文件名：associations.py
描述：数据库关联表定义
作者：denny
创建日期：2024-03-21
"""

from app.extensions import db

# 文章标签关联表
post_tags = db.Table(
    'post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    db.UniqueConstraint('post_id', 'tag_id', name='uq_post_tag'),
    db.CheckConstraint('post_id IS NOT NULL AND tag_id IS NOT NULL', name='chk_post_tag_not_null'),
    extend_existing=True
)
