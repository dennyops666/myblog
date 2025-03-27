"""
文件名：admin.py
描述：管理员视图
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import User, db, Category, Tag, Post, PostStatus, Role, Comment
from datetime import datetime, UTC
import os
from werkzeug.utils import secure_filename
from PIL import Image
import uuid
from flask import current_app
from app.forms.admin.post import PostForm
from app.forms.admin.user import RegisterForm

bp = Blueprint('admin_dashboard', __name__, url_prefix='/admin')

@bp.route('/')
@login_required
def index():
    """管理后台首页"""
    try:
        # 获取统计信息
        post_count = Post.query.count()
        published_count = Post.query.filter_by(status=PostStatus.PUBLISHED).count()
        draft_count = Post.query.filter_by(status=PostStatus.DRAFT).count()
        category_count = Category.query.count()
        tag_count = Tag.query.count()
        
        # 获取最近的文章
        recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
        
        # 确保所有必需的变量都有默认值
        context = {
            'title': '管理后台',
            'post_count': post_count or 0,
            'published_count': published_count or 0,
            'draft_count': draft_count or 0,
            'category_count': category_count or 0,
            'tag_count': tag_count or 0,
            'recent_posts': recent_posts or []
        }
        
        return render_template('admin/index.html', **context)
    except Exception as e:
        current_app.logger.error(f"管理后台首页加载失败: {str(e)}")
        flash('加载管理后台首页时发生错误', 'error')
        return render_template('admin/index.html',
                             title='管理后台',
                             post_count=0,
                             published_count=0,
                             draft_count=0,
                             category_count=0,
                             tag_count=0,
                             recent_posts=[])

@bp.route('/post/')
@login_required
def post_list():
    """文章管理页面"""
    # 查询所有文章
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin/post/list.html', title='文章管理', posts=posts)

@bp.route('/post/create', methods=['GET', 'POST'])
@login_required
def post_create():
    """创建文章"""
    form = PostForm()
    
    # 设置分类和标签选项
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    all_tags = Tag.query.all()
    form.tags.choices = [(t.id, t.name) for t in all_tags]
    
    if request.method == 'POST' and form.validate_on_submit():
        # 创建新文章
        post = Post(
            title=form.title.data,
            content=form.content.data,
            summary=form.summary.data,
            category_id=form.category_id.data,
            author_id=current_user.id,
            status=form.get_status()
        )
        
        # 添加标签
        try:
            tags = form.process_tags()
            for tag in tags:
                post.tags.append(tag)
        except ValueError as e:
            flash(str(e), 'error')
            return render_template('admin/post/create.html', title='创建文章', form=form)
        
        db.session.add(post)
        db.session.commit()
        
        flash('文章创建成功', 'success')
        return redirect(url_for('admin_dashboard.post_list'))
    
    return render_template('admin/post/create.html', title='创建文章', form=form)

@bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def post_edit(post_id):
    """编辑文章 (兼容旧路由，实际重定向到新路由)"""
    # 重定向到新的编辑页面
    current_app.logger.info(f"从旧路由重定向到新路由: post_id={post_id}")
    return redirect(url_for('post.edit', post_id=post_id))

@bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def post_delete(post_id):
    """删除文章"""
    post = Post.query.get_or_404(post_id)
    
    # 检查权限
    if post.author_id != current_user.id and not current_user.is_admin:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': '您没有权限删除此文章'
            })
        flash('您没有权限删除此文章', 'error')
        return redirect(url_for('admin_dashboard.post_list'))
    
    try:
        db.session.delete(post)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': '文章删除成功'
            })
        flash('文章删除成功', 'success')
        return redirect(url_for('admin_dashboard.post_list'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除文章失败: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': f'删除失败: {str(e)}'
            })
        flash(f'删除失败: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard.post_list'))

@bp.route('/category/create', methods=['GET', 'POST'])
@login_required
def category_create():
    """创建分类"""
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        description = request.form.get('description')
        
        if not name:
            flash('分类名称不能为空', 'error')
            return render_template('admin/category/create.html', title='创建分类')
        
        # 检查分类名称是否已存在
        existing_category = Category.query.filter_by(name=name).first()
        if existing_category:
            flash('分类名称已存在', 'error')
            return render_template('admin/category/create.html', title='创建分类')
        
        # 创建新分类
        category = Category(name=name, slug=slug, description=description)
        db.session.add(category)
        db.session.commit()
        
        flash('分类创建成功', 'success')
        return redirect(url_for('admin_dashboard.category_list'))
    
    return render_template('admin/category/create.html', title='创建分类')

@bp.route('/category/')
@login_required
def category_list():
    """分类列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 获取分类列表
    pagination = Category.query.order_by(Category.name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    categories = pagination.items
    
    # 获取每个分类下的文章数量
    category_post_counts = {}
    for category in categories:
        category_post_counts[category.id] = Post.query.filter_by(category_id=category.id).count()
    
    return render_template('admin/category/list.html', 
                          title='分类管理',
                          categories=categories,
                          pagination=pagination,
                          category_post_counts=category_post_counts)

@bp.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def category_edit(category_id):
    """编辑分类"""
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        description = request.form.get('description')
        
        if not name:
            flash('分类名称不能为空', 'error')
            return render_template('admin/category/edit.html', title='编辑分类', category=category)
        
        # 检查分类名称是否已存在（排除当前分类）
        existing_category = Category.query.filter(Category.name == name, Category.id != category_id).first()
        if existing_category:
            flash('分类名称已存在', 'error')
            return render_template('admin/category/edit.html', title='编辑分类', category=category)
        
        # 更新分类
        category.name = name
        category.slug = slug
        category.description = description
        category.updated_at = datetime.now(UTC)
        
        db.session.commit()
        
        flash('分类更新成功', 'success')
        return redirect(url_for('admin_dashboard.category_list'))
    
    return render_template('admin/category/edit.html', title='编辑分类', category=category)

@bp.route('/category/<int:category_id>/delete', methods=['POST'])
@login_required
def category_delete(category_id):
    """删除分类"""
    category = Category.query.get_or_404(category_id)
    
    # 检查分类下是否有文章
    if category.posts.count() > 0:
        flash(f'无法删除分类 "{category.name}"，该分类下有 {category.posts.count()} 篇文章', 'danger')
        return redirect(url_for('admin_dashboard.category_list'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash(f'分类 "{category.name}" 已成功删除', 'success')
    return redirect(url_for('admin_dashboard.category_list'))

@bp.route('/tag/create', methods=['GET', 'POST'])
@login_required
def tag_create():
    """创建标签"""
    if request.method == 'POST':
        name = request.form.get('name')
        
        if not name:
            flash('标签名称不能为空', 'error')
            return render_template('admin/tag/create.html', title='创建标签')
        
        # 检查标签名称是否已存在
        existing_tag = Tag.query.filter_by(name=name).first()
        if existing_tag:
            flash('标签名称已存在', 'error')
            return render_template('admin/tag/create.html', title='创建标签')
        
        # 创建新标签
        tag = Tag(name=name)
        db.session.add(tag)
        db.session.commit()
        
        flash('标签创建成功', 'success')
        return redirect(url_for('admin_dashboard.tag_list'))
    
    return render_template('admin/tag/create.html', title='创建标签')

@bp.route('/tag/')
@login_required
def tag_list():
    """标签列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 获取标签列表
    pagination = Tag.query.order_by(Tag.name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    tags = pagination.items
    
    # 获取每个标签下的文章数量
    tag_post_counts = {}
    for tag in tags:
        tag_post_counts[tag.id] = Post.query.filter_by(tags=tag).count()
    
    return render_template('admin/tag/list.html', 
                          title='标签管理',
                          tags=tags,
                          pagination=pagination,
                          tag_post_counts=tag_post_counts)

@bp.route('/tag/<int:tag_id>/delete', methods=['POST'])
@login_required
def tag_delete(tag_id):
    """删除标签"""
    tag = Tag.query.get_or_404(tag_id)
    
    # 检查标签下是否有文章
    if tag.posts.count() > 0:
        flash(f'无法删除标签 "{tag.name}"，该标签下有 {tag.posts.count()} 篇文章', 'danger')
        return redirect(url_for('admin_dashboard.tag_list'))
    
    db.session.delete(tag)
    db.session.commit()
    
    flash(f'标签 "{tag.name}" 已成功删除', 'success')
    return redirect(url_for('admin_dashboard.tag_list'))

@bp.route('/users/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    """用户个人资料"""
    # 确保用户对象绑定到会话
    try:
        user = User.query.get(current_user.id)
        if not user:
            # 如果找不到用户，重定向到首页
            flash('用户不存在', 'error')
            return redirect(url_for('admin_dashboard.index'))
    except Exception as e:
        # 处理可能的异常
        current_app.logger.error(f"获取用户信息失败: {str(e)}")
        flash('获取用户信息失败', 'error')
        return redirect(url_for('admin_dashboard.index'))
    
    if request.method == 'POST':
        # 获取表单数据
        email = request.form.get('email')
        nickname = request.form.get('nickname')
        bio = request.form.get('bio')
        
        # 更新用户信息
        user.email = email
        user.nickname = nickname
        user.bio = bio
        user.updated_at = datetime.now(UTC)
        
        try:
            db.session.commit()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': '个人资料更新成功'
                })
            flash('个人资料更新成功', 'success')
            return redirect(url_for('admin_dashboard.user_profile'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新用户信息失败: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': '更新失败，请重试',
                    'errors': {'email': ['更新失败，请重试']}
                })
            flash('更新失败，请重试', 'error')
            return redirect(url_for('admin_dashboard.user_profile'))
    
    return render_template('admin/user/profile.html', title='个人资料', user=user)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """个人资料"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证当前密码
        if not current_user.check_password(current_password):
            flash('当前密码错误', 'error')
            return redirect(url_for('admin_dashboard.profile'))
        
        # 更新用户名和邮箱
        current_user.username = username
        current_user.email = email
        
        # 如果提供了新密码，则更新密码
        if new_password:
            if new_password != confirm_password:
                flash('两次输入的密码不一致', 'error')
                return redirect(url_for('admin_dashboard.profile'))
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('个人资料更新成功', 'success')
        return redirect(url_for('admin_dashboard.profile'))
    
    return render_template('admin/profile.html', title='个人资料')

# 文件上传相关路由
def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['IMAGE_ALLOWED_EXTENSIONS']

@bp.route('/upload/', methods=['POST'])
@login_required
def upload_file():
    """上传文件"""
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': '没有文件被上传'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': '没有选择文件'
        }), 400
    
    if file and allowed_file(file.filename):
        try:
            # 读取文件内容到内存
            file_content = file.read()
            file.seek(0)  # 重置文件指针
            
            # 检查文件大小
            file_size = len(file_content)
            max_size = current_app.config.get('IMAGE_MAX_SIZE', 5 * 1024 * 1024)  # 默认5MB
            if file_size > max_size:
                return jsonify({
                    'success': False,
                    'message': f'文件太大，最大允许 {max_size/1024/1024:.1f}MB'
                }), 400
            
            # 确保上传目录存在
            upload_folder = current_app.config['IMAGE_UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            
            # 生成安全的文件名
            original_filename = secure_filename(file.filename)
            filename_parts = original_filename.rsplit('.', 1)
            unique_filename = f"{filename_parts[0]}_{uuid.uuid4().hex[:8]}.{filename_parts[1]}"
            
            # 保存原始文件
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            
            # 处理图片（调整大小等）
            try:
                with Image.open(file_path) as img:
                    # 转换为RGB模式（处理PNG等带透明通道的图片）
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # 调整大小
                    max_size = current_app.config.get('IMAGE_MAX_DIMENSION', 2048)
                    if img.width > max_size or img.height > max_size:
                        ratio = min(max_size / img.width, max_size / img.height)
                        new_size = (int(img.width * ratio), int(img.height * ratio))
                        img = img.resize(new_size, Image.LANCZOS)
                    
                    # 保存处理后的图片
                    img.save(
                        file_path, 
                        format=current_app.config.get('IMAGE_FORMAT', 'JPEG'),
                        quality=current_app.config.get('IMAGE_QUALITY', 85)
                    )
            except Exception as e:
                current_app.logger.error(f"图片处理失败: {str(e)}")
                # 如果图片处理失败，我们仍然保留原始文件，不返回错误
            
            # 获取文件URL
            file_url = url_for('static', filename=f'uploads/images/{unique_filename}', _external=True)
            
            return jsonify({
                'success': True,
                'filename': unique_filename,
                'url': file_url,
                'size': file_size
            })
        except Exception as e:
            current_app.logger.error(f"文件上传失败: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'文件上传失败: {str(e)}'
            }), 400
    
    return jsonify({
        'success': False,
        'message': '不支持的文件类型'
    }), 400

@bp.route('/upload/delete/<filename>', methods=['POST'])
@login_required
def delete_file(filename):
    """删除文件"""
    try:
        file_path = os.path.join(current_app.config['IMAGE_UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({
                'success': True,
                'message': '文件删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
    except Exception as e:
        current_app.logger.error(f"删除文件失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除文件失败: {str(e)}'
        }), 500

@bp.route('/upload/images', methods=['GET'])
@login_required
def get_images():
    """获取已上传的图片列表"""
    try:
        upload_folder = current_app.config['IMAGE_UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        
        files = []
        for filename in os.listdir(upload_folder):
            if allowed_file(filename):
                file_path = os.path.join(upload_folder, filename)
                file_stats = os.stat(file_path)
                files.append({
                    'name': filename,
                    'url': f"/uploads/images/{filename}",
                    'size': file_stats.st_size,
                    'modified': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # 按修改时间排序，最新的在前面
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': files
        })
    except Exception as e:
        current_app.logger.error(f"获取图片列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取图片列表失败: {str(e)}'
        }), 500

@bp.route('/post/preview', methods=['POST'])
@login_required
def post_preview():
    """预览文章内容"""
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({
                'success': False,
                'message': '无效的请求数据'
            }), 400
        
        content = data['content']
        
        # 使用Markdown渲染内容
        from app.utils.markdown import render_markdown
        html = render_markdown(content)
        
        return jsonify({
            'success': True,
            'html': html
        })
    except Exception as e:
        current_app.logger.error(f"预览文章失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'预览失败: {str(e)}'
        }), 500

@bp.route('/post/search-tags', methods=['GET'])
@login_required
def post_search_tags():
    """搜索标签"""
    try:
        query = request.args.get('q', '')
        
        # 搜索标签
        tags = []
        if query:
            tags = Tag.query.filter(Tag.name.ilike(f'%{query}%')).all()
        else:
            tags = Tag.query.limit(10).all()
        
        # 格式化结果
        result = {
            'tags': [{'id': tag.id, 'name': tag.name} for tag in tags]
        }
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"搜索标签失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'搜索失败: {str(e)}'
        }), 500

