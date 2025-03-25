from app import create_app
from app.models.post import Post, PostStatus
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO)

# 创建应用实例
app = create_app()
with app.app_context():
    print("-" * 50)
    print("正在查询所有文章...")
    
    # 直接从数据库查询
    all_posts = Post.query.all()
    print(f"数据库中共有 {len(all_posts)} 篇文章")
    
    # 按状态查询
    for status in PostStatus:
        posts = Post.query.filter_by(status=status).all()
        print(f"状态为 {status.name} 的文章数量: {len(posts)}")
        
        # 输出文章详情
        if posts:
            print(f"\n{status.name} 文章列表:")
            for i, post in enumerate(posts, 1):
                print(f"{i}. ID={post.id}, 标题={post.title}, 创建时间={post.created_at}")
    
    print("-" * 50) 