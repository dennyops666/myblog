"""
文件名：post.py
描述：文章管理控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, make_response
from flask_login import login_required, current_user
from app.services import PostService, CategoryService, TagService
from app.models.post import PostStatus, Post
from app.models.tag import Tag
from app.models.category import Category
from app.extensions import db
from app.forms.post_form import PostForm
from datetime import datetime

post_bp = Blueprint('posts', __name__)
post_service = PostService()
category_service = CategoryService()
tag_service = TagService()

@post_bp.route('/')
@login_required
def index():
    """文章列表页面"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', 'all')
        
        current_app.logger.debug(f"Requested status: {status}")
        current_app.logger.debug(f"Available PostStatus values: {[e.value for e in PostStatus]}")
        
        # 强制刷新数据库会话，确保获取最新数据
        db.session.expire_all()
        
        # 使用 joinedload 预加载关联数据
        query = Post.query.options(
            db.joinedload(Post.category),
            db.joinedload(Post.author)
        )
        
        # 添加状态过滤
        if status != 'all':
            try:
                # 遍历枚举值找到匹配的状态
                for status_enum in PostStatus:
                    current_app.logger.debug(f"Checking status_enum: {status_enum.name} = {status_enum.value}")
                    if status_enum.value == status:
                        current_app.logger.debug(f"Found matching status: {status_enum}")
                        query = query.filter(Post.status == status_enum)
                        break
                else:
                    current_app.logger.warning(f"Invalid status value: {status}")
                    flash('无效的状态值', 'error')
                    return redirect(url_for('admin.index'))
            except Exception as e:
                current_app.logger.warning(f"Error processing status filter: {str(e)}")
                flash('处理状态过滤时出错', 'error')
                return redirect(url_for('admin.index'))
        
        # 获取所有文章的状态进行调试
        all_posts = Post.query.all()
        for post in all_posts:
            current_app.logger.debug(f"Post {post.id} status: {post.status}")
            
        # 按创建时间倒序排序并执行分页
        posts = query.order_by(Post.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 确保所有关联数据都被加载
        if posts.items:
            for post in posts.items:
                db.session.refresh(post)
                if post.category:
                    db.session.refresh(post.category)
                if post.author:
                    db.session.refresh(post.author)
        
        # 提交会话以确保所有更改都被保存
        db.session.commit()
        
        # 设置响应头，禁止缓存
        response = make_response(render_template('admin/post/list.html', posts=posts, current_status=status))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except Exception as e:
        current_app.logger.error(f"获取文章列表失败: {str(e)}")
        current_app.logger.exception(e)
        flash('获取文章列表失败，请稍后重试', 'error')
        return redirect(url_for('admin.index'))

@post_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建文章"""
    form = PostForm()
    if request.method == 'POST':
        current_app.logger.info("开始处理文章创建请求...")
        current_app.logger.debug(f"表单数据: {request.form}")
        
        if form.validate_on_submit():
            try:
                # 根据表单中的状态值获取对应的枚举值
                for status_enum in PostStatus:
                    if status_enum.value == form.status.data:
                        status = status_enum
                        break
                else:
                    raise ValueError('无效的状态值')

                post = post_service.create_post(
                    title=form.title.data,
                    content=form.content.data,
                    author_id=current_user.id,
                    category_id=form.category_id.data,
                    tags=[Tag.query.get(tag_id) for tag_id in form.tags.data] if form.tags.data else None,
                    status=status
                )
                
                if post:  # 确保文章创建成功
                    if request.is_xhr:
                        current_app.logger.info("文章创建成功，返回JSON响应")
                        return jsonify({
                            'success': True,
                            'message': '文章创建成功',
                            'redirect_url': url_for('admin.posts.index')
                        })
                    
                    flash('文章创建成功', 'success')
                    return redirect(url_for('admin.posts.index'))
                else:
                    raise ValueError('文章创建失败')
                    
            except ValueError as e:
                current_app.logger.error(f"创建文章失败(ValueError): {str(e)}")
                if request.is_xhr:
                    return jsonify({
                        'success': False,
                        'message': str(e)
                    }), 400
                flash(str(e), 'error')
                return render_template('admin/post/create.html', form=form, tags=Tag.query.all())
                
            except Exception as e:
                current_app.logger.error(f"创建文章失败: {str(e)}")
                current_app.logger.exception(e)  # 记录完整的异常堆栈
                if request.is_xhr:
                    return jsonify({
                        'success': False,
                        'message': '创建文章失败，请稍后重试',
                        'error': str(e)
                    }), 500
                flash('创建文章失败，请稍后重试', 'error')
                return render_template('admin/post/create.html', form=form, tags=Tag.query.all())
        else:
            current_app.logger.warning(f"表单验证失败: {form.errors}")
            if request.is_xhr:
                return jsonify({
                    'success': False,
                    'message': '表单验证失败',
                    'errors': form.errors
                }), 400
                
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'error')
            return render_template('admin/post/create.html', form=form, tags=Tag.query.all())
            
    return render_template('admin/post/create.html', form=form, tags=Tag.query.all())

@post_bp.route('/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    """编辑文章"""
    post = Post.query.get_or_404(post_id)
    form = PostForm(obj=post)
    form.available_tags = [(str(tag.id), tag.name) for tag in Tag.query.order_by(Tag.name).all()]
    
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # 更新文章基本信息（除了标签）
                post.title = form.title.data
                post.content = form.content.data
                post.category_id = form.category_id.data
                
                # 根据表单中的状态值获取对应的枚举值
                for status_enum in PostStatus:
                    if status_enum.value == form.status.data:
                        post.status = status_enum
                        break
                else:
                    raise ValueError('无效的状态值')
                    
                post.summary = form.summary.data
                
                # 处理标签
                new_tags = []
                if form.tags.data:
                    tag_ids = form.tags.data.split(',')
                    for tag_id in tag_ids:
                        # 如果是数字ID，查找现有标签
                        if tag_id.isdigit():
                            tag = Tag.query.get(int(tag_id))
                            if tag:
                                new_tags.append(tag)
                        else:
                            # 如果是新标签名称，创建新标签
                            tag = Tag.query.filter_by(name=tag_id).first()
                            if not tag:
                                tag = Tag(name=tag_id)
                                db.session.add(tag)
                            new_tags.append(tag)
                
                # 更新文章的标签关系
                post.tags = new_tags
                
                # 保存所有更改
                db.session.commit()
                
                if request.is_xhr:
                    return jsonify({
                        'success': True,
                        'message': '文章更新成功',
                        'redirect_url': url_for('admin.posts.index')
                    })
                flash('文章更新成功', 'success')
                return redirect(url_for('admin.posts.index'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'更新文章失败: {str(e)}')
                if request.is_xhr:
                    return jsonify({
                        'success': False,
                        'message': '更新文章失败'
                    }), 500
                flash('更新文章失败', 'error')
                return redirect(url_for('admin.posts.edit', post_id=post.id))
        else:
            if request.is_xhr:
                return jsonify({
                    'success': False,
                    'message': '表单验证失败',
                    'errors': form.errors
                }), 400
    
    # 设置当前标签
    form.tags.data = ','.join([str(tag.id) for tag in post.tags])
    
    return render_template('admin/post/edit.html', form=form, post=post)

@post_bp.route('/<int:post_id>/delete', methods=['POST'])
@login_required
def delete(post_id):
    """删除文章"""
    try:
        # 从 JSON 请求中获取 CSRF token
        csrf_token = request.get_json().get('csrf_token')
        if not csrf_token:
            return jsonify({
                'success': False,
                'message': 'CSRF token 不能为空'
            }), 400

        result = post_service.delete_post(post_id)
        if result['status'] == 'success':
            return jsonify({
                'success': True,
                'message': '文章删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
    except Exception as e:
        current_app.logger.error(f"删除文章失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '删除文章失败，请稍后重试'
        }), 500

@post_bp.route('/<int:post_id>/view')
@login_required
def view(post_id):
    """查看文章"""
    post = Post.query.options(
        db.joinedload(Post.category),
        db.joinedload(Post.author),
        db.joinedload(Post.tags)
    ).get_or_404(post_id)
    
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
    try:
        content = request.json.get('content', '')
        if not content:
            return jsonify({
                'success': True,
                'html': ''
            })
        
        html_content = Post.render_markdown(content)
        current_app.logger.debug(f"预览内容长度: {len(html_content)}")
        
        return jsonify({
            'success': True,
            'html': html_content
        })
    except Exception as e:
        current_app.logger.error(f"预览文章内容时发生错误: {str(e)}")
        current_app.logger.exception(e)
        return jsonify({
            'success': False,
            'message': '预览失败，请稍后重试'
        }), 500