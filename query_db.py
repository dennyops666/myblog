from app import create_app, db
from app.models import Post, Tag, Category, User, Comment

app = create_app()
with app.app_context():
    print('文章总数:', Post.query.count())
    print('标签总数:', Tag.query.count())
    print('分类总数:', Category.query.count())
    print('用户总数:', User.query.count())
    print('评论总数:', Comment.query.count())
    
    # 查看最新的文章
    latest_post = Post.query.order_by(Post.created_at.desc()).first()
    if latest_post:
        print('\n最新文章:')
        print(f'标题: {latest_post.title}')
        print(f'创建时间: {latest_post.created_at}')
        print(f'状态: {latest_post.status}')
        
    # 查看用户信息
    users = User.query.all()
    print('\n用户列表:')
    for user in users:
        print(f'用户名: {user.username}, 邮箱: {user.email}, 角色: {user.role}') 