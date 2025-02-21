"""
文件名：category.py
描述：分类管理控制器
作者：denny
创建日期：2024-03-21
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.services import CategoryService
from . import admin_bp

category_service = CategoryService()

@admin_bp.route('/categories')
@login_required
def categories():
    """分类列表页面"""
    page = request.args.get('page', 1, type=int)
    result = category_service.get_category_list(page=page)
    return render_template('admin/category/list.html',
        categories=result['items'],
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

@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
def create_category():
    """创建分类"""
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        
        if not all([name, slug]):
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('admin.create_category'))
            
        result = category_service.create_category(name, slug)
        if result['status'] == 'success':
            flash('分类创建成功', 'success')
            return redirect(url_for('admin.categories'))
        else:
            flash(result['message'], 'danger')
            return redirect(url_for('admin.create_category'))
            
    return render_template('admin/category/create.html')

@admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """编辑分类"""
    category = category_service.get_category_by_id(category_id)
    if not category:
        flash('分类不存在', 'danger')
        return redirect(url_for('admin.categories'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        
        if not all([name, slug]):
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('admin.edit_category', category_id=category_id))
            
        result = category_service.update_category(category_id, name, slug)
        if result['status'] == 'success':
            flash('分类更新成功', 'success')
            return redirect(url_for('admin.categories'))
        else:
            flash(result['message'], 'danger')
            return redirect(url_for('admin.edit_category', category_id=category_id))
            
    return render_template('admin/category/edit.html', category=category)

@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    """删除分类"""
    result = category_service.delete_category(category_id)
    if result['status'] == 'success':
        flash('分类删除成功', 'success')
    else:
        flash(result['message'], 'danger')
        
    return redirect(url_for('admin.categories')) 