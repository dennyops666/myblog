#!/usr/bin/env python3
"""归档调试脚本"""
from app import create_app
from app.models.post import Post, PostStatus
from app.services.post import PostService
from sqlalchemy import desc

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("查询所有文章：")
        posts = Post.query.all()
        for post in posts:
            print(f"ID: {post.id}, 标题: {post.title}, 状态: {post.status}, 创建时间: {post.created_at}")
        
        print("\n查询PUBLISHED状态的文章：")
        posts = Post.query.filter_by(status=PostStatus.PUBLISHED).all()
        for post in posts:
            print(f"ID: {post.id}, 标题: {post.title}, 状态: {post.status}, 创建时间: {post.created_at}")
        
        print("\n查询ARCHIVED状态的文章：")
        posts = Post.query.filter_by(status=PostStatus.ARCHIVED).all()
        for post in posts:
            print(f"ID: {post.id}, 标题: {post.title}, 状态: {post.status}, 创建时间: {post.created_at}")
        
        print("\n使用OR条件查询文章：")
        posts = Post.query.filter(
            (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
        ).all()
        for post in posts:
            print(f"ID: {post.id}, 标题: {post.title}, 状态: {post.status}, 创建时间: {post.created_at}")
        
        print("\n调用get_archives查看结果：")
        archives = PostService.get_archives()
        print(f"归档条目数量：{len(archives)}")
        for key, posts in archives.items():
            print(f"归档时间：{key}, 文章数量：{len(posts)}")
            for post in posts:
                print(f"  - ID: {post.id}, 标题: {post.title}, 状态: {post.status}, 创建时间: {post.created_at}") 