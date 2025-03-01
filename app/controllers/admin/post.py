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

post_bp = Blueprint('post', __name__, url_prefix='/posts')
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
        
        # 强制刷新数据库会话，确保获取最新数据
        db.session.expire_all()
        
        # 使用 joinedload 预加载关联数据
        query = Post.query.options(
            db.joinedload(Post.category),
            db.joinedload(Post.author)
        )
        
        # 添加状态过滤
        if status != 'all':
            query = query.filter(Post.status == status)
            
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
        response = make_response(render_template('admin/post/list.html', posts=posts))
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
                status = PostStatus(form.status.data)
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
                            'redirect_url': url_for('admin.post.index')
                        })
                    
                    flash('文章创建成功', 'success')
                    return redirect(url_for('admin.post.index'))
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
                return render_template('admin/post/create.html', form=form)
                
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
                return render_template('admin/post/create.html', form=form)
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
            return render_template('admin/post/create.html', form=form)
            
    return render_template('admin/post/create.html', form=form)

@post_bp.route('/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    """编辑文章"""
    current_app.logger.info(f"开始处理文章编辑请求，文章ID: {post_id}")
    current_app.logger.debug(f"请求方法: {request.method}")
    
    if request.method == 'POST':
        current_app.logger.info("收到POST请求，记录原始表单数据...")
        current_app.logger.debug(f"原始表单数据: {request.form.to_dict()}")
    
    # 获取文章并预加载关联数据
    post = Post.query.options(
        db.joinedload(Post.category),
        db.joinedload(Post.tags)
    ).get(post_id)
    
    if not post:
        current_app.logger.warning(f"文章不存在，ID: {post_id}")
        if request.is_xhr:
            return jsonify({'success': False, 'message': '文章不存在'}), 404
        flash('文章不存在', 'error')
        return redirect(url_for('admin.post.index'))
        
    form = PostForm(obj=post)
    form.obj = post  # 用于标题唯一性验证
    
    if request.method == 'POST':
        current_app.logger.info("开始验证表单数据...")
        current_app.logger.debug(f"表单对象数据: category_id={form.category_id.data}, status={form.status.data}")
        current_app.logger.debug(f"请求表单数据: category_id={request.form.get('category_id')}, status={request.form.get('status')}")
        
        if form.validate_on_submit():
            try:
                current_app.logger.info("表单验证通过，开始更新文章...")
                status = PostStatus(form.status.data)
                category_id = int(request.form.get('category_id')) if request.form.get('category_id') else None
                
                # 记录更新前的文章信息
                current_app.logger.debug(f"更新前的文章信息: 标题={post.title}, 分类ID={post.category_id}, 状态={post.status}")
                current_app.logger.debug(f"准备更新的数据: category_id={category_id}, status={status}")
                
                # 强制刷新数据库会话
                db.session.expire_all()
                db.session.commit()
                
                updated_post = post_service.update_post(
                    post_id=post_id,
                    title=form.title.data,
                    content=form.content.data,
                    summary=form.summary.data,
                    category_id=category_id,
                    tags=[Tag.query.get(tag_id) for tag_id in form.tags.data],
                    status=status
                )
                
                if updated_post:
                    current_app.logger.info(f"文章更新成功，ID: {post_id}")
                    # 记录更新后的文章信息
                    current_app.logger.debug(f"更新后的文章信息: 标题={updated_post.title}, 分类ID={updated_post.category_id}, 状态={updated_post.status}")
                    
                    # 强制刷新更新后的文章对象
                    db.session.refresh(updated_post)
                    if updated_post.category:
                        db.session.refresh(updated_post.category)
                    
                    if request.is_xhr:
                        return jsonify({
                            'success': True,
                            'message': '文章更新成功',
                            'redirect_url': url_for('admin.post.index', _t=datetime.now().timestamp())
                        })
                    flash('文章更新成功', 'success')
                    return redirect(url_for('admin.post.index', _t=datetime.now().timestamp()))
                else:
                    current_app.logger.error("文章更新失败：update_post 返回 None")
                    if request.is_xhr:
                        return jsonify({
                            'success': False,
                            'message': '文章更新失败'
                        }), 400
                    flash('文章更新失败', 'error')
                    return render_template('admin/post/edit.html', form=form, post=post)
                    
            except (ValueError, TypeError) as e:
                error_message = f'表单数据无效: {str(e)}'
                current_app.logger.error(f"更新文章失败(ValueError/TypeError): {str(e)}")
                if request.is_xhr:
                    return jsonify({
                        'success': False,
                        'message': error_message
                    }), 400
                flash(error_message, 'error')
                return render_template('admin/post/edit.html', form=form, post=post)
                
            except Exception as e:
                error_message = '更新文章失败，请稍后重试'
                current_app.logger.error(f"更新文章失败(未知错误): {str(e)}")
                current_app.logger.exception(e)  # 记录完整的异常堆栈
                if request.is_xhr:
                    return jsonify({
                        'success': False,
                        'message': error_message,
                        'error': str(e)
                    }), 500
                flash(error_message, 'error')
                return render_template('admin/post/edit.html', form=form, post=post)
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
            return render_template('admin/post/edit.html', form=form, post=post)
    
    # 获取分类和标签数据
    categories = Category.query.all()
    tags = Tag.query.all()
    current_app.logger.debug(f"加载表单数据: {len(categories)} 个分类, {len(tags)} 个标签")
    
    return render_template('admin/post/edit.html', form=form, post=post, categories=categories, tags=tags)

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