"""
操作日志服务模块
"""
from flask import request, current_app
from app.models.operation_log import OperationLog
from app.extensions import db
from datetime import datetime, timedelta, UTC

class OperationLogService:
    """操作日志服务类"""

    def log_login(self, user):
        """记录登录日志"""
        log = OperationLog(
            user_id=user.id,
            action='login',
            target_type='user',
            target_id=user.id,
            details=f'用户登录 - 用户名: {user.username}, 浏览器: {request.user_agent}',
            result='success',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        current_app.logger.info(
            f'用户登录成功 - '
            f'用户名: {user.username}, '
            f'浏览器: {request.user_agent}'
        )

    def log_logout(self, user):
        """记录登出日志"""
        log = OperationLog(
            user_id=user.id,
            action='logout',
            target_type='user',
            target_id=user.id,
            details=f'用户登出 - 用户名: {user.username}, 浏览器: {request.user_agent}',
            result='success',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        current_app.logger.info(
            f'用户登出 - '
            f'用户名: {user.username}, '
            f'浏览器: {request.user_agent}'
        )

    @staticmethod
    def log_operation(user, action, target_type=None, target_id=None, details=None, result=None):
        """记录操作日志
        
        Args:
            user: 操作用户
            action: 操作行为
            target_type: 目标类型（可选）
            target_id: 目标ID（可选）
            details: 操作详情（可选）
            result: 操作结果（可选，如 'success' 或 'error'）
        """
        log = OperationLog(
            user_id=user.id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            result=result,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    
    @staticmethod
    def get_user_logs(user_id, page=1, per_page=20, start_date=None, end_date=None):
        """获取用户操作日志"""
        query = OperationLog.query.filter_by(user_id=user_id)
        
        if start_date:
            query = query.filter(OperationLog.created_at >= start_date)
        if end_date:
            query = query.filter(OperationLog.created_at <= end_date)
            
        return query.order_by(OperationLog.created_at.desc())\
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
    
    @staticmethod
    def get_system_logs(days=30):
        """获取系统日志
        
        Args:
            days: 获取最近几天的日志
            
        Returns:
            List[OperationLog]: 日志列表
        """
        start_date = datetime.now(UTC) - timedelta(days=days)
        return OperationLog.query.filter(
            OperationLog.created_at >= start_date
        ).order_by(OperationLog.created_at.desc()).all()
    
    @staticmethod
    def clean_old_logs(days=90):
        """清理旧日志
        
        Args:
            days: 保留最近几天的日志
            
        Returns:
            int: 清理的日志数量
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        result = OperationLog.query.filter(
            OperationLog.created_at < cutoff_date
        ).delete()
        db.session.commit()
        return result

operation_log_service = OperationLogService() 