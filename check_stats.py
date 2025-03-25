from app import create_app
from app.models.post import Post, PostStatus
from app.models.tag import Tag
from app.models.category import Category

app = create_app()
with app.app_context():
    print('文章总数:', Post.query.count())
    print('已发布文章数:', Post.query.filter_by(status=PostStatus.PUBLISHED).count())
    print('草稿数:', Post.query.filter_by(status=PostStatus.DRAFT).count())
    print('标签数:', Tag.query.count())
    print('分类数:', Category.query.count())
    
    # 打印所有文章的状态
    all_posts = Post.query.all()
    print('\n所有文章:')
    for post in all_posts:
        print(f'ID: {post.id}, 标题: {post.title}, 状态: {post.status}') 