"""
文件名：setting.py
描述：站点设置模型
作者：denny
创建日期：2024-03-25
"""

from app.extensions import db
from datetime import datetime

class Setting(db.Model):
    """站点设置模型"""
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __init__(self, key, value, description=None):
        self.key = key
        self.value = value
        self.description = description or key
    
    def __repr__(self):
        return f'<Setting {self.key}>' 