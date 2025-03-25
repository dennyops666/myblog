"""
文件名：settings.py
描述：系统设置控制器
作者：denny
创建日期：2024-03-22
"""

from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.forms.settings import SettingsForm
from app.models.settings import Settings

# 创建蓝图
settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """系统设置"""
    # 检查是否是管理员
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('admin_dashboard.index'))
    
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
        return redirect(url_for('admin_dashboard.settings.index'))
    
    return render_template('admin/settings.html', form=form) 