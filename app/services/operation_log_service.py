"""
文件名：operation_log_service.py
描述：操作日志服务
作者：denny
创建日期：2024-03-21
"""

from flask import request
from ..models.operation_log import OperationLog
from ..extensions import db

class OperationLogService:
    """操作日志服务类"""
    
    @staticmethod
    def log_operation(user, action, target_type=None, target_id=None, details=None):
        """记录操作日志"""
        log = OperationLog(
            user_id=user.id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    
    @staticmethod
    def get_user_logs(user_id, page=1, per_page=20):
        """获取用户操作日志"""
        return OperationLog.query.filter_by(user_id=user_id)\
            .order_by(OperationLog.created_at.desc())\
            .paginate(page=page, per_page=per_page)
    
    @staticmethod
    def get_operation_logs(operation=None, target_type=None, page=1, per_page=20):
        """获取操作日志"""
        query = OperationLog.query
        
        if operation:
            query = query.filter_by(action=operation)
        if target_type:
            query = query.filter_by(target_type=target_type)
            
        return query.order_by(OperationLog.created_at.desc())\
            .paginate(page=page, per_page=per_page)
            
    @staticmethod
    def get_log_by_id(log_id):
        """根据ID获取操作日志"""
        return OperationLog.query.get(log_id) 