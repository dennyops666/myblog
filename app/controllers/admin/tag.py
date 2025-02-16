"""
文件名：tag.py
描述：标签管理控制器
作者：denny
创建日期：2025-02-16
"""

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.services import TagService
from . import admin_bp

@admin_bp.route('/tags')
@login_required
def tags():
    """标签列表页面"""
    tags = TagService.get_all_tags()
    return render_template('admin/tag/list.html', tags=tags)

@admin_bp.route('/tags/create', methods=['GET', 'POST'])
@login_required
def create_tag():
    """创建标签"""
    if request.method == 'POST':
        name = request.form.get('name')
        
        if not name:
            flash('请填写标签名称', 'danger')
        else:
            try:
                TagService.create_tag(name=name)
                flash('标签创建成功', 'success')
                return redirect(url_for('admin.tags'))
            except Exception as e:
                flash(f'标签创建失败：{str(e)}', 'danger')
    
    return render_template('admin/tag/create.html')

@admin_bp.route('/tags/<int:tag_id>/rename', methods=['GET', 'POST'])
@login_required
def rename_tag(tag_id):
    """重命名标签"""
    tag = TagService.get_tag_by_id(tag_id)
    if not tag:
        flash('标签不存在', 'danger')
        return redirect(url_for('admin.tags'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        
        if not name:
            flash('请填写标签名称', 'danger')
        else:
            try:
                TagService.update_tag(tag, name=name)
                flash('标签重命名成功', 'success')
                return redirect(url_for('admin.tags'))
            except Exception as e:
                flash(f'标签重命名失败：{str(e)}', 'danger')
    
    return render_template('admin/tag/rename.html', tag=tag)

@admin_bp.route('/tags/merge', methods=['GET', 'POST'])
@login_required
def merge_tags():
    """合并标签"""
    if request.method == 'POST':
        source_id = request.form.get('source_id', type=int)
        target_id = request.form.get('target_id', type=int)
        
        if not all([source_id, target_id]):
            flash('请选择要合并的标签', 'danger')
        elif source_id == target_id:
            flash('不能合并相同的标签', 'danger')
        else:
            try:
                TagService.merge_tags(source_id, target_id)
                flash('标签合并成功', 'success')
                return redirect(url_for('admin.tags'))
            except Exception as e:
                flash(f'标签合并失败：{str(e)}', 'danger')
    
    tags = TagService.get_all_tags()
    return render_template('admin/tag/merge.html', tags=tags)

@admin_bp.route('/tags/<int:tag_id>/delete', methods=['POST'])
@login_required
def delete_tag(tag_id):
    """删除标签"""
    tag = TagService.get_tag_by_id(tag_id)
    if not tag:
        flash('标签不存在', 'danger')
    else:
        try:
            TagService.delete_tag(tag)
            flash('标签删除成功', 'success')
        except Exception as e:
            flash(f'标签删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('admin.tags')) 