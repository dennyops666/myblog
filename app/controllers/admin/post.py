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
        current_app.logger.info("开始加载文章列表...")
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', 'all')
        
        current_app.logger.debug(f"请求参数: page={page}, per_page={per_page}, status={status}")
        
        # 强制刷新数据库会话
        db.session.expire_all()
        db.session.commit()
        
        # 使用 joinedload 预加载所有关联数据
        query = Post.query.options(
            db.joinedload(Post.category),
            db.joinedload(Post.author),
            db.joinedload(Post.tags)  # 使用 joinedload 加载标签
        )
        
        # 添加状态过滤
        if status != 'all':
            try:
                for status_enum in PostStatus:
                    if status_enum.value == status:
                        query = query.filter(Post.status == status_enum)
                        break
            except Exception as e:
                current_app.logger.error(f"处理状态过滤时出错: {str(e)}")
                flash('处理状态过滤时出错', 'error')
                return redirect(url_for('admin.index'))
        
        # 按创建时间倒序排序并执行分页
        posts = query.order_by(Post.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 强制加载每篇文章的标签并记录日志
        for post in posts.items:
            db.session.refresh(post)  # 刷新文章对象
            if post.category:
                db.session.refresh(post.category)
            if post.author:
                db.session.refresh(post.author)
            for tag in post.tags:
                db.session.refresh(tag)  # 刷新每个标签对象
            current_app.logger.info(f"文章 {post.id} 的标签: {[tag.name for tag in post.tags]}")
        
        # 设置响应头，禁止缓存
        response = make_response(render_template('admin/post/list.html', posts=posts, current_status=status))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
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
    current_app.logger.info("开始加载分类选项...")
    categories = Category.query.all()
    current_app.logger.info(f"成功获取到 {len(categories)} 个分类")
    
    current_app.logger.info("开始加载标签选项...")
    tags = Tag.query.all()
    current_app.logger.info(f"成功获取到 {len(tags)} 个标签")
    
    form = PostForm()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    form.tags.choices = [(str(t.id), t.name) for t in tags]
    
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

                # 获取标签对象
                selected_tags = []
                if form.tags.data:
                    selected_tags = Tag.query.filter(Tag.id.in_([int(tag_id) for tag_id in form.tags.data])).all()

                post = post_service.create_post(
                    title=form.title.data,
                    content=form.content.data,
                    summary=form.summary.data,
                    author_id=current_user.id,
                    category_id=form.category_id.data,
                    tags=selected_tags,
                    status=status
                )
                
                if post:  # 确保文章创建成功
                    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                    if is_xhr:
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
                is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                if is_xhr:
                    return jsonify({
                        'success': False,
                        'message': str(e)
                    }), 400
                flash(str(e), 'error')
                return render_template('admin/post/create.html', form=form)
                
            except Exception as e:
                current_app.logger.error(f"创建文章失败: {str(e)}")
                current_app.logger.exception(e)  # 记录完整的异常堆栈
                is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                if is_xhr:
                    return jsonify({
                        'success': False,
                        'message': '创建文章失败，请稍后重试',
                        'error': str(e)
                    }), 500
                flash('创建文章失败，请稍后重试', 'error')
                return render_template('admin/post/create.html', form=form)
        else:
            current_app.logger.warning(f"表单验证失败: {form.errors}")
            is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_xhr:
                return jsonify({
                    'success': False,
                    'message': '表单验证失败',
                    'errors': form.errors
                }), 400
                
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'error')
            return render_template('admin/post/create.html', form=form)
            
    return render_template('admin/post/create.html', form=form)

