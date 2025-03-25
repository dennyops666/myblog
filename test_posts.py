#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app
from app.services import get_post_service
from app.models.post import PostStatus
import traceback
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO)

try:
    app = create_app()
    with app.app_context():
        try:
            post_service = get_post_service()
            
            # 测试获取所有状态的文章
            print("开始测试获取最近文章...")
            recent_posts = post_service.get_recent_posts(limit=10)
            print(f"获取到的文章数量: {len(recent_posts) if recent_posts else 0}")
            if recent_posts:
                for i, post in enumerate(recent_posts, 1):
                    print(f"{i}. {post.title} - 状态: {post.status}")
            else:
                print("没有获取到任何文章")
            
            # 测试获取已发布文章
            print("\n开始测试获取已发布文章...")
            published_posts = post_service.get_posts_by_status(PostStatus.PUBLISHED, page=1, per_page=10)
            print(f'已发布文章数量: {len(published_posts.items)}')
            
            # 测试获取草稿文章
            print("\n开始测试获取草稿文章...")
            draft_posts = post_service.get_posts_by_status(PostStatus.DRAFT, page=1, per_page=10)
            print(f'草稿文章数量: {len(draft_posts.items)}')
        except Exception as e:
            print(f"应用上下文中出错: {e}")
            traceback.print_exc()
except Exception as e:
    print(f"创建应用出错: {e}")
    traceback.print_exc() 