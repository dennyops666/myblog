"""
文件名：views.py
描述：管理后台视图
作者：denny
"""

from flask import render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from app.admin import admin
from app.models.user import User
from app.models.tag import Tag
from app.forms import TagForm, TagCreateForm, TagEditForm
from app.extensions import db
from app.models.post import Post, PostStatus
from app.models.category import Category
import re

@admin.route('/')
@login_required
def index():
    """管理后台首页"""
    # 清除SQLAlchemy缓存，确保获取最新数据
    db.session.expire_all()
    
    # 获取标签数量
    tag_count = Tag.query.count()
    current_app.logger.info(f"标签数量: {tag_count}")
    
    # 获取文章统计数据
    post_count = Post.query.count()
    current_app.logger.info(f"文章总数: {post_count}")
    
    published_count = Post.query.filter_by(status=PostStatus.PUBLISHED).count()
    current_app.logger.info(f"已发布文章数: {published_count}")
    
    draft_count = Post.query.filter_by(status=PostStatus.DRAFT).count()
    current_app.logger.info(f"草稿数: {draft_count}")
    
    # 获取分类数量
    category_count = Category.query.count()
    current_app.logger.info(f"分类数量: {category_count}")
    
    # 获取最近的文章
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    current_app.logger.info(f"最近文章数量: {len(recent_posts)}")
    
    # 打印所有文章的状态
    all_posts = Post.query.all()
    for post in all_posts:
        current_app.logger.info(f"文章ID: {post.id}, 标题: {post.title}, 状态: {post.status}")
    
    # 记录传递给模板的数据
    current_app.logger.info(f"传递给模板的数据: post_count={post_count}, published_count={published_count}, draft_count={draft_count}, tag_count={tag_count}")
    
    # 确保数据库查询结果正确传递给模板
    return render_template('admin/index.html', 
                          tag_count=tag_count,
                          post_count=post_count,
                          published_count=published_count,
                          draft_count=draft_count,
                          category_count=category_count,
                          recent_posts=recent_posts)

@admin.route('/tags')
@login_required
def tag_list():
    """标签列表"""
    tags = Tag.query.order_by(Tag.name).all()
    return render_template('admin/tag/list.html', tags=tags)

@admin.route('/tags/new', methods=['GET', 'POST'])
@login_required
def tag_create():
    """创建标签"""
    from app.models.tag import Tag
    from app.forms.tag_form import TagForm
    import re
    
    form = TagForm()
    if form.validate_on_submit():
        # 准备slug数据，确保不为空
        slug = form.slug.data if form.slug.data else re.sub(r'[^\w\-]', '', form.name.data.lower().replace(' ', '-'))
        
        tag = Tag(
            name=form.name.data,
            slug=slug,
            description=form.description.data if form.description.data else None
        )
        db.session.add(tag)
        db.session.commit()
        flash('标签创建成功', 'success')
        return redirect(url_for('admin_dashboard.tag_list'))
    return render_template('admin/tag/edit.html', form=form, is_edit=False)

@admin.route('/tags/<int:tag_id>/edit', methods=['GET', 'POST'])
@login_required
def tag_edit(tag_id):
    """编辑标签"""
    tag = Tag.query.get_or_404(tag_id)
    form = TagForm(obj=tag)
    if form.validate_on_submit():
        tag.name = form.name.data
        
        # 确保slug不为空，如果用户没有提供，则从name生成
        if form.slug.data:
            tag.slug = form.slug.data
        else:
            # 生成slug：转换为小写，替换空格为连字符，移除特殊字符
            tag.slug = re.sub(r'[^\w\-]', '', form.name.data.lower().replace(' ', '-'))
            
        tag.description = form.description.data if form.description.data else None
        db.session.commit()
        flash('标签更新成功', 'success')
        return redirect(url_for('admin_dashboard.tag_list'))
    return render_template('admin/tag/edit.html', form=form, tag=tag, is_edit=True)

@admin.route('/tags/<int:tag_id>/delete', methods=['POST'])
@login_required
def tag_delete(tag_id):
    """删除标签"""
    tag = Tag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    flash('标签删除成功', 'success')
    return redirect(url_for('admin_dashboard.tag_list'))

@admin.route('/posts')
@login_required
def post_list():
    """文章列表"""
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin/post/list.html', posts=posts)