@post_bp.route('/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    """编辑文章"""
    try:
        current_app.logger.info("开始加载分类选项...")
        categories = Category.query.all()
        current_app.logger.info(f"成功获取到 {len(categories)} 个分类")
        
        current_app.logger.info("开始加载标签选项...")
        tags = Tag.query.all()
        current_app.logger.info(f"成功获取到 {len(tags)} 个标签")
        
        # 使用 joinedload 预加载所有关联数据
        post = Post.query.options(
            db.joinedload(Post.category),
            db.joinedload(Post.tags),
            db.joinedload(Post.author)
        ).get_or_404(post_id)
        
        form = PostForm(obj=post)
        form.category_id.choices = [(c.id, c.name) for c in categories]
        form.tags.choices = [(str(t.id), t.name) for t in tags]
        
        if request.method == 'POST':
            current_app.logger.info("开始处理文章更新请求...")
            current_app.logger.debug(f"表单数据: {request.form}")
            
            if form.validate_on_submit():
                try:
                    # 处理标签数据
                    selected_tags = form.process_tags()
                    current_app.logger.info(f"处理后的标签: {[tag.name for tag in selected_tags]}")
                    
                    # 根据表单中的状态值获取对应的枚举值
                    for status_enum in PostStatus:
                        if status_enum.value == form.status.data:
                            status = status_enum
                            break
                    else:
                        raise ValueError('无效的状态值')
                    
                    # 更新文章
                    post = post_service.update_post(
                        post_id=post_id,
                        title=form.title.data,
                        content=form.content.data,
                        summary=form.summary.data,
                        category_id=form.category_id.data,
                        tags=selected_tags,
                        status=status
                    )
                    
                    if post:  # 确保文章更新成功
                        is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                        if is_xhr:
                            current_app.logger.info("文章更新成功，返回JSON响应")
                            return jsonify({
                                'success': True,
                                'message': '文章更新成功',
                                'redirect_url': url_for('admin.posts.index')
                            })
                        
                        flash('文章更新成功', 'success')
                        return redirect(url_for('admin.posts.index'))
                    else:
                        raise ValueError('文章更新失败')
                        
                except ValueError as e:
                    current_app.logger.error(f"更新文章失败(ValueError): {str(e)}")
                    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                    if is_xhr:
                        return jsonify({
                            'success': False,
                            'message': str(e)
                        }), 400
                    flash(str(e), 'error')
                    return render_template('admin/post/edit.html', form=form, post=post)
                    
                except Exception as e:
                    current_app.logger.error(f"更新文章失败: {str(e)}")
                    current_app.logger.exception(e)
                    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                    if is_xhr:
                        return jsonify({
                            'success': False,
                            'message': '更新文章失败，请稍后重试'
                        }), 500
                    flash('更新文章失败，请稍后重试', 'error')
                    return render_template('admin/post/edit.html', form=form, post=post)
            else:
                current_app.logger.warning(f"表单验证失败: {form.errors}")
                is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                if is_xhr:
                    return jsonify({
                        'success': False,
                        'message': '表单验证失败',
                        'errors': form.errors
                    }), 400
                    
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{getattr(form, field).label.text}: {error}', 'error')
                return render_template('admin/post/edit.html', form=form, post=post)
                
        # 设置初始标签数据
        if post.tags:
            form.tags.data = [str(tag.id) for tag in post.tags]
            current_app.logger.info(f"设置初始标签: {form.tags.data}")
                
        return render_template('admin/post/edit.html', form=form, post=post)
        
    except Exception as e:
        current_app.logger.error(f"编辑文章失败: {str(e)}")
        current_app.logger.exception(e)
        is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_xhr:
            return jsonify({
                'success': False,
                'message': '编辑文章失败，请稍后重试'
            }), 500
        flash('编辑文章失败，请稍后重试', 'error')
        return redirect(url_for('admin.posts.index'))

@post_bp.route('/<int:post_id>/delete', methods=['POST'])
@login_required
def delete(post_id):
    """删除文章"""
    try:
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
    try:
        post = Post.query.options(
            db.joinedload(Post.category),
            db.joinedload(Post.author),
            db.joinedload(Post.tags)
        ).get_or_404(post_id)
        
        # 刷新所有关联数据
        db.session.refresh(post)
        if post.category:
            db.session.refresh(post.category)
        if post.author:
            db.session.refresh(post.author)
        for tag in post.tags:
            db.session.refresh(tag)
        
        return render_template('admin/post/view.html', post=post)
    except Exception as e:
        current_app.logger.error(f"查看文章失败: {str(e)}")
        current_app.logger.exception(e)
        flash('查看文章失败，请稍后重试', 'error')
        return redirect(url_for('admin.posts.index'))

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

@post_bp.route('/search_tags')
@login_required
def search_tags():
    """搜索标签"""
    try:
        query = request.args.get('q', '')
        page = request.args.get('page', 1, type=int)
        per_page = 30
        
        # 查询标签
        tags_query = Tag.query
        if query:
            tags_query = tags_query.filter(Tag.name.ilike(f'%{query}%'))
        
        # 获取总数
        total_count = tags_query.count()
        
        # 分页
        tags = tags_query.order_by(Tag.name).offset((page - 1) * per_page).limit(per_page).all()
        
        # 格式化结果
        items = [{'id': str(tag.id), 'text': tag.name} for tag in tags]
        
        return jsonify({
            'items': items,
            'total_count': total_count
        })
        
    except Exception as e:
        current_app.logger.error(f"搜索标签失败: {str(e)}")
        current_app.logger.exception(e)
        return jsonify({
            'items': [],
            'total_count': 0
        }), 500