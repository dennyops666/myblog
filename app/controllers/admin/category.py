"""
文件名：category.py
描述：分类管理控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app.models.category import Category
from app.forms.category_form import CategoryForm
from app.extensions import db
from sqlalchemy.exc import IntegrityError

category_bp = Blueprint('admin_category', __name__, url_prefix='/categories')

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
        try:
            # 检查分类名是否已存在
            existing_name = Category.query.filter_by(name=form.name.data).first()
            if existing_name:
                flash('分类名称已存在，请使用其他名称', 'warning')
                return render_template('admin/category/create.html', form=form)
            
            # 如果提供了slug，检查是否已存在
            if form.slug.data:
                existing_slug = Category.query.filter_by(slug=form.slug.data).first()
                if existing_slug:
                    flash('分类别名已存在，请使用其他别名', 'warning')
                    return render_template('admin/category/create.html', form=form)
            
            category = Category(
                name=form.name.data,
                slug=form.slug.data if form.slug.data else None,
                description=form.description.data
            )
            db.session.add(category)
            db.session.commit()
            flash('分类创建成功', 'success')
            return redirect(url_for('.index'))
        except IntegrityError:
            db.session.rollback()
            flash('分类名称或别名已存在，请修改后重试', 'warning')
            return render_template('admin/category/create.html', form=form)
        except Exception as e:
            db.session.rollback()
            flash('创建分类时发生错误，请稍后重试', 'error')
            return render_template('admin/category/create.html', form=form)
    return render_template('admin/category/create.html', form=form)

@category_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        try:
            # 检查名称是否已被其他分类使用
            existing = Category.query.filter(
                Category.name == form.name.data,
                Category.id != id
            ).first()
            if existing:
                flash('分类名称已存在，请使用其他名称', 'warning')
                return render_template('admin/category/edit.html', form=form, category=category)
            
            # 如果提供了slug，检查是否已被其他分类使用
            if form.slug.data:
                existing = Category.query.filter(
                    Category.slug == form.slug.data,
                    Category.id != id
                ).first()
                if existing:
                    flash('分类别名已存在，请使用其他别名', 'warning')
                    return render_template('admin/category/edit.html', form=form, category=category)
            
            category.name = form.name.data
            category.slug = form.slug.data if form.slug.data else None
            category.description = form.description.data
            db.session.commit()
            flash('分类更新成功', 'success')
            return redirect(url_for('.index'))
        except IntegrityError:
            db.session.rollback()
            flash('分类名称或别名已存在，请修改后重试', 'warning')
            return render_template('admin/category/edit.html', form=form, category=category)
        except Exception as e:
            db.session.rollback()
            flash('更新分类时发生错误，请稍后重试', 'error')
            return render_template('admin/category/edit.html', form=form, category=category)
    return render_template('admin/category/edit.html', form=form, category=category)

@category_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    category = Category.query.get_or_404(id)
    try:
        if category.posts.count() > 0:
            if request.is_xhr:
                return jsonify({
                    'success': False,
                    'message': '该分类下还有文章，无法删除'
                })
            flash('该分类下还有文章，无法删除', 'warning')
            return redirect(url_for('.index'))
            
        db.session.delete(category)
        db.session.commit()
        
        if request.is_xhr:
            return jsonify({
                'success': True,
                'message': '分类删除成功'
            })
        flash('分类删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_xhr:
            return jsonify({
                'success': False,
                'message': '删除分类时发生错误，请稍后重试'
            })
        flash('删除分类时发生错误，请稍后重试', 'error')
    return redirect(url_for('.index'))

@category_bp.route('/search')
@login_required
def search():
    """搜索分类的 API 接口"""
    term = request.args.get('term', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 构建查询
    query = Category.query.order_by(Category.name)
    
    # 如果有搜索词，添加过滤条件
    if term:
        query = query.filter(Category.name.ilike(f'%{term}%'))
    
    # 分页
    offset = (page - 1) * per_page
    categories = query.limit(per_page).offset(offset).all()
    
    # 计算是否有更多结果
    total = query.count()
    has_more = total > offset + per_page
    
    # 格式化返回结果
    results = [{
        'id': category.id,
        'text': category.name,
        'description': category.description or ''
    } for category in categories]
    
    return jsonify({
        'results': results,
        'pagination': {
            'more': has_more
        }
    }) 