"""
文件名：comment.py
描述：评论控制器
作者：denny
"""

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from app.services import CommentService, PostService
from app.models import Comment, Post, db

comment_bp = Blueprint('comment', __name__)

comment_service = CommentService()
post_service = PostService()

@comment_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
def create_comment(post_id):
    """创建评论"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
        
    content = data.get('content')
    author_name = data.get('author_name')
    author_email = data.get('author_email')
    parent_id = data.get('parent_id')
    
    if not content:
        return jsonify({'error': '评论内容不能为空'}), 400
        
    result = comment_service.create_comment(
        post_id=post_id,
        content=content,
        author_name=author_name,
        author_email=author_email,
        parent_id=parent_id
    )
    
    if result['status'] == 'success':
        return jsonify({
            'message': '评论提交成功，等待审核',
            'comment': {
                'id': result['comment'].id,
                'content': result['comment'].content,
                'author_name': result['comment'].author_name,
                'created_at': result['comment'].created_at.isoformat()
            }
        })
    else:
        return jsonify({'error': result['message']}), 400

@comment_bp.route('/admin/comments')
@login_required
def admin_comments():
    """评论管理页面"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', None, type=int)
    
    if status == 0:
        result = comment_service.get_pending_comments(page)
    else:
        result = comment_service.get_comments_by_post(None, True, page)
        
    return render_template('admin/comment/list.html',
        comments=result['comments'],
        pagination=result
    )

@comment_bp.route('/admin/comments/<int:comment_id>/approve', methods=['POST'])
@login_required
def approve_comment(comment_id):
    """审核通过评论"""
    result = comment_service.approve_comment(comment_id)
    
    if result['status'] == 'success':
        return jsonify({'message': '评论已审核通过'})
    else:
        return jsonify({'error': result['message']}), 400

@comment_bp.route('/admin/comments/<int:comment_id>/reject', methods=['POST'])
@login_required
def reject_comment(comment_id):
    """拒绝评论"""
    result = comment_service.reject_comment(comment_id)
    
    if result['status'] == 'success':
        return jsonify({'message': '评论已拒绝'})
    else:
        return jsonify({'error': result['message']}), 400

@comment_bp.route('/admin/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    """删除评论"""
    result = comment_service.delete_comment(comment_id)
    
    if result['status'] == 'success':
        return jsonify({'message': '评论已删除'})
    else:
        return jsonify({'error': result['message']}), 400

@comment_bp.route('/posts/<int:post_id>/comments')
def get_comments(post_id):
    """获取文章评论"""
    page = request.args.get('page', 1, type=int)
    result = comment_service.get_comments_by_post(post_id, page=page)
    
    return jsonify({
        'comments': [{
            'id': comment.id,
            'content': comment.content,
            'author_name': comment.author_name,
            'created_at': comment.created_at.isoformat(),
            'parent_id': comment.parent_id
        } for comment in result['comments']],
        'total': result['total'],
        'pages': result['pages'],
        'current_page': result['current_page'],
        'has_next': result['has_next'],
        'has_prev': result['has_prev']
    }) 