from app import create_app
from app.models.post import Post

def check_post(post_id):
    app = create_app()
    with app.app_context():
        post = Post.query.get(post_id)
        if post:
            print(f"文章ID {post_id} 存在")
            print(f"标题: {post.title}")
            print(f"状态: {post.status}")
            print(f"HTML内容长度: {len(post.html_content) if post.html_content else 0}")
            print(f"更新时间: {post.updated_at}")
        else:
            print(f"文章ID {post_id} 不存在")

if __name__ == "__main__":
    check_post(6) 