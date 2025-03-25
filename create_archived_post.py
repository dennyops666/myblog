#!/usr/bin/env python3
"""
创建一篇归档状态的文章
"""
from app import create_app
from app.models.post import Post, PostStatus
from app.extensions import db
from datetime import datetime, UTC
import random

app = create_app()

with app.app_context():
    print("===== 创建测试归档文章 =====")
    
    # 检查是否已经存在同名文章
    title = f"测试归档文章_{random.randint(1000, 9999)}"
    existing = Post.query.filter_by(title=title).first()
    if existing:
        print(f"同名文章已存在，使用随机标题")
        title = f"测试归档文章_{random.randint(10000, 99999)}"
    
    # 创建新文章
    post = Post(
        title=title,
        content=f"这是一篇测试归档功能的文章，创建于 {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}",
        summary="测试归档功能",
        status=PostStatus.ARCHIVED,
        author_id=1,  # 假设ID为1的用户存在
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    # 保存到数据库
    try:
        db.session.add(post)
        db.session.commit()
        print(f"已成功创建文章 '{title}', ID: {post.id}, 状态: {post.status}")
    except Exception as e:
        db.session.rollback()
        print(f"创建文章失败: {e}")
    
    # 查询所有归档文章
    print("\n当前所有归档状态的文章:")
    archived_posts = Post.query.filter_by(status=PostStatus.ARCHIVED).all()
    for p in archived_posts:
        print(f"ID: {p.id}, 标题: {p.title}, 状态: {p.status}")
    
    # 使用字符串值查询
    print("\n使用字符串值查询:")
    str_posts = Post.query.filter_by(status='ARCHIVED').all()
    for p in str_posts:
        print(f"ID: {p.id}, 标题: {p.title}, 状态: {p.status}")
    
    # 使用OR条件查询
    print("\n使用OR条件查询:")
    from sqlalchemy import or_
    or_posts = Post.query.filter(
        or_(Post.status == PostStatus.PUBLISHED, Post.status == PostStatus.ARCHIVED)
    ).all()
    
    print(f"找到 {len(or_posts)} 篇文章")
    for i, p in enumerate(or_posts):
        print(f"{i+1}. ID: {p.id}, 标题: {p.title}, 状态: {p.status}") 