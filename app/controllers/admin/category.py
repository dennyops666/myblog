"""
文件名：category.py
描述：分类管理控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required
from app.services import CategoryService
from app.extensions import db
from app.forms.category_form import CategoryForm
from app.models.category import Category
from sqlalchemy.exc import IntegrityError

category_bp = Blueprint('admin_category', __name__)
category_service = CategoryService()

def is_ajax():
    """检查是否是 AJAX 请求"""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

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
    """创建分类"""
    form = CategoryForm()
    if request.method == 'POST':
        # 手动验证表单数据
        form.name.data = request.form.get('name')
        form.slug.data = request.form.get('slug')
        form.description.data = request.form.get('description')
        
        current_app.logger.debug(f'表单数据: {request.form}')
        current_app.logger.debug(f'表单验证结果: {form.validate()}')
        if form.errors:
            current_app.logger.debug(f'表单错误: {form.errors}')
            
        try:
            if form.validate():
                # 检查分类名是否已存在
                existing_name = Category.query.filter_by(name=form.name.data).first()
                if existing_name:
                    message = '分类名称已存在，请使用其他名称'
                    if is_ajax():
                        return jsonify({
                            'success': False, 
                            'message': message, 
                            'errors': {'name': [message]}
                        })
                    flash(message, 'warning')
                    return render_template('admin/category/create.html', form=form)
                
                # 处理别名
                slug = form.slug.data.strip() if form.slug.data else None
                current_app.logger.debug(f'处理后的别名: {slug}')
                
                # 如果提供了有效的slug，检查是否已存在
                if slug:
                    existing_slug = Category.query.filter_by(slug=slug).first()
                    if existing_slug:
                        message = '分类别名已存在，请使用其他别名'
                        if is_ajax():
                            return jsonify({
                                'success': False, 
                                'message': message, 
                                'errors': {'slug': [message]}
                            })
                        flash(message, 'warning')
                        return render_template('admin/category/create.html', form=form)
                
                try:
                    category = Category(
                        name=form.name.data,
                        slug=slug,
                        description=form.description.data
                    )
                    db.session.add(category)
                    db.session.commit()
                    current_app.logger.debug('分类创建成功')
                    
                    message = '分类创建成功'
                    if is_ajax():
                        return jsonify({
                            'success': True,
                            'message': message,
                            'redirect_url': url_for('.index')
                        })
                    flash(message, 'success')
                    return redirect(url_for('.index'))
                except IntegrityError as e:
                    db.session.rollback()
                    current_app.logger.error(f'数据库错误: {str(e)}')
                    message = '创建分类失败，请稍后重试'
                    if is_ajax():
                        return jsonify({
                            'success': False,
                            'message': message,
                            'errors': {'name': [message]}
                        })
                    flash(message, 'warning')
                    return render_template('admin/category/create.html', form=form)
            else:
                # 表单验证失败
                current_app.logger.debug(f'表单验证失败: {form.errors}')
                if is_ajax():
                    return jsonify({
                        'success': False,
                        'message': '表单验证失败，请检查输入',
                        'errors': form.errors
                    })
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{getattr(form, field).label.text}: {error}', 'error')
                return render_template('admin/category/create.html', form=form)
                
        except Exception as e:
            current_app.logger.error(f'创建分类时发生错误: {str(e)}')
            db.session.rollback()
            message = '创建分类时发生错误，请稍后重试'
            if is_ajax():
                return jsonify({
                    'success': False, 
                    'message': message
                })
            flash(message, 'error')
            return render_template('admin/category/create.html', form=form)
            
    return render_template('admin/category/create.html', form=form)

@category_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """编辑分类"""
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    
    if request.method == 'POST':
        current_app.logger.debug(f'表单数据: {request.form}')
        current_app.logger.debug(f'表单验证结果: {form.validate()}')
        current_app.logger.debug(f'表单验证结果(validate_on_submit): {form.validate_on_submit()}')
        current_app.logger.debug(f'CSRF Token: {request.form.get("csrf_token")}')
        current_app.logger.debug(f'请求头: {dict(request.headers)}')
        
        if form.errors:
            current_app.logger.debug(f'表单错误: {form.errors}')
            
        try:
            if form.validate_on_submit():
                current_app.logger.debug('表单验证通过，开始处理数据')
                # 检查分类名是否已存在（排除当前分类）
                existing_name = Category.query.filter(
                    Category.name == form.name.data,
                    Category.id != id
                ).first()
                if existing_name:
                    message = '分类名称已存在，请使用其他名称'
                    if is_ajax():
                        return jsonify({'success': False, 'message': message, 'errors': {'name': [message]}})
                    flash(message, 'warning')
                    return render_template('admin/category/edit.html', form=form, category=category)
                
                # 处理别名
                slug = form.slug.data.strip() if form.slug.data else None
                current_app.logger.debug(f'处理后的别名: {slug}')
                
                # 如果提供了有效的slug，检查是否已存在（排除当前分类）
                if slug:
                    existing_slug = Category.query.filter(
                        Category.slug == slug,
                        Category.id != id
                    ).first()
                    if existing_slug:
                        message = '分类别名已存在，请使用其他别名'
                        if is_ajax():
                            return jsonify({'success': False, 'message': message, 'errors': {'slug': [message]}})
                        flash(message, 'warning')
                        return render_template('admin/category/edit.html', form=form, category=category)
                
                try:
                    category.name = form.name.data
                    category.slug = slug
                    category.description = form.description.data
                    db.session.commit()
                    current_app.logger.debug('分类更新成功')
                    
                    message = '分类更新成功'
                    if is_ajax():
                        return jsonify({
                            'success': True,
                            'message': message,
                            'redirect_url': url_for('.index')
                        })
                    flash(message, 'success')
                    return redirect(url_for('.index'))
                except IntegrityError as e:
                    db.session.rollback()
                    current_app.logger.error(f'数据库错误: {str(e)}')
                    message = '更新分类失败，请稍后重试'
                    if is_ajax():
                        return jsonify({
                            'success': False,
                            'message': message,
                            'errors': {'_error': [message]}
                        })
                    flash(message, 'warning')
                    return render_template('admin/category/edit.html', form=form, category=category)
            else:
                # 表单验证失败
                current_app.logger.debug(f'表单验证失败: {form.errors}')
                if is_ajax():
                    return jsonify({
                        'success': False,
                        'message': '表单验证失败，请检查输入',
                        'errors': form.errors
                    })
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{getattr(form, field).label.text}: {error}', 'error')
                return render_template('admin/category/edit.html', form=form, category=category)
                
        except Exception as e:
            current_app.logger.error(f'更新分类时发生错误: {str(e)}')
            db.session.rollback()
            message = '更新分类时发生错误，请稍后重试'
            if is_ajax():
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')
            return render_template('admin/category/edit.html', form=form, category=category)
    
    return render_template('admin/category/edit.html', form=form, category=category)

@category_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """删除分类"""
    try:
        result = category_service.delete_category(id)
        if result['status'] == 'success':
            if is_ajax():
                return jsonify({'success': True, 'message': '分类删除成功'})
            flash('分类删除成功', 'success')
        else:
            if is_ajax():
                return jsonify({'success': False, 'message': result['message']})
            flash(result['message'], 'error')
    except Exception as e:
        current_app.logger.error(f'删除分类失败：{str(e)}')
        if is_ajax():
            return jsonify({'success': False, 'message': '删除分类失败'})
        flash('删除分类失败', 'error')
    
    return redirect(url_for('admin.admin_category.index'))

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