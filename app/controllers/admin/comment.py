"""
文件名：comment.py
描述：评论管理控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.services import CommentService
from app.extensions import db

comment_bp = Blueprint('comment', __name__, url_prefix='/comments')
comment_service = CommentService()

@comment_bp.route('/')
@login_required
def index():
    """评论列表页面"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    current_status = request.args.get('status', None, type=int)
    
    if current_status == 0:
        result = comment_service.get_pending_comments(page=page, per_page=per_page)
    else:
        result = comment_service.get_comments(page=page, per_page=per_page)
    
    return render_template('admin/comment/list.html', 
                         comments=result,  # 直接传递分页对象
                         current_status=current_status)

@comment_bp.route('/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(comment_id):
    """编辑评论"""
    result = comment_service.get_comment(comment_id)
    if result['status'] == 'error':
        flash(result['message'], 'error')
        return redirect(url_for('admin.comment.index'))
        
    comment = result['comment']
    if request.method == 'POST':
        content = request.form.get('content')
        
        try:
            result = comment_service.update_comment(comment_id, content)
            if result['status'] == 'success':
                flash('评论更新成功', 'success')
                return redirect(url_for('admin.comment.index'))
            else:
                flash(result['message'], 'error')
        except Exception as e:
            flash(str(e), 'error')
            
    return render_template('admin/comment/edit.html', comment=comment)

@comment_bp.route('/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete(comment_id):
    """删除评论"""
    try:
        result = comment_service.delete_comment(comment_id)
        if result['status'] == 'success':
            flash('评论删除成功', 'success')
        else:
            flash(result['message'], 'error')
    except Exception as e:
        flash(str(e), 'error')
        
    return redirect(url_for('admin.comment.index'))

@comment_bp.route('/<int:comment_id>/approve', methods=['POST'])
@login_required
def approve(comment_id):
    """审核通过评论"""
    try:
        success, message = comment_service.approve_comment(comment_id)
        if success:
            flash('评论审核通过', 'success')
        else:
            flash(message, 'error')
    except Exception as e:
        flash(str(e), 'error')
        
    return redirect(url_for('admin.comment.index'))

@comment_bp.route('/<int:comment_id>/reject', methods=['POST'])
@login_required
def reject(comment_id):
    """拒绝评论"""
    try:
        success, message = comment_service.reject_comment(comment_id)
        if success:
            flash('评论已被拒绝', 'success')
        else:
            flash(message, 'error')
    except Exception as e:
        flash(str(e), 'error')
        
    return redirect(url_for('admin.comment.index')) 