# 评论管理
@bp.route('/comments/')
@login_required
def comment_list():
    """评论列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 获取评论列表
    pagination = Comment.query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    comments = pagination.items
    
    return render_template('admin/comment/list.html', 
                          title='评论管理',
                          comments=comments,
                          pagination=pagination)

@bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def comment_delete(comment_id):
    """删除评论"""
    comment = Comment.query.get_or_404(comment_id)
    
    try:
        db.session.delete(comment)
        db.session.commit()
        flash('评论删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard.comment_list'))

@bp.route('/comment/<int:comment_id>/approve', methods=['POST'])
@login_required
def comment_approve(comment_id):
    """审核评论"""
    comment = Comment.query.get_or_404(comment_id)
    
    try:
        comment.is_approved = True
        db.session.commit()
        flash('评论审核通过', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'审核失败: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard.comment_list'))

@bp.route('/comment/<int:comment_id>/reject', methods=['POST'])
@login_required
def comment_reject(comment_id):
    """拒绝评论"""
    comment = Comment.query.get_or_404(comment_id)
    
    try:
        comment.is_approved = False
        db.session.commit()
        flash('评论已拒绝', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'操作失败: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard.comment_list'))

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """系统设置"""
    if request.method == 'POST':
        # 获取表单数据
        blog_name = request.form.get('blog_name')
        blog_description = request.form.get('blog_description')
        posts_per_page = request.form.get('posts_per_page', type=int)
        allow_comments = request.form.get('allow_comments') == 'on'
        allow_registration = request.form.get('allow_registration') == 'on'
        
        # 更新设置
        current_app.config['BLOG_NAME'] = blog_name
        current_app.config['BLOG_DESCRIPTION'] = blog_description
        current_app.config['POSTS_PER_PAGE'] = posts_per_page
        current_app.config['ALLOW_COMMENTS'] = allow_comments
        current_app.config['ALLOW_REGISTRATION'] = allow_registration
        
        # 保存到数据库
        settings = {
            'blog_name': blog_name,
            'blog_description': blog_description,
            'posts_per_page': posts_per_page,
            'allow_comments': allow_comments,
            'allow_registration': allow_registration
        }
        
        # 这里可以添加将设置保存到数据库的代码
        
        flash('系统设置已更新', 'success')
        return redirect(url_for('admin_dashboard.settings'))
    
    # 获取当前设置
    settings = {
        'blog_name': current_app.config.get('BLOG_NAME', '我的博客'),
        'blog_description': current_app.config.get('BLOG_DESCRIPTION', ''),
        'posts_per_page': current_app.config.get('POSTS_PER_PAGE', 10),
        'allow_comments': current_app.config.get('ALLOW_COMMENTS', True),
        'allow_registration': current_app.config.get('ALLOW_REGISTRATION', True)
    }
    
    return render_template('admin/settings.html', title='系统设置', settings=settings) 