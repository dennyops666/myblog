from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.post import Post, PostStatus
from app.models.category import Category
from app.models.tag import Tag
from app.models.comment import Comment
from app.extensions import db

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    """仪表板首页"""
    # 获取统计信息
    stats = {
        'posts': Post.query.filter_by(author_id=current_user.id).count(),
        'published_posts': Post.query.filter_by(author_id=current_user.id, status=PostStatus.PUBLISHED).count(),
        'draft_posts': Post.query.filter_by(author_id=current_user.id, status=PostStatus.DRAFT).count(),
        'categories': Category.query.count(),
        'tags': Tag.query.count(),
        'comments': Comment.query.join(Post).filter(Post.author_id == current_user.id).count()
    }
    
    # 获取最近的文章
    recent_posts = Post.query.filter_by(author_id=current_user.id).order_by(Post.created_at.desc()).limit(5).all()
    
    # 获取最近的评论
    recent_comments = Comment.query.join(Post).filter(Post.author_id == current_user.id).order_by(Comment.created_at.desc()).limit(5).all()
    
    return render_template('dashboard/index.html', 
                          title='仪表板', 
                          stats=stats, 
                          recent_posts=recent_posts, 
                          recent_comments=recent_comments)
