"""
文件名：category.py
描述：分类管理控制器
作者：denny
创建日期：2025-02-16
"""

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.services import CategoryService
from . import admin_bp

@admin_bp.route('/categories')
@login_required
def categories():
    """分类列表页面"""
    categories = CategoryService.get_all_categories()
    return render_template('admin/category/list.html', categories=categories)

@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
def create_category():
    """创建分类"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('请填写分类名称', 'danger')
        else:
            try:
                CategoryService.create_category(name=name, description=description)
                flash('分类创建成功', 'success')
                return redirect(url_for('admin.categories'))
            except Exception as e:
                flash(f'分类创建失败：{str(e)}', 'danger')
    
    return render_template('admin/category/create.html')

@admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """编辑分类"""
    category = CategoryService.get_category_by_id(category_id)
    if not category:
        flash('分类不存在', 'danger')
        return redirect(url_for('admin.categories'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('请填写分类名称', 'danger')
        else:
            try:
                CategoryService.update_category(
                    category,
                    name=name,
                    description=description
                )
                flash('分类更新成功', 'success')
                return redirect(url_for('admin.categories'))
            except Exception as e:
                flash(f'分类更新失败：{str(e)}', 'danger')
    
    return render_template('admin/category/edit.html', category=category)

@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    """删除分类"""
    category = CategoryService.get_category_by_id(category_id)
    if not category:
        flash('分类不存在', 'danger')
    else:
        # 检查分类下是否有文章
        if category.posts:
            flash('该分类下还有文章，无法删除', 'danger')
        else:
            try:
                CategoryService.delete_category(category)
                flash('分类删除成功', 'success')
            except Exception as e:
                flash(f'分类删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('admin.categories')) 