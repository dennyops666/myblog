"""
文件名：log.py
描述：日志服务
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, timedelta, UTC
from typing import List, Optional
from app.models.operation_log import OperationLog
from app.extensions import db

class LogService:
    """日志服务类"""
    
    @staticmethod
    def log_action(user_id: int, action: str, details: str = None) -> OperationLog:
        """记录用户操作
        
        Args:
            user_id: 用户ID
            action: 操作类型
            details: 操作详情
            
        Returns:
            OperationLog: 操作日志记录
        """
        log = OperationLog(
            user_id=user_id,
            action=action,
            details=details,
            created_at=datetime.now(UTC)
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def get_user_logs(user_id: int, start_date: Optional[datetime] = None, 
                      end_date: Optional[datetime] = None) -> List[OperationLog]:
        """获取用户日志
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[OperationLog]: 日志列表
        """
        query = OperationLog.query.filter_by(user_id=user_id)
        
        if start_date:
            query = query.filter(OperationLog.created_at >= start_date)
        if end_date:
            query = query.filter(OperationLog.created_at <= end_date)
            
        return query.order_by(OperationLog.created_at.desc()).all()
    
    @staticmethod
    def get_system_logs(days: int = 30) -> List[OperationLog]:
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
    def clean_old_logs(days: int = 90) -> int:
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