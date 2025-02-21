"""
文件名：tag.py
描述：标签管理控制器
作者：denny
创建日期：2024-03-21
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.services import TagService
from . import admin_bp
from app.extensions import csrf

tag_service = TagService()

@admin_bp.route('/tags')
@login_required
def tags():
    """标签列表页面"""
    page = request.args.get('page', 1, type=int)
    result = tag_service.get_tag_list(page=page)
    return render_template('admin/tag/list.html',
        tags=result['items'],
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

@admin_bp.route('/tags/create', methods=['GET', 'POST'])
@login_required
def create_tag():
    """创建标签"""
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        csrf_token = request.form.get('csrf_token')
        
        if not name or not csrf_token:
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('admin.create_tag'))
            
        result = tag_service.create_tag(name=name, slug=slug)
        if result['status'] == 'success':
            flash('标签创建成功', 'success')
            return redirect(url_for('admin.tags'))
        else:
            flash(result['message'], 'danger')
            return redirect(url_for('admin.create_tag'))
            
    return render_template('admin/tag/create.html')

@admin_bp.route('/tags/<int:tag_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_tag(tag_id):
    """编辑标签"""
    tag = tag_service.get_tag_by_id(tag_id)
    if not tag:
        flash('标签不存在', 'danger')
        return redirect(url_for('admin.tags'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        csrf_token = request.form.get('csrf_token')
        
        if not all([name, csrf_token]):
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('admin.edit_tag', tag_id=tag_id))
            
        result = tag_service.update_tag(tag_id, name=name, slug=slug)
        if result['status'] == 'success':
            flash('标签更新成功', 'success')
            return redirect(url_for('admin.tags'))
        else:
            flash(result['message'], 'danger')
            return redirect(url_for('admin.edit_tag', tag_id=tag_id))
            
    return render_template('admin/tag/edit.html', tag=tag)

@admin_bp.route('/tags/<int:tag_id>/delete', methods=['POST'])
@login_required
def delete_tag(tag_id):
    """删除标签"""
    csrf_token = request.form.get('csrf_token')
    if not csrf_token:
        return jsonify({'status': 'error', 'message': '缺少CSRF令牌'}), 400
        
    result = tag_service.delete_tag(tag_id)
    if result['status'] == 'success':
        flash('标签删除成功', 'success')
    else:
        flash(result['message'], 'danger')
        
    return redirect(url_for('admin.tags')) 