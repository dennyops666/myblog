"""
文件名：tag.py
描述：标签管理控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.services import TagService
from app.extensions import db
from app.forms.tag_form import TagForm
from app.models.tag import Tag
from sqlalchemy.exc import IntegrityError

tag_bp = Blueprint('tag', __name__, url_prefix='/tag')
tag_service = TagService()

def is_xhr():
    """检查是否是 AJAX 请求"""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

@tag_bp.route('/')
@login_required
def index():
    """标签列表页面"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 获取标签列表
    pagination = tag_service.get_tag_list(page=page, per_page=per_page)
    
    # 获取标签统计信息
    stats = tag_service.get_tag_stats()
    
    return render_template('admin/tag/list.html', 
                         pagination=pagination,
                         stats=stats)

@tag_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建标签"""
    form = TagForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # 检查标签名是否已存在
                existing_tag = Tag.query.filter_by(name=form.name.data).first()
                if existing_tag:
                    if is_xhr():
                        return jsonify({
                            'success': False,
                            'message': '标签名称已存在，请使用其他名称',
                            'errors': {'name': ['标签名称已存在，请使用其他名称']}
                        })
                    flash('标签名称已存在，请使用其他名称', 'warning')
                    return render_template('admin/tag/create.html', form=form)
                
                # 检查别名是否已存在
                if form.slug.data:  # 只在提供别名时检查
                    existing_slug = Tag.query.filter_by(slug=form.slug.data).first()
                    if existing_slug:
                        if is_xhr():
                            return jsonify({
                                'success': False,
                                'message': '标签别名已存在，请使用其他别名',
                                'errors': {'slug': ['标签别名已存在，请使用其他别名']}
                            })
                        flash('标签别名已存在，请使用其他别名', 'warning')
                        return render_template('admin/tag/create.html', form=form)
                
                tag = Tag(
                    name=form.name.data,
                    slug=form.slug.data,
                    description=form.description.data
                )
                db.session.add(tag)
                db.session.commit()
                
                if is_xhr():
                    return jsonify({
                        'success': True,
                        'message': '标签创建成功',
                        'redirect_url': url_for('.index')
                    })
                flash('标签创建成功', 'success')
                return redirect(url_for('.index'))
                
            except IntegrityError:
                db.session.rollback()
                if is_xhr():
                    return jsonify({
                        'success': False,
                        'message': '标签名称或别名已存在，请修改后重试'
                    })
                flash('标签名称或别名已存在，请修改后重试', 'warning')
                return render_template('admin/tag/create.html', form=form)
                
            except Exception as e:
                db.session.rollback()
                if is_xhr():
                    return jsonify({
                        'success': False,
                        'message': '创建标签时发生错误，请稍后重试'
                    })
                flash('创建标签时发生错误，请稍后重试', 'error')
                return render_template('admin/tag/create.html', form=form)
        else:
            if is_xhr():
                return jsonify({
                    'success': False,
                    'message': '表单验证失败',
                    'errors': {field: errors for field, errors in form.errors.items()}
                })
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'error')
            
    return render_template('admin/tag/create.html', form=form)

@tag_bp.route('/<int:tag_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(tag_id):
    """编辑标签"""
    tag = tag_service.get_tag_by_id(tag_id)
    if not tag:
        if is_xhr():
            return jsonify({
                'success': False,
                'message': '标签不存在'
            })
        flash('标签不存在', 'error')
        return redirect(url_for('admin.tag.index'))
        
    form = TagForm(obj=tag)
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # 检查名称是否已存在
                existing_tag = Tag.query.filter(
                    Tag.name == form.name.data,
                    Tag.id != tag_id
                ).first()
                if existing_tag:
                    if is_xhr():
                        return jsonify({
                            'success': False,
                            'message': '标签名称已存在，请使用其他名称',
                            'errors': {'name': ['标签名称已存在，请使用其他名称']}
                        })
                    flash('标签名称已存在，请使用其他名称', 'warning')
                    return render_template('admin/tag/edit.html', form=form, tag=tag)
                
                # 检查别名是否已存在
                if form.slug.data:
                    existing_slug = Tag.query.filter(
                        Tag.slug == form.slug.data,
                        Tag.id != tag_id
                    ).first()
                    if existing_slug:
                        if is_xhr():
                            return jsonify({
                                'success': False,
                                'message': '标签别名已存在，请使用其他别名',
                                'errors': {'slug': ['标签别名已存在，请使用其他别名']}
                            })
                        flash('标签别名已存在，请使用其他别名', 'warning')
                        return render_template('admin/tag/edit.html', form=form, tag=tag)
                
                # 更新标签
                tag.name = form.name.data
                tag.slug = form.slug.data
                tag.description = form.description.data
                db.session.commit()
                
                if is_xhr():
                    return jsonify({
                        'success': True,
                        'message': '标签更新成功',
                        'redirect_url': url_for('.index')
                    })
                flash('标签更新成功', 'success')
                return redirect(url_for('.index'))
                
            except IntegrityError:
                db.session.rollback()
                if is_xhr():
                    return jsonify({
                        'success': False,
                        'message': '标签名称或别名已存在，请修改后重试'
                    })
                flash('标签名称或别名已存在，请修改后重试', 'warning')
                return render_template('admin/tag/edit.html', form=form, tag=tag)
                
            except Exception as e:
                db.session.rollback()
                if is_xhr():
                    return jsonify({
                        'success': False,
                        'message': '更新标签时发生错误，请稍后重试'
                    })
                flash('更新标签时发生错误，请稍后重试', 'error')
                return render_template('admin/tag/edit.html', form=form, tag=tag)
        else:
            if is_xhr():
                return jsonify({
                    'success': False,
                    'message': '表单验证失败',
                    'errors': {field: errors for field, errors in form.errors.items()}
                })
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'error')
            
    return render_template('admin/tag/edit.html', form=form, tag=tag)

@tag_bp.route('/<int:tag_id>/delete', methods=['POST'])
@login_required
def delete(tag_id):
    """删除标签"""
    try:
        result = tag_service.delete_tag(tag_id)
        if result['status'] == 'success':
            if is_xhr():
                return jsonify({
                    'success': True,
                    'message': result['message']
                })
            flash(result['message'], 'success')
        else:
            if is_xhr():
                return jsonify({
                    'success': False,
                    'message': result['message']
                })
            flash(result['message'], 'error')
    except Exception as e:
        if is_xhr():
            return jsonify({
                'success': False,
                'message': str(e)
            })
        flash(str(e), 'error')
    return redirect(url_for('admin.tag.index')) 