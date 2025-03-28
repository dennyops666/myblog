"""
文件名：operation_log.py
描述：操作日志模型
作者：denny
"""

from datetime import datetime, UTC
from app.extensions import db

class OperationLog(db.Model):
    """操作日志模型类"""
    __tablename__ = 'operation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # 操作类型
    target_type = db.Column(db.String(50))  # 目标类型
    target_id = db.Column(db.Integer)  # 目标ID
    details = db.Column(db.Text)  # 详细信息
    result = db.Column(db.String(20))  # 操作结果
    ip_address = db.Column(db.String(50))  # IP地址
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    # 关联关系
    user = db.relationship('User', back_populates='operation_logs')
    
    def __repr__(self):
        return f'<OperationLog {self.action}>' 