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

tag_bp = Blueprint('tag', __name__, url_prefix='/tag')
tag_service = TagService()

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
    if form.validate_on_submit():
        try:
            tag = Tag(
                name=form.name.data,
                slug=form.slug.data,
                description=form.description.data
            )
            db.session.add(tag)
            db.session.commit()
            flash('标签创建成功', 'success')
            return redirect(url_for('.index'))
        except Exception as e:
            db.session.rollback()
            flash(str(e), 'error')
            return render_template('admin/tag/create.html', form=form)
    return render_template('admin/tag/create.html', form=form)

@tag_bp.route('/<int:tag_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(tag_id):
    """编辑标签"""
    tag = tag_service.get_tag_by_id(tag_id)
    if not tag:
        flash('标签不存在', 'error')
        return redirect(url_for('admin.tag.index'))
        
    form = TagForm(obj=tag)
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                result = tag_service.update_tag(
                    tag_id=tag_id,
                    name=form.name.data,
                    slug=form.slug.data,
                    description=form.description.data
                )
                if result['status'] == 'success':
                    flash(result['message'], 'success')
                    return redirect(url_for('admin.tag.index'))
                else:
                    flash(result['message'], 'error')
            except Exception as e:
                flash(str(e), 'error')
            return redirect(url_for('admin.tag.index'))
        else:
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
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'error')
    except Exception as e:
        flash(str(e), 'error')
    return redirect(url_for('admin.tag.index')) 