@admin.route('/posts/new', methods=['GET', 'POST'])
@login_required
def post_create():
    """创建文章"""
    from app.models.post import Post, PostStatus
    from app.models.tag import Tag
    from app.forms.admin.post import PostForm
    
    form = PostForm()
    
    if form.validate_on_submit():
        try:
            # 检查标题是否已存在
            existing_post = Post.query.filter_by(title=form.title.data).first()
            if existing_post:
                form.title.errors.append('该标题已存在，请使用其他标题')
                return render_template('admin/post/create.html', form=form)
            
            # 使用最简单的方式创建文章，手动构造SQL插入语句
            from sqlalchemy import text
            
            # 准备数据
            title = form.title.data
            content = form.content.data if form.content.data else ""
            summary = form.summary.data if form.summary.data else ""
            category_id = form.category_id.data if form.category_id.data != 0 else None
            status = form.status.data  # 这是字符串，如 'DRAFT'
            is_sticky = 1 if form.is_sticky.data else 0
            is_private = 1 if form.is_private.data else 0
            can_comment = 1 if form.can_comment.data else 0
            author_id = current_user.id
            
            # 直接执行SQL插入语句
            sql = text("""
                INSERT INTO posts (
                    title, content, html_content, summary, category_id, 
                    author_id, status, is_sticky, is_private, can_comment,
                    created_at, updated_at, view_count, comments_count, published
                ) VALUES (
                    :title, :content, :html_content, :summary, :category_id,
                    :author_id, :status, :is_sticky, :is_private, :can_comment,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, 0, 1
                )
            """)
            
            # 执行SQL
            result = db.session.execute(sql, {
                'title': title,
                'content': content,
                'html_content': f"<p>{content}</p>", # 简单HTML格式
                'summary': summary,
                'category_id': category_id,
                'author_id': author_id,
                'status': status,
                'is_sticky': is_sticky,
                'is_private': is_private,
                'can_comment': can_comment
            })
            db.session.commit()
            
            # 获取新文章ID
            post_id = result.lastrowid
            
            # 如果有标签，处理标签关联
            if form.tags.data:
                # 过滤掉None值
                valid_tag_ids = [tag_id for tag_id in form.tags.data if tag_id is not None]
                
                for tag_id in valid_tag_ids:
                    # 确保标签存在
                    tag = Tag.query.get(tag_id)
                    if tag:
                        db.session.execute(
                            text("INSERT INTO post_tags (post_id, tag_id) VALUES (:post_id, :tag_id)"),
                            {'post_id': post_id, 'tag_id': tag_id}
                        )
                # 只有有标签需要提交时才执行commit
                if valid_tag_ids:
                    db.session.commit()
            
            flash('文章创建成功', 'success')
            return redirect(url_for('admin_dashboard.post_list'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建文章出错: {str(e)}")
            import traceback
            current_app.logger.error(f"异常堆栈: {traceback.format_exc()}")
            flash(f'创建文章失败: {str(e)}', 'error')
            return render_template('admin/post/create.html', form=form)
    
    return render_template('admin/post/create.html', form=form)

@admin.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def post_edit(post_id):
    """编辑文章"""
    from app.models.post import Post, PostStatus
    from app.models.tag import Tag
    from app.forms.admin.post import PostForm
    from flask import jsonify
    
    post = Post.query.get_or_404(post_id)
    
    # 检查权限
    if post.author_id != current_user.id and not current_user.is_admin:
        flash('您没有权限编辑此文章', 'danger')
        return redirect(url_for('admin_dashboard.post_list'))
    
    form = PostForm(obj=post)
    form.post_id = post_id  # 设置post_id属性以便验证标题唯一性时排除当前文章
    
    # 设置当前标签
    if request.method == 'GET':
        form.status.data = post.status.name
        form.tags.data = [tag.id for tag in post.tags]
    
    if form.validate_on_submit():
        try:
            # 更新文章
            post.title = form.title.data
            post.content = form.content.data
            post.summary = form.summary.data
            post.category_id = form.category_id.data if form.category_id.data != 0 else None
            post.status = PostStatus[form.status.data]
            post.is_sticky = form.is_sticky.data
            post.is_private = form.is_private.data
            post.can_comment = form.can_comment.data
            
            # 处理标签
            post.tags = []
            if form.tags.data:
                # 过滤掉None值
                valid_tag_ids = [tag_id for tag_id in form.tags.data if tag_id is not None]
                
                for tag_id in valid_tag_ids:
                    tag = Tag.query.get(tag_id)
                    if tag:
                        post.tags.append(tag)
            
            # 添加：强制更新HTML内容并记录日志
            current_app.logger.info(f"编辑文章 {post_id}：开始更新HTML内容")
            post.update_html_content()
            current_app.logger.info(f"编辑文章 {post_id}：HTML内容更新完成，长度: {len(post.html_content or '')}")
            
            # 最后一次保存到数据库
            db.session.add(post)
            db.session.commit()
            
            flash('文章更新成功', 'success')
            
            # 检查是否为AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': '文章更新成功',
                    'redirect_url': url_for('admin_dashboard.post_list')
                })
            
            # 跳转到文章列表页面
            return redirect(url_for('admin_dashboard.post_list'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新文章错误: {str(e)}")
            
            # 检查是否为AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': f'更新文章失败: {str(e)}'
                }), 500
                
            flash(f'更新文章失败: {str(e)}', 'error')
    
    elif request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # 表单验证失败，返回错误信息
        errors = {}
        for field_name, field_errors in form.errors.items():
            errors[field_name] = field_errors
            
        return jsonify({
            'success': False,
            'message': '表单验证失败',
            'errors': errors
        }), 400
    
    return render_template('admin/post/edit.html', form=form, post=post)

