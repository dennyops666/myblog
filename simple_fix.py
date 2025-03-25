#!/usr/bin/env python
print("开始修复归档功能...")

from app import create_app
from app.models.post import Post, PostStatus
from app.extensions import db, cache

app = create_app()

with app.app_context():
    # 修改文章状态为归档
    posts = Post.query.filter(Post.title.in_(["小型博客系统开发文档", "test01"])).all()
    print(f"找到 {len(posts)} 篇要归档的文章")
    
    for post in posts:
        post.status = PostStatus.ARCHIVED
        print(f"已将文章 '{post.title}' (ID: {post.id}) 设置为归档状态")
    
    # 提交更改
    db.session.commit()
    
    # 清除缓存
    cache.clear()
    
    # 验证修改
    archived = Post.query.filter_by(status=PostStatus.ARCHIVED).all()
    print(f"现在共有 {len(archived)} 篇归档文章:")
    for post in archived:
        print(f"- ID: {post.id}, 标题: {post.title}")

print("修复完成，请重启应用: /data/myblog/manage.sh restart") 