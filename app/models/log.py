"""
日志模型
创建日期: 2025-02-16
"""
from datetime import datetime, UTC
from app.extensions import db

class OperationLog(db.Model):
    """操作日志模型"""
    __tablename__ = 'operation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    # 关系
    user = db.relationship('User', backref=db.backref('operation_logs', lazy=True))
    
    def __repr__(self):
        return f'<OperationLog {self.action}>' 