@admin.route('/posts/<int:post_id>/delete', methods=['POST'])
@login_required
def post_delete(post_id):
    """删除文章"""
    from app.models.post import Post
    
    post = Post.query.get_or_404(post_id)
    
    # 检查权限
    if post.author_id != current_user.id and not current_user.is_admin:
        flash('您没有权限删除此文章', 'danger')
        return redirect(url_for('admin_dashboard.post_list'))
    
    # 删除文章
    db.session.delete(post)
    db.session.commit()
    
    flash('文章删除成功', 'success')
    return redirect(url_for('admin_dashboard.post_list'))

@admin.route('/categories')
@login_required
def category_list():
    """分类列表"""
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/category/list.html', categories=categories)

@admin.route('/categories/new', methods=['GET', 'POST'])
@login_required
def category_create():
    """创建分类"""
    from app.models.category import Category
    from app.forms.category_form import CategoryForm
    
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            slug=form.slug.data if form.slug.data else None,
            description=form.description.data if form.description.data else None
        )
        db.session.add(category)
        db.session.commit()
        
        flash('分类创建成功', 'success')
        return redirect(url_for('admin_dashboard.category_list'))
    
    return render_template('admin/category/edit.html', form=form, is_edit=False)

@admin.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def category_edit(category_id):
    """编辑分类"""
    from app.models.category import Category
    from app.forms.category_form import CategoryForm
    
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.slug = form.slug.data if form.slug.data else None
        category.description = form.description.data if form.description.data else None
        db.session.commit()
        
        flash('分类更新成功', 'success')
        return redirect(url_for('admin_dashboard.category_list'))
    
    return render_template('admin/category/edit.html', form=form, category=category, is_edit=True)

@admin.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def category_delete(category_id):
    """删除分类"""
    from app.models.category import Category
    
    category = Category.query.get_or_404(category_id)
    
    # 检查分类下是否有文章
    if category.posts.count() > 0:
        flash(f'无法删除分类 "{category.name}"，该分类下有 {category.posts.count()} 篇文章', 'danger')
        return redirect(url_for('admin_dashboard.category_list'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash(f'分类 "{category.name}" 已成功删除', 'success')
    return redirect(url_for('admin_dashboard.category_list'))

@admin.route('/users')
@login_required
def user_list():
    """用户列表"""
    # 检查是否是管理员
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('admin_dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('USERS_PER_PAGE', 10)
    
    pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    users = pagination.items
    
    return render_template('admin/user/list.html', users=users, pagination=pagination)

@admin.route('/users/new', methods=['GET', 'POST'])
@login_required
def user_create():
    """创建用户"""
    # 检查是否是管理员
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('admin_dashboard.index'))
    
    from app.forms.user import UserForm
    
    form = UserForm()
    
    if form.validate_on_submit():
        # 检查用户名是否已存在
        if User.query.filter_by(username=form.username.data).first():
            flash('用户名已存在', 'danger')
            return render_template('admin/user/edit.html', form=form, is_edit=False)
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=form.email.data).first():
            flash('邮箱已存在', 'danger')
            return render_template('admin/user/edit.html', form=form, is_edit=False)
        
        # 创建新用户
        user = User(
            username=form.username.data,
            email=form.email.data,
            nickname=form.nickname.data,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data)
        
        # 设置角色
        from app.models.role import Role
        role = Role.query.get(form.role_id.data)
        if role:
            user.roles.append(role)
        
        db.session.add(user)
        db.session.commit()
        
        flash('用户创建成功', 'success')
        return redirect(url_for('admin_dashboard.user_list'))
    
    return render_template('admin/user/edit.html', form=form, is_edit=False)

@admin.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    """编辑用户"""
    # 检查是否是管理员
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('admin_dashboard.index'))
    
    from app.forms.user import UserEditForm
    
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    
    # 设置当前角色
    if request.method == 'GET' and user.roles:
        form.role_id.data = user.roles[0].id if user.roles else None
    
    if form.validate_on_submit():
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user and existing_user.id != user_id:
            flash('用户名已存在', 'danger')
            return render_template('admin/user/edit.html', form=form, user=user, is_edit=True)
        
        # 检查邮箱是否已存在
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email and existing_email.id != user_id:
            flash('邮箱已存在', 'danger')
            return render_template('admin/user/edit.html', form=form, user=user, is_edit=True)
        
        # 更新用户信息
        user.username = form.username.data
        user.email = form.email.data
        user.nickname = form.nickname.data
        user.is_active = form.is_active.data
        
        # 如果提供了新密码，则更新密码
        if form.password.data:
            user.set_password(form.password.data)
        
        # 更新角色
        from app.models.role import Role
        user.roles = []
        role = Role.query.get(form.role_id.data)
        if role:
            user.roles.append(role)
        
        db.session.commit()
        
        flash('用户更新成功', 'success')
        return redirect(url_for('admin_dashboard.user_list'))
    
    return render_template('admin/user/edit.html', form=form, user=user, is_edit=True)

