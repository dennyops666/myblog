"""
文件名：category.py
描述：分类管理控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required
from app.services import get_category_service
from app.extensions import db
from app.forms.category_form import CategoryForm
from app.models.category import Category
from sqlalchemy.exc import IntegrityError
import logging
from app.utils.slug import generate_slug
from app.models.post import Post
import traceback

# 创建Blueprint
category_bp = Blueprint('category', __name__)

# 获取服务实例
category_service = get_category_service()

def is_ajax():
    """检查是否是 AJAX 请求"""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

@category_bp.route('/')
@login_required
def index():
    """分类列表页面"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 获取分类列表
        pagination = Category.query.order_by(Category.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        categories = pagination.items
        
        # 记录日志
        current_app.logger.info(f"获取到{len(categories)}个分类")
        
        # Category模型已经有post_count属性，不需要手动计算
        
        return render_template('admin/category/list.html', 
                             categories=categories, 
                             pagination=pagination)
    except Exception as e:
        current_app.logger.error(f"获取分类列表失败: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        flash('获取分类列表失败，请稍后重试', 'error')
        return render_template('admin/category/list.html', 
                             categories=[], 
                             pagination=None)

@category_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建分类"""
    if request.method == 'GET':
        return render_template('admin/category/create.html')
    
    try:
        # 获取并验证数据
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip()
        description = request.form.get('description', '').strip()
        
        # 验证必填字段
        if not name:
            return jsonify({
                'success': False,
                'message': '分类名称不能为空'
            })
        
        # 检查名称是否已存在
        if Category.query.filter_by(name=name).first():
            return jsonify({
                'success': False,
                'message': '该分类名称已存在'
            })
        
        # 处理 slug
        if slug:
            # 检查 slug 是否已存在
            if Category.query.filter_by(slug=slug).first():
                return jsonify({
                    'success': False,
                    'message': '该分类别名已存在'
                })
        else:
            # 自动生成 slug
            slug = generate_slug(name)
            # 确保生成的 slug 不重复
            base_slug = slug
            counter = 1
            while Category.query.filter_by(slug=slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
        
        # 创建分类
        category = Category(
            name=name,
            slug=slug,
            description=description if description else None
        )
        db.session.add(category)
        db.session.commit()
        
        # 记录日志
        current_app.logger.info(f'分类创建成功：{name}')
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'message': '分类创建成功！',
            'redirect_url': url_for('admin_dashboard.category.index')
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建分类时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '服务器错误，请稍后重试'
        })

@category_bp.route('/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(category_id):
    """编辑分类"""
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'GET':
        form = CategoryForm(obj=category)
        return render_template('admin/category/edit.html', category=category, form=form, is_edit=True)
    
    try:
        # 获取并验证数据
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip()
        description = request.form.get('description', '').strip()
        
        # 验证必填字段
        if not name:
            return jsonify({
                'success': False,
                'message': '分类名称不能为空'
            })
        
        # 检查名称是否已存在（排除当前分类）
        existing_name = Category.query.filter(
            Category.name == name,
            Category.id != category_id
        ).first()
        if existing_name:
            return jsonify({
                'success': False,
                'message': '该分类名称已存在'
            })
        
        # 处理 slug
        if slug:
            # 检查 slug 是否已存在（排除当前分类）
            existing_slug = Category.query.filter(
                Category.slug == slug,
                Category.id != category_id
            ).first()
            if existing_slug:
                return jsonify({
                    'success': False,
                    'message': '该分类别名已存在'
                })
        else:
            # 自动生成 slug
            slug = generate_slug(name)
            # 确保生成的 slug 不重复
            base_slug = slug
            counter = 1
            while Category.query.filter(
                Category.slug == slug,
                Category.id != category_id
            ).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
        
        # 更新分类
        category.name = name
        category.slug = slug
        category.description = description if description else None
        
        db.session.commit()
        
        # 记录日志
        current_app.logger.info(f'分类更新成功：{name}')
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'message': '分类更新成功！',
            'redirect_url': url_for('admin_dashboard.category.index')
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新分类时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '服务器错误，请稍后重试'
        })

@category_bp.route('/<int:category_id>/delete', methods=['POST'])
@login_required
def delete(category_id):
    """删除分类"""
    category = Category.query.get_or_404(category_id)
    
    # 检查是否有关联的文章
    post_count = db.session.query(Post).filter_by(category_id=category_id).count()
    if post_count > 0:
        return jsonify({
            'success': False,
            'message': f'该分类下还有{post_count}篇文章，请先删除或移动这些文章后再删除分类。'
        })

    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '分类删除成功',
            'redirect_url': url_for('admin_dashboard.category.index')
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除分类时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '服务器错误，请稍后重试'
        })

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