"""
文件名：post.py
描述：文章管理视图
作者：denny
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app, make_response
from flask_login import login_required, current_user
from app.services import get_post_service, get_category_service, get_tag_service
from app.models.post import PostStatus, Post
from app.models.tag import Tag
from app.models.category import Category
from app.extensions import db
from app.forms.admin.post import PostForm
from datetime import datetime
import traceback
from sqlalchemy.exc import IntegrityError
from app.decorators import admin_required
from app.services.post import PostService
from app.services.category import CategoryService
from app.services.tag import TagService
from app.utils.file import allowed_file, save_file
import os

post_bp = Blueprint('post', __name__)

# 获取服务实例
post_service = get_post_service()
category_service = get_category_service()
tag_service = get_tag_service()

@post_bp.route('/')
@login_required
def index():
    """文章列表页面"""
    try:
        current_app.logger.info("开始加载文章列表...")
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', 'all')
        search_query = request.args.get('q', '').strip()
        
        current_app.logger.debug(f"请求参数: page={page}, per_page={per_page}, status={status}, q={search_query}")
        
        # 强制刷新数据库会话
        db.session.expire_all()
        db.session.commit()
        
        # 使用 joinedload 预加载所有关联数据
        query = Post.query.options(
            db.joinedload(Post.category),
            db.joinedload(Post.author),
            db.joinedload(Post.tags)  # 使用 joinedload 加载标签
        )
        
        # 添加搜索过滤
        if search_query:
            query = query.filter(Post.title.ilike(f'%{search_query}%'))
            current_app.logger.info(f"应用搜索过滤: '{search_query}'")
        
        # 添加状态过滤
        if status != 'all':
            try:
                for status_enum in PostStatus:
                    if status_enum.value == status:
                        query = query.filter(Post.status == status_enum)
                        current_app.logger.info(f"应用状态过滤: {status}")
                        break
            except Exception as e:
                current_app.logger.error(f"处理状态过滤时出错: {str(e)}")
                flash('处理状态过滤时出错', 'error')
                return redirect(url_for('.index'))
        
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
        return redirect(url_for('.index'))

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
    form.tags.choices = [(t.id, t.name) for t in tags]
    
    if request.method == 'POST':
        current_app.logger.info("开始处理文章创建请求...")
        current_app.logger.debug(f"表单数据: {request.form}")
        
        # 首先检查标题是否已存在
        title = request.form.get('title', '').strip()
        current_app.logger.info(f"检查标题是否存在: '{title}'")
        
        existing_post = Post.query.filter_by(title=title).first()
        if existing_post:
            current_app.logger.warning(f"标题已存在，ID: {existing_post.id}, 标题: '{existing_post.title}'")
            flash('标题已存在，请使用不同的标题', 'error')
            return render_template('admin/post/create.html', form=form)
        
        current_app.logger.info(f"标题可用: '{title}'")
        
        # 使用表单验证
        if form.validate_on_submit():
            try:
                # 处理标签数据
                selected_tags = form.process_tags()
                
                # 获取状态枚举值
                status = form.get_status()
                
                # 创建文章
                post = Post(
                    title=form.title.data,
                    content=form.content.data,
                    summary=form.summary.data,
                    author_id=current_user.id,
                    category_id=form.category_id.data,
                    status=status,
                    is_sticky=form.is_sticky.data,
                    is_private=form.is_private.data,
                    can_comment=form.can_comment.data
                )
                
                # 设置标签
                post.tags = selected_tags
                
                # 确保status和published字段一致
                post.update_status_consistency()
                
                # 保存到数据库
                db.session.add(post)
                db.session.commit()
                
                flash('文章创建成功', 'success')
                return redirect(url_for('.index'))
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"创建文章失败: {str(e)}")
                current_app.logger.exception(e)
                
                # 检查异常是否为数据库约束错误
                if 'UNIQUE constraint failed: posts.title' in str(e):
                    flash('标题已存在，请使用不同的标题', 'error')
                else:
                    flash(f'创建文章失败: {str(e)}', 'error')
        else:
            # 表单验证失败
            current_app.logger.error("表单验证失败")
            # 显示详细的表单错误信息
            for field_name, field_errors in form.errors.items():
                field_label = getattr(form, field_name).label.text if hasattr(getattr(form, field_name), 'label') else field_name
                for error in field_errors:
                    flash(f"{field_label}: {error}", 'error')
                    current_app.logger.error(f"表单验证错误: {field_name} - {error}")
            
            flash('表单验证失败，请检查输入', 'error')
        
        return render_template('admin/post/create.html', form=form)
            
    return render_template('admin/post/create.html', form=form)

@post_bp.route('/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    """编辑文章"""
    try:
        # 记录请求详情
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        current_app.logger.info(f"编辑文章请求 - ID: {post_id}, 方法: {request.method}, AJAX: {is_ajax}")
        
        if request.method == 'POST':
            # 检查和记录表单数据
            form_keys = list(request.form.keys())
            content_length = len(request.form.get('content', ''))
            current_app.logger.info(f"表单字段: {form_keys}, 内容长度: {content_length}")
            
            # 检查POST请求中是否有内容字段且不为空
            if 'content' not in request.form or not request.form['content'].strip():
                current_app.logger.error(f"表单中缺少内容字段或内容为空")
                if is_ajax:
                    return jsonify({'success': False, 'message': '文章内容不能为空'})
                flash('文章内容不能为空', 'error')
                return redirect(request.url)
                
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
        form.tags.choices = [(t.id, t.name) for t in tags]
        
        if request.method == 'POST':
            current_app.logger.info("开始处理文章更新请求...")
            current_app.logger.debug(f"表单数据: {request.form}")
            
            if form.validate_on_submit():
                try:
                    # 处理标签数据
                    selected_tags = form.process_tags()
                    current_app.logger.info(f"处理后的标签: {[tag.name for tag in selected_tags]}")
                    
                    # 获取状态枚举值
                    status = form.get_status()
                    current_app.logger.info(f"文章状态: {status}")
                    
                    # 更新文章
                    try:
                        current_app.logger.info(f"准备更新文章，ID: {post_id}")
                        current_app.logger.info(f"标题: {form.title.data}")
                        current_app.logger.info(f"分类ID: {form.category_id.data}")
                        current_app.logger.info(f"状态: {status}")
                        current_app.logger.info(f"标签数量: {len(selected_tags)}")
                        
                        # 获取新的分类对象并确保它在当前会话中
                        new_category = Category.query.get(form.category_id.data)
                        if not new_category:
                            raise ValueError("分类不存在")
                        
                        # 更新文章属性
                        post.title = form.title.data
                        post.content = form.content.data
                        post.summary = form.summary.data
                        post.category = new_category
                        post.tags = selected_tags
                        post.status = status
                        post.is_sticky = form.is_sticky.data
                        post.is_private = form.is_private.data
                        post.can_comment = form.can_comment.data
                        
                        # 确保status和published字段一致
                        post.update_status_consistency()
                        
                        # 记录内容更新
                        current_app.logger.info(f"文章内容被更新 - 长度: {len(post.content)}")
                        
                        # 强制更新HTML内容并直接提交
                        try:
                            current_app.logger.info(f"强制更新文章 {post_id} 的HTML内容...")
                            
                            # 先强制保存基本内容变更
                            db.session.add(post)
                            db.session.flush()
                            
                            # 先清空HTML内容，强制重新生成
                            post.html_content = None
                            db.session.flush()
                            
                            # 强制等待会话刷新
                            db.session.expire(post)
                            db.session.refresh(post)
                            
                            # 确保内容被正确设置
                            if not post.content:
                                current_app.logger.error(f"严重错误: 刷新后文章内容为空")
                                post.content = form.content.data
                                db.session.add(post)
                                db.session.flush()
                            
                            # 调用更新方法
                            post.update_html_content()
                            
                            # 再次验证HTML内容是否正确生成
                            db.session.refresh(post)
                            if post.html_content:
                                html_length = len(post.html_content)
                                current_app.logger.info(f"文章 {post_id} HTML内容已更新，长度: {html_length}")
                                if html_length < 10:
                                    current_app.logger.warning(f"文章 {post_id} HTML内容异常短，可能生成失败")
                            else:
                                current_app.logger.warning(f"文章 {post_id} HTML内容更新失败，内容为空")
                                # 使用备用方法
                                from app.utils.markdown import markdown_to_html
                                html_content = markdown_to_html(post.content)
                                post.html_content = html_content
                                db.session.add(post)
                                db.session.flush()
                                
                                current_app.logger.info(f"使用备用方法更新HTML内容，长度: {len(post.html_content or '')}")
                        except Exception as e:
                            current_app.logger.error(f"更新HTML内容时出错: {str(e)}")
                            current_app.logger.exception(e)
                            # 使用备用方法
                            try:
                                post.html_content = f"<p>{post.content}</p>"
                                db.session.add(post)
                                db.session.flush()
                                current_app.logger.info(f"使用应急方法更新HTML内容")
                            except Exception as inner_e:
                                current_app.logger.error(f"应急更新也失败: {str(inner_e)}")
                        
                        # 最后提交所有更改
                        db.session.commit()
                        current_app.logger.info(f"文章 {post_id} 所有更改已提交到数据库")
                        
                        # 最后再次刷新确保数据最新
                        db.session.refresh(post)
                        if post.html_content:
                            current_app.logger.info(f"最终HTML内容长度: {len(post.html_content)}")
                        else:
                            current_app.logger.error(f"严重错误: 提交后HTML内容仍为空")
                        
                        # 刷新所有关联对象以确保数据一致性
                        db.session.refresh(new_category)
                        for tag in selected_tags:
                            db.session.refresh(tag)
                            
                        # 清除所有相关缓存
                        try:
                            from flask_caching import Cache
                            cache = Cache()
                            cache.clear()
                            current_app.logger.info("全部缓存已清除")
                        except Exception as cache_error:
                            current_app.logger.error(f"清除缓存出错: {str(cache_error)}")
                            
                        current_app.logger.info("文章更新成功")
                        flash('文章更新成功', 'success')
                        return redirect(url_for('admin_dashboard.post.index'))
                    except Exception as e:
                        current_app.logger.error(f"更新文章时发生错误: {str(e)}")
                        db.session.rollback()
                        flash(f'更新文章失败: {str(e)}', 'error')
                except Exception as e:
                    current_app.logger.error(f"处理表单数据时发生错误: {str(e)}")
                    flash(f'处理表单数据失败: {str(e)}', 'error')
            else:
                current_app.logger.error("表单验证失败")
                # 显示详细的表单错误信息
                for field_name, field_errors in form.errors.items():
                    field_label = getattr(form, field_name).label.text if hasattr(getattr(form, field_name), 'label') else field_name
                    for error in field_errors:
                        flash(f"{field_label}: {error}", 'error')
                        current_app.logger.error(f"表单验证错误: {field_name} - {error}")
        
        return render_template('admin/post/edit.html', form=form, post=post)
    except Exception as e:
        current_app.logger.error(f"加载编辑页面时发生错误: {str(e)}")
        flash(f'加载页面失败: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard.post.index'))

@post_bp.route('/<int:post_id>/delete', methods=['POST'])
@login_required
def delete(post_id):
    """删除文章"""
    try:
        # 检查是否是AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        result = post_service.delete_post(post_id)
        if result['status'] == 'success':
            # 设置闪现消息
            flash('文章删除成功', 'success')
            
            # 如果是AJAX请求，返回JSON响应
            if is_ajax:
                return jsonify({
                    'success': True,
                    'message': '文章删除成功'
                })
            
            # 非AJAX请求，重定向到文章列表页面
            return redirect(url_for('admin_dashboard.post.index'))
        else:
            # 删除失败
            flash(result['message'], 'error')
            
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': result['message']
                }), 400
            
            return redirect(url_for('admin_dashboard.post.index'))
    except Exception as e:
        current_app.logger.error(f"删除文章失败: {str(e)}")
        flash('删除文章失败，请稍后重试', 'error')
        
        if is_ajax:
            return jsonify({
                'success': False,
                'message': '删除文章失败，请稍后重试'
            }), 500
        
        return redirect(url_for('admin_dashboard.post.index'))

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
        return redirect(url_for('.index'))

@post_bp.route('/<int:post_id>/status', methods=['POST'])
@login_required
def change_status(post_id):
    """修改文章状态"""
    try:
        status = request.form.get('status')
        if not status:
            return jsonify({'success': False, 'message': '状态不能为空'}), 400
            
        # 获取文章并更新状态
        post = Post.query.get_or_404(post_id)
        post.status = PostStatus(status)
        
        # 确保status和published字段一致
        post.update_status_consistency()
        
        # 保存到数据库
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': '状态更新成功',
            'status': post.status.value
        })
    except ValueError:
        return jsonify({'success': False, 'message': '无效的状态值'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更改文章状态失败: {str(e)}")
        current_app.logger.exception(e)
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

@post_bp.route('/api/check-title', methods=['GET'])
@login_required
def check_title_exists():
    """检查文章标题是否已存在"""
    title = request.args.get('title', '')
    if not title:
        return jsonify({'exists': False, 'message': '标题为空'})
    
    # 查询数据库
    post = Post.query.filter_by(title=title).first()
    return jsonify({
        'exists': post is not None,
        'message': '标题已存在' if post else '标题可用'
    })

@post_bp.route('/upload', methods=['GET'])
@admin_required
def upload_page():
    """图片上传页面"""
    return render_template('admin/post/upload.html')

@post_bp.route('/upload', methods=['POST'])
@admin_required
def upload():
    """处理图片上传"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件被上传'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'}), 400
        
    try:
        filename = save_file(file)
        file_url = url_for('static', filename=f'uploads/images/{filename}')
        current_app.logger.info(f'文件上传成功: {filename}, URL: {file_url}')
        return jsonify({
            'url': file_url,
            'filename': filename
        })
    except Exception as e:
        current_app.logger.error(f'文件上传失败: {str(e)}')
        return jsonify({'error': str(e)}), 500