@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def user_delete(user_id):
    """删除用户"""
    # 检查是否是管理员
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('admin_dashboard.index'))
    
    user = User.query.get_or_404(user_id)
    
    # 不能删除自己
    if user.id == current_user.id:
        flash('不能删除当前登录的用户', 'danger')
        return redirect(url_for('admin_dashboard.user_list'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('用户删除成功', 'success')
    return redirect(url_for('admin_dashboard.user_list'))

@admin.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """个人资料"""
    from app.forms.user import ProfileForm
    
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # 检查邮箱是否已存在
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email and existing_email.id != current_user.id:
            flash('邮箱已存在', 'danger')
            return render_template('admin/profile.html', form=form)
        
        # 更新用户信息
        current_user.email = form.email.data
        current_user.nickname = form.nickname.data
        current_user.bio = form.bio.data
        
        # 如果提供了新密码，则更新密码
        if form.password.data:
            current_user.set_password(form.password.data)
        
        db.session.commit()
        
        flash('个人资料更新成功', 'success')
        return redirect(url_for('admin_dashboard.profile'))
    
    return render_template('admin/profile.html', form=form)

@admin.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """系统设置"""
    # 检查是否是管理员
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('admin_dashboard.index'))
    
    from app.forms.settings import SettingsForm
    from app.models.settings import Settings
    
    # 获取当前设置
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()
    
    form = SettingsForm(obj=settings)
    
    if form.validate_on_submit():
        # 更新设置
        settings.blog_name = form.blog_name.data
        settings.blog_description = form.blog_description.data
        settings.posts_per_page = form.posts_per_page.data
        settings.allow_registration = form.allow_registration.data
        settings.allow_comments = form.allow_comments.data
        
        db.session.commit()
        
        # 更新应用配置
        current_app.config['BLOG_NAME'] = settings.blog_name
        current_app.config['BLOG_DESCRIPTION'] = settings.blog_description
        current_app.config['POSTS_PER_PAGE'] = settings.posts_per_page
        
        flash('系统设置更新成功', 'success')
        return redirect(url_for('admin_dashboard.settings'))
    
    return render_template('admin/settings.html', form=form)

@admin.route('/comments')
@login_required
def comment_list():
    """评论列表"""
    # 检查是否是管理员
    if not current_user.is_admin and not current_user.can_moderate_comments:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('admin_dashboard.index'))
    
    from app.models.comment import Comment
    
    # 获取页码参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 获取评论列表，使用分页
    pagination = Comment.query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    comments = pagination.items
    
    return render_template(
        'admin/comments.html',
        comments=pagination,
        title='评论管理'
    )

@admin.route('/comments/<int:comment_id>/approve', methods=['POST'])
@login_required
def comment_approve(comment_id):
    """批准评论"""
    # 检查是否是管理员
    if not current_user.is_admin and not current_user.can_moderate_comments:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('admin_dashboard.index'))
    
    from app.models.comment import Comment, CommentStatus
    
    comment = Comment.query.get_or_404(comment_id)
    comment.status = CommentStatus.APPROVED
    db.session.commit()
    
    flash('评论已批准', 'success')
    return redirect(url_for('admin_dashboard.comment_list'))

