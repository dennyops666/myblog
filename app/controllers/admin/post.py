"""
文件名：post.py
描述：文章管理控制器
作者：denny
创建日期：2024-03-21
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.services import PostService
from app.models.post import PostStatus
from . import admin_bp

post_service = PostService()

@admin_bp.route('/posts')
@login_required
def posts():
    """文章列表页面"""
    page = request.args.get('page', 1, type=int)
    result = post_service.get_post_list(page=page)
    return render_template('admin/post/list.html',
        posts=result['items'],
        pagination={
            'page': result['page'],
            'per_page': result['per_page'],
            'total': result['total'],
            'pages': result['pages'],
            'has_prev': result['has_prev'],
            'has_next': result['has_next'],
            'prev_num': result['prev_num'],
            'next_num': result['next_num']
        }
    )

@admin_bp.route('/posts/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """创建文章"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id', type=int)
        status = request.form.get('status', 'draft')
        
        if not all([title, content, category_id]):
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('admin.create_post'))
            
        result = post_service.create_post(
            title=title,
            content=content,
            category_id=category_id,
            status=PostStatus.PUBLISHED if status == 'published' else PostStatus.DRAFT,
            author=current_user
        )
        
        if result['status'] == 'success':
            flash('文章创建成功', 'success')
            return redirect(url_for('admin.posts'))
        else:
            flash(result['message'], 'danger')
            return redirect(url_for('admin.create_post'))
            
    return render_template('admin/post/create.html')

@admin_bp.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """编辑文章"""
    post = post_service.get_post_by_id(post_id)
    if not post:
        flash('文章不存在', 'danger')
        return redirect(url_for('admin.posts'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id', type=int)
        status = request.form.get('status', 'draft')
        
        if not all([title, content, category_id]):
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('admin.edit_post', post_id=post_id))
            
        result = post_service.update_post(
            post_id=post_id,
            title=title,
            content=content,
            category_id=category_id,
            status=PostStatus.PUBLISHED if status == 'published' else PostStatus.DRAFT
        )
        
        if result['status'] == 'success':
            flash('文章更新成功', 'success')
            return redirect(url_for('admin.posts'))
        else:
            flash(result['message'], 'danger')
            return redirect(url_for('admin.edit_post', post_id=post_id))
            
    return render_template('admin/post/edit.html', post=post)

@admin_bp.route('/posts/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    """删除文章"""
    result = post_service.delete_post(post_id)
    if result['status'] == 'success':
        flash('文章删除成功', 'success')
    else:
        flash(result['message'], 'danger')
    return redirect(url_for('admin.posts'))

@admin_bp.route('/posts/<int:post_id>/view')
@login_required
def view_post(post_id):
    """查看文章"""
    post = post_service.get_post_by_id(post_id)
    if not post:
        flash('文章不存在', 'danger')
        return redirect(url_for('admin.posts'))
    return render_template('admin/post/view.html', post=post)