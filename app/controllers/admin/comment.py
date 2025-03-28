"""
文件名：comment.py
描述：评论管理视图
作者：denny
"""

import traceback
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.services import get_comment_service
from app.models.comment import Comment, CommentStatus
from app.extensions import db
from sqlalchemy.orm import joinedload

# 创建Blueprint
comment_bp = Blueprint('comment', __name__, url_prefix='/comment')

# 获取服务实例
comment_service = get_comment_service()

@comment_bp.route('/')
@login_required
def index():
    """评论列表页面"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        # 默认显示所有评论（不再按状态筛选）
        parent_only = request.args.get('parent_only', False, type=bool)
        
        # 构建查询
        query = Comment.query.options(
            joinedload(Comment.post),  # 预加载文章信息
            joinedload(Comment.author)  # 预加载作者信息
        )
        
        # 如果只显示父评论
        if parent_only:
            query = query.filter(Comment.parent_id == None)
            
        # 按时间倒序排序
        query = query.order_by(Comment.created_at.desc())
        
        # 使用 SQLAlchemy 的分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        comments = pagination.items
        
        # 确保每个评论的 post 对象已加载
        for comment in comments:
            if comment.post is None:
                current_app.logger.warning(f"评论 {comment.id} 的文章不存在 (post_id={comment.post_id})")
            else:
                current_app.logger.info(f"评论 {comment.id} 关联文章: {comment.post.title}")
        
        # 获取评论统计信息
        stats = {
            'pending': Comment.query.filter_by(status=CommentStatus.PENDING).count(),
            'approved': Comment.query.filter_by(status=CommentStatus.APPROVED).count(),
            'rejected': Comment.query.filter_by(status=CommentStatus.REJECTED).count(),
            'total': Comment.query.count()
        }
        
        # 打印调试信息
        current_app.logger.info(f"评论数量: {len(comments)}")
        
        return render_template('admin/comment/list.html', 
                             comments=comments,
                             pagination=pagination,
                             current_status=None,  # 不再指定状态
                             parent_only=parent_only,
                             stats=stats)
                             
    except Exception as e:
        current_app.logger.error(f'获取评论列表失败: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        flash('获取评论列表失败，请稍后重试', 'error')
        return render_template('admin/comment/list.html', 
                             comments=[],
                             pagination=None,
                             current_status=None,
                             parent_only=False,
                             stats=None)

@comment_bp.route('/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(comment_id):
    """编辑评论"""
    try:
        comment = comment_service.get_comment_by_id(comment_id)
        
        if not comment:
            flash('评论不存在', 'error')
            return redirect(url_for('admin_dashboard.comment.index'))
            
        if request.method == 'POST':
            content = request.form.get('content')
            
            if content and len(content.strip()) > 0:
                comment.content = content
                db.session.commit()
                flash('评论已更新', 'success')
                return redirect(url_for('admin_dashboard.comment.index'))
            else:
                flash('评论内容不能为空', 'error')
        
        return render_template('admin/comment/edit.html', comment=comment)
    except Exception as e:
        current_app.logger.error(f'编辑评论失败: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        flash('编辑评论失败，请稍后重试', 'error')
        return redirect(url_for('admin_dashboard.comment.index'))

@comment_bp.route('/approve/<int:comment_id>', methods=['POST'])
@login_required
def approve(comment_id):
    """批准评论"""
    approve_replies = False  # 默认不批准回复
    result = comment_service.approve_comment(comment_id, approve_replies)
    if result['status'] == 'success':
        flash('评论已批准', 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('admin_dashboard.comment.index'))

@comment_bp.route('/reject/<int:comment_id>', methods=['POST'])
@login_required
def reject(comment_id):
    """拒绝评论"""
    reject_replies = False  # 默认不拒绝回复
    result = comment_service.reject_comment(comment_id, reject_replies)
    if result['status'] == 'success':
        flash('评论已拒绝', 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('admin_dashboard.comment.index'))

@comment_bp.route('/delete/<int:comment_id>', methods=['GET', 'POST'])
@login_required
def delete(comment_id):
    try:
        # 获取评论
        comment = Comment.query.get_or_404(comment_id)
        
        # 删除评论
        db.session.delete(comment)
        db.session.commit()
        
        # 记录操作日志
        current_app.logger.info(f"管理员 {current_user.username} 删除了评论ID {comment_id}")
        
        # 设置成功消息
        flash("评论删除成功", "success")
    except Exception as e:
        # 回滚事务
        db.session.rollback()
        
        # 记录错误
        current_app.logger.error(f"删除评论失败: {str(e)}")
        
        # 设置错误消息
        flash(f"删除评论失败: {str(e)}", "error")
    
    # 重定向到评论列表页
    return redirect(url_for('admin_dashboard.comment.index'))

@comment_bp.route('/batch-delete', methods=['POST'])
@login_required
def batch_delete():
    """批量删除评论"""
    try:
        comment_ids = request.json.get('ids', [])
        delete_replies = request.json.get('delete_replies', False)
        
        if not comment_ids:
            return jsonify({
                'success': False,
                'message': '请选择要删除的评论'
            })
        
        # 记录操作日志
        current_app.logger.info('批量删除评论', extra={
            'comment_ids': comment_ids,
            'delete_replies': delete_replies,
            'action': 'batch_delete_comments'
        })
        
        # 批量删除评论
        deleted_count = 0
        deleted_replies_count = 0
        
        for comment_id in comment_ids:
            result = comment_service.delete_comment(comment_id, delete_replies)
            if result['status'] == 'success':
                deleted_count += 1
                deleted_replies_count += result.get('deleted_replies_count', 0)
        
        # 获取最新的评论统计
        stats = comment_service.get_comment_stats()
        
        # 记录成功日志
        current_app.logger.info('批量删除评论成功', extra={
            'deleted_count': deleted_count,
            'deleted_replies_count': deleted_replies_count,
            'action': 'batch_delete_comments_success'
        })
        
        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count} 条评论和 {deleted_replies_count} 条回复',
            'stats': stats
        })
        
    except Exception as e:
        # 记录错误日志
        current_app.logger.error(f'批量删除评论失败: {str(e)}', extra={
            'error': str(e),
            'traceback': traceback.format_exc(),
            'action': 'batch_delete_comments_error'
        })
        
        return jsonify({
            'success': False,
            'message': '系统错误，请稍后重试'
        }), 500