"""
文件名：tag_service.py
描述：标签服务
作者：denny
创建日期：2024-03-20
"""

from app.models import Tag
from app.extensions import db

class TagService:
    """标签服务类"""
    
    @staticmethod
    def create_tag(name):
        """创建标签"""
        tag = Tag(name=name)
        db.session.add(tag)
        db.session.commit()
        return tag
    
    @staticmethod
    def get_tag_by_id(tag_id):
        """根据ID获取标签"""
        return Tag.query.get(tag_id)
    
    @staticmethod
    def get_tag_by_name(name):
        """根据名称获取标签"""
        return Tag.query.filter_by(name=name).first()
    
    @staticmethod
    def get_all_tags():
        """获取所有标签"""
        return Tag.query.all()
    
    @staticmethod
    def update_tag(tag_id, name):
        """更新标签"""
        tag = TagService.get_tag_by_id(tag_id)
        if tag:
            tag.name = name
            db.session.commit()
        return tag
    
    @staticmethod
    def delete_tag(tag_id):
        """删除标签"""
        tag = TagService.get_tag_by_id(tag_id)
        if tag:
            db.session.delete(tag)
            db.session.commit()
        return True 