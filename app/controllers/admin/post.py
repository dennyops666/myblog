"""
文件名：post.py
描述：文章管理控制器
作者：denny
创建日期：2025-02-16
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.services import PostService, CategoryService
from . import admin_bp

@admin_bp.route('/posts')
@login_required
def posts():
    """文章列表页面"""
    page = request.args.get('page', 1, type=int)
    posts = PostService.get_posts_by_page(page)
    return render_template('admin/post/list.html', posts=posts)

@admin_bp.route('/posts/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """创建文章"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id', type=int)
        summary = request.form.get('summary')
        status = request.form.get('status', type=int, default=0)
        
        if not all([title, content, category_id]):
            flash('请填写所有必填字段', 'danger')
        else:
            try:
                PostService.create_post(
                    title=title,
                    content=content,
                    category_id=category_id,
                    author_id=current_user.id,
                    summary=summary,
                    status=status
                )
                flash('文章创建成功', 'success')
                return redirect(url_for('admin.posts'))
            except Exception as e:
                flash(f'文章创建失败：{str(e)}', 'danger')
    
    categories = CategoryService.get_all_categories()
    return render_template('admin/post/create.html', categories=categories)

@admin_bp.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """编辑文章"""
    post = PostService.get_post_by_id(post_id)
    if not post:
        flash('文章不存在', 'danger')
        return redirect(url_for('admin.posts'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id', type=int)
        summary = request.form.get('summary')
        status = request.form.get('status', type=int, default=0)
        
        if not all([title, content, category_id]):
            flash('请填写所有必填字段', 'danger')
        else:
            try:
                PostService.update_post(
                    post,
                    title=title,
                    content=content,
                    category_id=category_id,
                    summary=summary,
                    status=status
                )
                flash('文章更新成功', 'success')
                return redirect(url_for('admin.posts'))
            except Exception as e:
                flash(f'文章更新失败：{str(e)}', 'danger')
    
    categories = CategoryService.get_all_categories()
    return render_template('admin/post/edit.html', post=post, categories=categories)

@admin_bp.route('/posts/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    """删除文章"""
    post = PostService.get_post_by_id(post_id)
    if not post:
        flash('文章不存在', 'danger')
    else:
        try:
            PostService.delete_post(post)
            flash('文章删除成功', 'success')
        except Exception as e:
            flash(f'文章删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('admin.posts'))

@admin_bp.route('/posts/upload-image', methods=['POST'])
@login_required
def upload_image():
    """上传图片"""
    if 'image' not in request.files:
        return jsonify({'error': '没有文件上传'}), 400
        
    file = request.files['image']
    if not file:
        return jsonify({'error': '文件为空'}), 400
        
    try:
        image_url = PostService.upload_image(file)
        return jsonify({'url': image_url})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': '上传失败'}), 500

@admin_bp.route('/posts/images/<int:post_id>', methods=['GET'])
@login_required
def get_post_images(post_id):
    """获取文章图片列表"""
    images = PostService.get_post_images(post_id)
    return jsonify({'images': images})

@admin_bp.route('/posts/images/<path:image_path>', methods=['DELETE'])
@login_required
def delete_image(image_path):
    """删除图片"""
    if PostService.delete_image(image_path):
        return jsonify({'message': '删除成功'})
    return jsonify({'error': '删除失败'}), 400 