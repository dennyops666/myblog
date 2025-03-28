"""
文件名：__init__.py
描述：API蓝图初始化
作者：denny
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
from app.models.post import Post, PostStatus
from app.extensions import db

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.before_request
def before_request():
    """请求预处理"""
    # 检查是否需要登录
    if current_app.config.get('LOGIN_REQUIRED'):
        if not current_user.is_authenticated:
            return jsonify({
                'status': 'error',
                'message': '请先登录'
            }), 401
    
    # 检查请求频率
    if current_app.config.get('RATE_LIMIT_ENABLED'):
        client_ip = request.remote_addr
        if not rate_limiter.is_allowed(client_ip):
            return jsonify({
                'status': 'error',
                'message': '请求过于频繁，请稍后再试'
            }), 429

@bp.route('/posts')
def get_posts():
    """获取文章列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', 'PUBLISHED')
        
        # 构建查询
        query = Post.query
        
        # 添加状态过滤
        if status != 'all':
            query = query.filter(Post.status == PostStatus[status])
        
        # 执行分页查询
        pagination = query.order_by(Post.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 格式化返回数据
        posts = [{
            'id': post.id,
            'title': post.title,
            'summary': post.summary,
            'content': post.content,
            'author': post.author.username if post.author else None,
            'category': post.category.name if post.category else None,
            'status': post.status.value,
            'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': post.updated_at.strftime('%Y-%m-%d %H:%M:%S') if post.updated_at else None
        } for post in pagination.items]
        
        return jsonify({
            'success': True,
            'data': {
                'posts': posts,
                'pagination': {
                    'page': pagination.page,
                    'pages': pagination.pages,
                    'total': pagination.total,
                    'per_page': pagination.per_page
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取文章列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取文章列表失败，请稍后重试'
        }), 500

@bp.after_request
def after_request(response):
    """请求后处理"""
    # 添加跨域支持
    if current_app.config.get('CORS_ENABLED'):
        response.headers['Access-Control-Allow-Origin'] = current_app.config.get('CORS_ORIGIN', '*')
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    return response

# 导入路由模块
from . import comment  # 只导入评论模块，其他模块暂时不导入

# 注册路由
bp.register_blueprint(comment.bp)

__all__ = ['bp']