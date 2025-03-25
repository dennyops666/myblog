"""
文件名：comment.py
描述：评论API控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user
from app.services.comment import CommentService
from app.services.post import PostService
from app.models.comment import Comment, CommentStatus

bp = Blueprint('comment', __name__)

@bp.route('/posts/<int:post_id>/comments', methods=['POST'])
def create_comment(post_id):
    try:
        # 检查文章是否存在
        post = PostService.get_post_by_id(post_id)
        if not post:
            return jsonify({
                'success': False,
                'message': '文章不存在'
            }), 404

        data = request.get_json()
        content = data.get('content')
        nickname = data.get('nickname')
        email = data.get('email')
        parent_id = data.get('parent_id')

        # 获取当前用户ID
        author_id = current_user.id if current_user.is_authenticated else None

        # 创建评论
        result = CommentService.create_comment(
            post_id=post_id,
            content=content,
            author_id=author_id,
            nickname=nickname,
            email=email,
            parent_id=parent_id
        )

        if result['status'] == 'success':
            comment = result['comment']
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': {
                    'id': comment.id,
                    'content': comment.content,
                    'html_content': comment.html_content,
                    'author_name': comment.author.username if comment.author else comment.nickname,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': comment.status
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400

    except Exception as e:
        current_app.logger.error(f'创建评论失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': '评论创建失败'
        }), 500

@bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    try:
        # 获取评论列表 - 只获取已审核的评论，排除已拒绝的评论
        comments = Comment.query.filter(
            Comment.post_id == post_id,
            Comment.parent_id == None,  # 只获取顶级评论
            Comment.status == CommentStatus.APPROVED  # 只获取已审核的评论，状态值1
        ).order_by(Comment.created_at.desc()).all()
        
        # 格式化评论数据
        formatted_comments = []
        for comment in comments:
            formatted_comment = {
                'id': comment.id,
                'content': comment.content,
                'html_content': comment.html_content,
                'author_name': comment.author.username if comment.author else comment.nickname,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'status': comment.status,
                'replies': []
            }
            
            # 添加回复 - 也只获取已审核的回复
            if comment.replies:
                for reply in comment.replies.filter(Comment.status == CommentStatus.APPROVED).all():
                    formatted_reply = {
                        'id': reply.id,
                        'content': reply.content,
                        'html_content': reply.html_content,
                        'author_name': reply.author.username if reply.author else reply.nickname,
                        'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'status': reply.status
                    }
                    formatted_comment['replies'].append(formatted_reply)
                    
            formatted_comments.append(formatted_comment)

        return jsonify({
            'success': True,
            'data': formatted_comments
        })

    except Exception as e:
        current_app.logger.error(f'获取评论列表失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': '获取评论列表失败'
        }), 500 