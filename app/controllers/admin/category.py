"""
文件名：category.py
描述：分类管理控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.models.category import Category
from app.forms.category_form import CategoryForm
from app.extensions import db

category_bp = Blueprint('category', __name__, url_prefix='/category')

@category_bp.route('/')
@login_required
def index():
    """分类列表页面"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    categories = Category.query.order_by(Category.id.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    return render_template('admin/category/list.html', categories=categories)

@category_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            slug=form.slug.data,
            description=form.description.data
        )
        db.session.add(category)
        db.session.commit()
        flash('分类创建成功', 'success')
        return redirect(url_for('.index'))
    return render_template('admin/category/create.html', form=form)

@category_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        category.name = form.name.data
        category.slug = form.slug.data
        category.description = form.description.data
        db.session.commit()
        flash('分类更新成功', 'success')
        return redirect(url_for('.index'))
    return render_template('admin/category/edit.html', form=form, category=category)

@category_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('分类删除成功', 'success')
    return redirect(url_for('.index')) 