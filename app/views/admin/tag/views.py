from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.models import Tag, Post, db
from app.forms.tag import TagCreateForm, TagEditForm
from app.utils.slug import generate_slug
from sqlalchemy import func

tag_bp = Blueprint('admin_tag', __name__)

@tag_bp.route('/tag')
@login_required
def tag_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取标签列表
    pagination = Tag.query.order_by(Tag.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    tags = pagination.items
    
    # 获取每个标签关联的文章数量
    tag_post_counts = {}
    tag_ids = [tag.id for tag in tags]
    if tag_ids:
        # 使用子查询统计每个标签的文章数
        tag_counts = db.session.query(
            Post.tags.any(Tag.id.in_(tag_ids)),
            func.count(Post.id)
        ).group_by(Post.tags.any(Tag.id.in_(tag_ids))).all()
        
        for tag_id, count in tag_counts:
            tag_post_counts[tag_id] = count
    
    return render_template('admin/tag/list.html', 
                          tags=tags, 
                          pagination=pagination,
                          tag_post_counts=tag_post_counts)

@tag_bp.route('/tag/create', methods=['GET', 'POST'])
@login_required
def tag_create():
    form = TagCreateForm()
    
    if form.validate_on_submit():
        tag = Tag()
        tag.name = form.name.data
        
        # 如果没有提供slug，则自动生成
        if form.slug.data:
            tag.slug = form.slug.data
        else:
            tag.slug = generate_slug(form.name.data)
        
        db.session.add(tag)
        db.session.commit()
        
        flash('标签创建成功', 'success')
        return redirect(url_for('admin_tag.tag_list'))
    
    return render_template('admin/tag/create.html', form=form)

@tag_bp.route('/tag/<int:tag_id>/edit', methods=['GET', 'POST'])
@login_required
def tag_edit(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    form = TagEditForm(tag_id=tag.id, obj=tag)
    
    # 获取标签关联的文章数量
    tag_post_count = Post.query.filter(Post.tags.any(Tag.id == tag.id)).count()
    
    if form.validate_on_submit():
        tag.name = form.name.data
        
        # 如果没有提供slug，则自动生成
        if form.slug.data:
            tag.slug = form.slug.data
        else:
            tag.slug = generate_slug(form.name.data)
        
        db.session.commit()
        
        flash('标签更新成功', 'success')
        return redirect(url_for('admin_tag.tag_list'))
    
    return render_template('admin/tag/edit.html', 
                          tag=tag, 
                          form=form,
                          tag_post_count=tag_post_count)

@tag_bp.route('/tag/<int:tag_id>/delete', methods=['POST'])
@login_required
def tag_delete(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    
    # 检查标签是否关联了文章
    post_count = Post.query.filter(Post.tags.any(Tag.id == tag.id)).count()
    if post_count > 0:
        flash(f'无法删除标签 "{tag.name}"，该标签下有 {post_count} 篇关联文章', 'error')
        return redirect(url_for('admin_tag.tag_list'))
    
    db.session.delete(tag)
    db.session.commit()
    
    flash(f'标签 "{tag.name}" 已成功删除', 'success')
    return redirect(url_for('admin_tag.tag_list')) 