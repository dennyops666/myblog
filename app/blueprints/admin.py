from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request, current_app
from flask_login import login_required, current_user
from app.services.comment import CommentService
from app.services.post import PostService
from app.services.category import CategoryService
from app.services.tag import TagService
from app.services.user import UserService
from app.models.comment import CommentStatus

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/comments/')
@login_required
def comments():
    """评论管理页面"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', 0, type=int)  # 默认显示待审核评论
        parent_only = request.args.get('parent_only', False, type=bool)
        
        comment_service = CommentService()
        # 获取评论列表
        result = comment_service.get_comments(
            page=page,
            per_page=per_page,
            status=status,
            parent_only=parent_only
        )
        
        current_app.logger.info(f"评论列表结果: {result}")
        
        # 获取评论统计信息
        stats = {
            'pending': comment_service.count_comments_by_status(CommentStatus.PENDING),
            'approved': comment_service.count_comments_by_status(CommentStatus.APPROVED),
            'rejected': comment_service.count_comments_by_status(CommentStatus.REJECTED)
        }
        
        current_app.logger.info(f"评论统计信息: {stats}")
        
        return render_template('admin/comment/list.html',
                             comments=result.get('comments', []),
                             pagination=result.get('pagination'),
                             current_status=status,
                             parent_only=parent_only,
                             stats=stats)
                             
    except Exception as e:
        current_app.logger.error(f"获取评论列表失败: {str(e)}")
        flash('获取评论列表失败', 'error')
        return render_template('admin/comment/list.html',
                             comments=[],
                             pagination=None,
                             current_status=0,
                             parent_only=False,
                             stats={'pending': 0, 'approved': 0, 'rejected': 0})

@admin_bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """删除评论"""
    try:
        comment_service = CommentService()
        result = comment_service.delete_comment(comment_id)
        if result['status'] == 'success':
            # 获取最新的评论统计
            stats = {
                'pending': comment_service.count_comments_by_status(CommentStatus.PENDING),
                'approved': comment_service.count_comments_by_status(CommentStatus.APPROVED),
                'rejected': comment_service.count_comments_by_status(CommentStatus.REJECTED)
            }
            return jsonify({
                'success': True,
                'message': result['message'],
                'stats': stats
            })
        return jsonify({
            'success': False,
            'message': result['message']
        })
    except Exception as e:
        current_app.logger.error(f"删除评论失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        })

@admin_bp.route('/comments/batch-delete', methods=['POST'])
@login_required
def batch_delete_comments():
    """批量删除评论"""
    try:
        data = request.get_json()
        comment_ids = data.get('comment_ids', [])
        delete_replies = data.get('delete_replies', False)
        
        comment_service = CommentService()
        result = comment_service.batch_delete_comments(comment_ids, delete_replies)
        
        if result['status'] == 'success':
            # 获取最新的评论统计
            stats = {
                'pending': comment_service.count_comments_by_status(CommentStatus.PENDING),
                'approved': comment_service.count_comments_by_status(CommentStatus.APPROVED),
                'rejected': comment_service.count_comments_by_status(CommentStatus.REJECTED)
            }
            return jsonify({
                'success': True,
                'message': result['message'],
                'stats': stats
            })
        return jsonify({
            'success': False,
            'message': result['message']
        })
        
    except Exception as e:
        current_app.logger.error(f"批量删除评论失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        })

@admin_bp.route('/comments/<int:comment_id>/approve', methods=['POST'])
@login_required
def approve_comment(comment_id):
    """审核通过评论"""
    try:
        approve_replies = request.json.get('approve_replies', False)
        comment_service = CommentService()
        result = comment_service.approve_comment(comment_id, approve_replies)
        
        if result['status'] == 'success':
            # 获取最新的评论统计
            stats = {
                'pending': comment_service.count_comments_by_status(CommentStatus.PENDING),
                'approved': comment_service.count_comments_by_status(CommentStatus.APPROVED),
                'rejected': comment_service.count_comments_by_status(CommentStatus.REJECTED)
            }
            return jsonify({
                'success': True,
                'status': 'success',
                'message': result['message'],
                'stats': stats
            })
        return jsonify({
            'success': False,
            'status': 'error',
            'message': result['message']
        })
    except Exception as e:
        current_app.logger.error(f"审核评论失败: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': str(e)
        })

@admin_bp.route('/admin/comments/<int:comment_id>/reject', methods=['POST'])
@login_required
def reject_comment(comment_id):
    """拒绝评论
    
    Args:
        comment_id: 评论id
        
    Returns:
        JSON响应
    """
    try:
        # 获取请求内容，检查是否需要同时拒绝回复
        request_json = request.get_json()
        current_app.logger.info(f"评论拒绝请求内容: {request_json}")
        reject_replies = request_json.get('reject_replies', False) if request_json else False
        current_app.logger.info(f"拒绝评论: {comment_id}, 同时拒绝回复: {reject_replies}")

        # 初始化CommentService
        comment_service = CommentService()
        
        # 拒绝评论
        result = comment_service.reject_comment(comment_id, reject_replies)
        
        if not result['success']:
            current_app.logger.error(f"拒绝评论失败: {result['message']}")
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
        
        # 获取最新评论统计
        stats = comment_service.get_comment_stats()
        
        return jsonify({
            'success': True,
            'message': '评论拒绝成功',
            'pending_count': stats['pending_count'],
            'approved_count': stats['approved_count'],
            'rejected_count': stats['rejected_count']
        })
    except Exception as e:
        current_app.logger.error(f"拒绝评论时发生异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'拒绝评论失败: {str(e)}'
        }), 500 