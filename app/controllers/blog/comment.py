from flask import Blueprint, request, jsonify, current_app
from app.models.comment import Comment
from app.models.post import Post
from app.extensions import db
from app.utils.decorators import login_required
from datetime import datetime
import logging

comment_bp = Blueprint('comment', __name__)

# 获取日志器
logger = logging.getLogger(__name__)

@comment_bp.route('/<int:post_id>/comments', methods=['POST'])
def create_comment(post_id):
    """创建评论"""
    try:
        logger.info(f"开始处理评论创建请求，文章ID: {post_id}")
        
        # 获取评论内容
        content = ''
        nickname = ''
        
        # 支持 JSON 和表单数据
        if request.is_json:
            data = request.get_json()
            content = data.get('content', '').strip() if data else ''
            nickname = data.get('nickname', '').strip() if data else ''
        else:
            content = request.form.get('content', '').strip()
            nickname = request.form.get('nickname', '').strip()
        
        # 验证评论内容
        if not content:
            logger.warning("评论创建失败：内容为空")
            return jsonify({
                'success': False,
                'message': '评论内容不能为空'
            }), 400
            
        # 获取文章
        post = Post.query.get(post_id)
        if not post:
            logger.error(f"评论创建失败：文章不存在，ID: {post_id}")
            return jsonify({
                'success': False,
                'message': '文章不存在'
            }), 404
        
        # 创建评论
        comment = Comment(
            content=content,
            post_id=post_id,
            status=0  # 待审核状态
        )
        
        # 处理作者信息
        if hasattr(request, 'user') and request.user:
            comment.author_id = request.user.id
            logger.info(f"评论作者为登录用户，ID: {request.user.id}")
        else:
            if not nickname:
                logger.warning("评论创建失败：未登录用户未提供昵称")
                return jsonify({
                    'success': False,
                    'message': '请输入昵称'
                }), 400
            comment.nickname = nickname
            logger.info(f"评论作者为访客，昵称: {nickname}")
            
        # 保存评论
        db.session.add(comment)
        db.session.commit()
        
        logger.info(f"评论创建成功，ID: {comment.id}")
        return jsonify({
            'success': True,
            'message': '评论提交成功，请等待审核',
            'data': {
                'id': comment.id,
                'content': comment.content,
                'author': comment.author.username if comment.author else comment.nickname,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        logger.error(f"评论创建失败，发生异常: {str(e)}")
        logger.exception(e)  # 记录完整的异常堆栈
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '评论提交失败，请稍后重试'
        }), 500 