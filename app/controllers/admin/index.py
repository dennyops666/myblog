"""
文件名：index.py
描述：管理后台首页控制器
作者：denny
创建日期：2025-02-16
"""

from flask import render_template, redirect, url_for, current_app, flash
from flask_login import login_required, logout_user
from app.services import get_post_service, get_category_service, get_comment_service
from . import admin_bp
from app.models.post import Post, PostStatus
from app.models.comment import Comment
from app.models.category import Category
from app.models.tag import Tag
from sqlalchemy import desc, or_, func
import traceback
from datetime import datetime

@admin_bp.route('/dashboard')
@admin_bp.route('/')
@login_required
def dashboard():
    """管理后台首页"""
    try:
        current_app.logger.info("访问管理后台首页")
        from app.extensions import db
        
        # 获取基础统计数据
        try:
            post_count = Post.query.count()
            comment_count = Comment.query.count()
            category_count = Category.query.count()
            tag_count = Tag.query.count()
            view_count = db.session.query(func.sum(Post.view_count)).scalar() or 0
            
            # 获取最近文章
            recent_posts = Post.query.order_by(desc(Post.created_at)).limit(5).all()
            
            # 记录统计结果
            current_app.logger.info(f"管理后台统计: 文章={post_count}, 评论={comment_count}, 分类={category_count}, 标签={tag_count}")
            current_app.logger.info(f"获取到 {len(recent_posts)} 篇最近文章")
            
        except Exception as e:
            current_app.logger.error(f"获取统计数据失败: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            post_count = comment_count = category_count = tag_count = view_count = 0
            recent_posts = []
        
        # 渲染模板
        return render_template('admin/index.html',
            post_count=post_count,
            comment_count=comment_count,
            category_count=category_count,
            tag_count=tag_count,
            view_count=view_count,
            recent_posts=recent_posts
        )
    except Exception as e:
        current_app.logger.error(f"加载后台首页失败: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        flash('加载管理后台数据失败，请查看日志了解详情', 'danger')
        return render_template('admin/index.html', 
            error=True, 
            error_message=str(e),
            recent_posts=[]
        )

# 添加别名路由，解决模板中使用admin_dashboard.index的问题
@admin_bp.route('/index')
@login_required
def index():
    """管理后台首页别名，用于兼容模板中的url_for('admin_dashboard.index')调用"""
    return dashboard()

@admin_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """退出登录"""
    logout_user()
    return redirect(url_for('admin_dashboard.dashboard')) 