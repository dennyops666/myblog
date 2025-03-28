"""
文件名：operation_log.py
描述：操作日志控制器
作者：denny
"""

from flask import Blueprint, render_template, request, current_app, abort
from flask_login import login_required
from app.decorators import admin_required
from app.services.operation_log import operation_log_service

operation_log_bp = Blueprint('operation_log', __name__)

@operation_log_bp.route('/')
@login_required
@admin_required
def index():
    """操作日志列表页面"""
    page = request.args.get('page', 1, type=int)
    operation = request.args.get('operation')
    target_type = request.args.get('target_type')
    
    logs = operation_log_service.get_operation_logs(
        operation=operation,
        target_type=target_type,
        page=page,
        per_page=current_app.config['ITEMS_PER_PAGE']
    )
    
    return render_template('admin/operation_log/list.html', 
                         logs=logs,
                         operation=operation,
                         target_type=target_type)

@operation_log_bp.route('/<int:log_id>')
@login_required
@admin_required
def detail(log_id):
    """操作日志详情页面"""
    log = operation_log_service.get_log_by_id(log_id)
    if not log:
        abort(404)
    return render_template('admin/operation_log/detail.html', log=log) 