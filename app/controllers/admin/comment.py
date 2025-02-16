"""
文件名：comment.py
描述：评论管理控制器
作者：denny
创建日期：2025-02-16
"""

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.services import CommentService
from . import admin_bp

@admin_bp.route('/comments')
@login_required
def comments():
    """评论列表页面"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', type=int)
    
    # 获取评论列表
    if status == 0:  # 待审核评论
        comments = CommentService.get_pending_comments(page)
    else:  # 所有评论
        comments = CommentService.get_comments_by_page(page)
    
    return render_template('admin/comment/list.html', comments=comments, current_status=status)

@admin_bp.route('/comments/<int:comment_id>/approve', methods=['POST'])
@login_required
def approve_comment(comment_id):
    """审核通过评论"""
    comment = CommentService.get_comment_by_id(comment_id)
    if not comment:
        flash('评论不存在', 'danger')
    else:
        try:
            CommentService.approve_comment(comment)
            flash('评论已通过审核', 'success')
        except Exception as e:
            flash(f'操作失败：{str(e)}', 'danger')
    
    return redirect(url_for('admin.comments', status=0))

@admin_bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """删除评论"""
    comment = CommentService.get_comment_by_id(comment_id)
    if not comment:
        flash('评论不存在', 'danger')
    else:
        try:
            CommentService.reject_comment(comment)
            flash('评论已删除', 'success')
        except Exception as e:
            flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('admin.comments')) 