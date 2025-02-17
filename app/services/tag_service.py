"""
文件名：tag_service.py
描述：标签服务
作者：denny
创建日期：2024-03-20
"""

from app.models import Tag
from app.extensions import db
from sqlalchemy import desc

class TagService:
    """标签服务类"""
    
    @staticmethod
    def create_tag(name, description=None):
        """创建标签"""
        if not name:
            raise ValueError("标签名称不能为空")
        if len(name) > 50:
            raise ValueError("标签名称不能超过50个字符")
        
        tag = Tag(name=name, description=description)
        db.session.add(tag)
        db.session.commit()
        return tag
    
    @staticmethod
    def get_tag_by_id(tag_id):
        """根据ID获取标签"""
        return db.session.get(Tag, tag_id)
    
    @staticmethod
    def get_tag_by_name(name):
        """根据名称获取标签"""
        return Tag.query.filter_by(name=name).first()
    
    @staticmethod
    def get_all_tags():
        """获取所有标签"""
        return Tag.query.all()
    
    @staticmethod
    def update_tag(tag, **kwargs):
        """更新标签
        
        参数：
            tag: Tag对象或标签ID
            **kwargs: 要更新的字段
        """
        if isinstance(tag, int):
            tag = db.session.get(Tag, tag)
        if not tag:
            raise ValueError("标签不存在")
            
        for key, value in kwargs.items():
            if hasattr(tag, key):
                setattr(tag, key, value)
        
        try:
            db.session.commit()
            return tag
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"更新标签失败：{str(e)}")
    
    @staticmethod
    def delete_tag(tag):
        """删除标签"""
        if isinstance(tag, int):
            tag = db.session.get(Tag, tag)
        if not tag:
            raise ValueError("标签不存在")
            
        if tag.posts.count() > 0:
            raise ValueError("该标签下还有文章，无法删除")
            
        try:
            db.session.delete(tag)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"删除标签失败：{str(e)}")
    
    @staticmethod
    def get_posts_by_tag(tag_id, page=1, per_page=10):
        """获取标签下的文章列表（分页）"""
        tag = TagService.get_tag_by_id(tag_id)
        if not tag:
            raise ValueError("标签不存在")
        
        return tag.posts.order_by(
            desc('created_at')
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    @staticmethod
    def merge_tags(source_tag_id, target_tag_id):
        """合并标签
        
        将source_tag的所有文章关联转移到target_tag，然后删除source_tag
        
        Args:
            source_tag_id: 源标签ID
            target_tag_id: 目标标签ID
            
        Returns:
            bool: 合并成功返回True
            
        Raises:
            ValueError: 标签不存在或合并失败时抛出
        """
        source_tag = db.session.get(Tag, source_tag_id)
        target_tag = db.session.get(Tag, target_tag_id)
        
        if not source_tag or not target_tag:
            raise ValueError('源标签或目标标签不存在')
            
        if source_tag_id == target_tag_id:
            raise ValueError('不能合并相同的标签')
        
        try:
            # 将源标签的所有文章关联转移到目标标签
            for post in source_tag.posts:
                if target_tag not in post.tags:
                    post.tags.append(target_tag)
            
            # 删除源标签
            db.session.delete(source_tag)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise ValueError(f'标签合并失败：{str(e)}') 