@admin.route('/comments/<int:comment_id>/reject', methods=['POST'])
@login_required
def comment_reject(comment_id):
    """拒绝评论"""
    # 检查是否是管理员
    if not current_user.is_admin and not current_user.can_moderate_comments:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('admin_dashboard.index'))
    
    from app.models.comment import Comment, CommentStatus
    
    try:
        comment = Comment.query.get_or_404(comment_id)
        comment.status = CommentStatus.REJECTED
        db.session.commit()
        
        # 检查请求是否为AJAX
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'message': '评论已拒绝'
            })
        
        flash('评论已拒绝', 'success')
        return redirect(url_for('admin_dashboard.comment_list'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'拒绝评论失败，ID: {comment_id}, 错误: {str(e)}')
        
        # 检查请求是否为AJAX
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'error',
                'message': '操作失败，请稍后重试'
            }), 500
        
        flash('拒绝评论失败', 'danger')
        return redirect(url_for('admin_dashboard.comment_list'))

@admin.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def comment_delete(comment_id):
    """删除评论"""
    # 检查是否是管理员
    if not current_user.is_admin and not current_user.can_moderate_comments:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': '您没有权限执行此操作'}), 403
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('admin_dashboard.index'))
    
    from app.models.comment import Comment
    
    try:
        comment = Comment.query.get_or_404(comment_id)
        db.session.delete(comment)
        db.session.commit()
        
        # 检查请求是否为AJAX
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'message': '评论已删除'
            })
        
        flash('评论已删除', 'success')
        return redirect(url_for('admin_dashboard.comment_list'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除评论失败，ID: {comment_id}, 错误: {str(e)}')
        
        # 检查请求是否为AJAX
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'error',
                'message': '删除失败，请稍后重试'
            }), 500
        
        flash('删除评论失败', 'danger')
        return redirect(url_for('admin_dashboard.comment_list'))

@admin.route('/test_stats')
@login_required
def test_stats():
    """测试统计数据页面"""
    return render_template('admin/test_stats.html')

@admin.route('/api/stats')
@login_required
def get_stats():
    """获取最新的统计数据，用于AJAX请求"""
    # 清除SQLAlchemy缓存，确保获取最新数据
    db.session.expire_all()
    
    # 获取标签数量
    tag_count = Tag.query.count()
    
    # 获取文章统计数据
    post_count = Post.query.count()
    published_count = Post.query.filter_by(status=PostStatus.PUBLISHED).count()
    draft_count = Post.query.filter_by(status=PostStatus.DRAFT).count()
    
    # 获取分类数量
    category_count = Category.query.count()
    
    # 返回JSON数据
    return jsonify({
        'tag_count': tag_count,
        'post_count': post_count,
        'published_count': published_count,
        'draft_count': draft_count,
        'category_count': category_count
    })

@admin.route('/comments/batch-delete', methods=['POST'])
@login_required
def batch_delete_comments():
    """批量删除评论"""
    # 检查是否是管理员
    if not current_user.is_admin and not current_user.can_moderate_comments:
        return jsonify({'status': 'error', 'message': '您没有权限执行此操作'}), 403
    
    try:
        from app.models.comment import Comment
        
        data = request.get_json()
        comment_ids = data.get('comment_ids', [])
        
        if not comment_ids:
            return jsonify({'status': 'error', 'message': '未选择任何评论'}), 400
        
        # 删除评论
        for comment_id in comment_ids:
            comment = Comment.query.get(comment_id)
            if comment:
                db.session.delete(comment)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'已成功删除 {len(comment_ids)} 条评论'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'批量删除评论失败: {str(e)}')
        return jsonify({'status': 'error', 'message': '删除评论失败'}), 500

@admin.route('/login', methods=['GET', 'POST'])
def login():
    """管理后台登录页"""
    # 如果用户已登录，则重定向到管理后台首页
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard.index'))
    
    # 处理POST请求（AJAX登录）
    if request.method == 'POST' and request.is_json:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        remember_me = data.get('remember_me', False)
        
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            return jsonify({
                'status': 'error',
                'message': '用户名或密码错误'
            })
        
        # 执行登录
        login_user(user, remember=remember_me)
        
        # 获取next参数，确保安全重定向
        next_url = request.args.get('next')
        if next_url and 'admin' in next_url:
            return jsonify({
                'status': 'success',
                'message': '登录成功',
                'next_url': next_url
            })
        
        # 默认重定向到管理后台首页
        return jsonify({
            'status': 'success',
            'message': '登录成功',
            'next_url': url_for('admin_dashboard.index')
        })
    
    # 处理GET请求（显示登录页面）
    return render_template('admin/login.html')

@admin.route('/logout')
@login_required
def logout():
    """管理后台登出"""
    logout_user()
    flash('您已成功退出登录', 'success')
    return redirect(url_for('admin_dashboard.login')) 