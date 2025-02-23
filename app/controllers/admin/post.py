"""
文件名：post.py
描述：文章管理控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.services import PostService, CategoryService, TagService
from app.models.post import PostStatus, Post
from app.models.tag import Tag
from app.extensions import db
from app.forms.post_form import PostForm

post_bp = Blueprint('post', __name__, url_prefix='/post')
post_service = PostService()
category_service = CategoryService()
tag_service = TagService()

@post_bp.route('/')
@login_required
def index():
    """文章列表页面"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', 'all')
    
    query = Post.query
    
    # 根据状态筛选
    if status != 'all':
        try:
            query = query.filter(Post.status == PostStatus(status))
        except ValueError:
            pass
    
    # 排序
    query = query.order_by(Post.created_at.desc())
    
    # 分页
    posts = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    return render_template('admin/post/list.html', posts=posts, current_status=status)

@post_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建文章"""
    form = PostForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                status = PostStatus(form.status.data)
                post = post_service.create_post(
                    title=form.title.data,
                    content=form.content.data,
                    author_id=current_user.id,
                    category_id=form.category_id.data,
                    tags=[Tag.query.get(tag_id) for tag_id in form.tags.data],
                    status=status
                )
                flash('文章创建成功', 'success')
                return redirect(url_for('admin.post.index'))
            except Exception as e:
                flash(str(e), 'error')
                return render_template('admin/post/create.html', form=form)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'error')
            return render_template('admin/post/create.html', form=form)
    return render_template('admin/post/create.html', form=form)

@post_bp.route('/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    """编辑文章"""
    post = post_service.get_post(post_id)
    if not post:
        flash('文章不存在', 'error')
        return redirect(url_for('admin.post.index'))
        
    form = PostForm(obj=post)
    if request.method == 'POST' and form.validate_on_submit():
        try:
            status = PostStatus(form.status.data)
            post = post_service.update_post(
                post_id=post_id,
                title=form.title.data,
                content=form.content.data,
                summary=form.summary.data,
                category_id=form.category_id.data,
                tags=[Tag.query.get(tag_id) for tag_id in form.tags.data],
                status=status
            )
            if post:
                flash('文章更新成功', 'success')
                return redirect(url_for('admin.post.index'))
            else:
                flash('文章更新失败', 'error')
        except Exception as e:
            flash(str(e), 'error')
        return redirect(url_for('admin.post.index'))
    return render_template('admin/post/edit.html', form=form, post=post)

@post_bp.route('/<int:post_id>/delete', methods=['POST'])
@login_required
def delete(post_id):
    """删除文章"""
    try:
        post_service.delete_post(post_id)
        flash('文章删除成功', 'success')
    except Exception as e:
        flash(str(e), 'error')
    return redirect(url_for('admin.post.index'))

@post_bp.route('/<int:post_id>/view')
@login_required
def view(post_id):
    """查看文章"""
    post = post_service.get_post(post_id)
    if not post:
        flash('文章不存在', 'error')
        return redirect(url_for('admin.post.index'))
    return render_template('admin/post/view.html', post=post)

@post_bp.route('/<int:post_id>/status', methods=['POST'])
@login_required
def change_status(post_id):
    """修改文章状态"""
    try:
        status = request.form.get('status')
        if not status:
            return jsonify({'success': False, 'message': '状态不能为空'}), 400
            
        post = post_service.update_post(
            post_id=post_id,
            status=PostStatus(status)
        )
        
        if post:
            return jsonify({
                'success': True,
                'message': '状态更新成功',
                'status': post.status.value
            })
        return jsonify({'success': False, 'message': '文章不存在'}), 404
    except ValueError:
        return jsonify({'success': False, 'message': '无效的状态值'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@post_bp.route('/preview', methods=['POST'])
@login_required
def preview():
    """处理文章预览请求"""
    content = request.json.get('content', '')
    if not content:
        return jsonify({'html': ''})
    
    try:
        html_content = Post.render_markdown(content)
        return jsonify({
            'success': True,
            'html': html_content
        })
    except Exception as e:
        current_app.logger.error(f"预览文章内容时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '预览失败，请稍后重试'
        }), 500