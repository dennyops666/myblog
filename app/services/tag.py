"""
文件名：tag.py
描述：标签服务
作者：denny
创建日期：2024-03-21
"""

from flask import current_app
from app.models import Tag, db, Post, PostStatus
from app.extensions import db
from app.services import SecurityService
from typing import List, Optional, Dict
from sqlalchemy import func
from datetime import datetime, UTC

class TagService:
    def __init__(self):
        self.security = SecurityService()
    
    def create_tag(self, name, slug, description=None):
        """创建标签
        
        Args:
            name: 标签名称
            slug: 标签别名
            description: 标签描述（可选）
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            # 检查名称是否已存在
            if Tag.query.filter_by(name=name).first():
                return {'status': 'error', 'message': '标签名称已存在'}
            
            # 检查别名是否已存在
            if Tag.query.filter_by(slug=slug).first():
                return {'status': 'error', 'message': '标签别名已存在'}
            
            tag = Tag(
                name=name,
                slug=slug,
                description=description,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            db.session.add(tag)
            db.session.commit()
            return {'status': 'success', 'message': '标签创建成功', 'tag': tag}
            
        except Exception as e:
            db.session.rollback()
            return {'status': 'error', 'message': f'创建标签失败：{str(e)}'}
    
    def get_tag_by_id(self, tag_id: int) -> Optional[Tag]:
        """根据ID获取标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            Tag: 标签对象
        """
        return db.session.get(Tag, tag_id)
    
    def get_tag_by_slug(self, slug: str) -> Optional[Tag]:
        """根据别名获取标签
        
        Args:
            slug: 标签别名
            
        Returns:
            Tag: 标签对象
        """
        return Tag.query.filter_by(slug=slug).first()
    
    def get_all_tags(self) -> List[Tag]:
        """获取所有标签
        
        Returns:
            list: 标签列表
        """
        current_app.logger.info("TagService: 正在获取所有标签...")
        tags = Tag.query.all()
        
        # 为每个标签计算已发布文章的数量
        for tag in tags:
            from app.models import Post, PostStatus
            tag.post_count = Post.query.filter(
                Post.tags.any(id=tag.id),
                Post.status == PostStatus.PUBLISHED
            ).count()
            
        current_app.logger.info(f"TagService: 获取到 {len(tags)} 个标签")
        return tags
    
    def update_tag(self, tag_id: int, name: str = None, 
                  slug: str = None, description: str = None) -> Dict:
        """更新标签
        
        Args:
            tag_id: 标签ID
            name: 新的标签名称
            slug: 新的标签别名
            description: 标签描述
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            tag = self.get_tag_by_id(tag_id)
            if not tag:
                return {'status': 'error', 'message': '标签不存在'}
                
            if name and name != tag.name:
                # 检查新名称是否已存在
                if Tag.query.filter_by(name=name).first():
                    return {'status': 'error', 'message': '标签名已存在'}
                tag.name = name
                
            if slug and slug != tag.slug:
                # 检查新别名是否已存在
                if Tag.query.filter_by(slug=slug).first():
                    return {'status': 'error', 'message': '标签别名已存在'}
                tag.slug = slug
                
            if description is not None:
                tag.description = description
            
            tag.updated_at = datetime.now(UTC)
            db.session.commit()
            return {'status': 'success', 'message': '标签更新成功', 'tag': tag}
            
        except Exception as e:
            db.session.rollback()
            return {'status': 'error', 'message': f'更新标签失败：{str(e)}'}
    
    def delete_tag(self, tag_id: int) -> Dict:
        """删除标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            tag = self.get_tag_by_id(tag_id)
            if not tag:
                return {'status': 'error', 'message': '标签不存在'}
            
            # 检查标签是否有关联的文章
            if len(tag.posts) > 0:
                return {'status': 'error', 'message': '该标签下还有关联的文章，无法删除'}
                
            db.session.delete(tag)
            db.session.commit()
            return {'status': 'success', 'message': '标签删除成功'}
            
        except Exception as e:
            db.session.rollback()
            return {'status': 'error', 'message': f'删除标签失败：{str(e)}'}
    
    def get_tag_list(self, page=1, per_page=10):
        """获取标签列表
        
        Args:
            page: 页码
            per_page: 每页数量
            
        Returns:
            Pagination: 分页对象
        """
        # 先获取所有标签
        query = Tag.query.order_by(Tag.created_at.desc())
        
        # 执行分页查询
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 为分页后的标签计算文章数量
        for tag in pagination.items:
            from app.models import Post, PostStatus
            tag.post_count = Post.query.filter(
                Post.tags.any(id=tag.id),
                Post.status == PostStatus.PUBLISHED
            ).count()
        
        return pagination
    
    def search_tags(self, keyword, page=1, per_page=10):
        """搜索标签"""
        return Tag.query.filter(
            Tag.name.ilike(f'%{keyword}%')
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    def get_tag_stats(self):
        """获取标签统计信息"""
        total_tags = Tag.query.count()
        tags_with_posts = Tag.query.filter(
            Tag.posts.any()
        ).count()
        
        # 获取每个标签的文章数量
        tag_post_counts = []
        for tag in Tag.query.all():
            post_count = Post.query.filter(
                Post.tags.any(id=tag.id),
                Post.status == PostStatus.PUBLISHED
            ).count()
            tag_post_counts.append({
                'id': tag.id,
                'name': tag.name,
                'post_count': post_count
            })
        
        return {
            'total_tags': total_tags,
            'tags_with_posts': tags_with_posts,
            'tag_post_counts': tag_post_counts
        }
    
    def get_tags_with_post_count(self) -> List[Dict]:
        """获取标签及其文章数量
        
        Returns:
            list: 包含标签信息和文章数量的字典列表
        """
        from app.models import Post
        tags = Tag.query.all()
        result = []
        
        for tag in tags:
            post_count = Post.query.filter(
                Post.tags.any(id=tag.id),
                Post.status == 1
            ).count()
            result.append({
                'id': tag.id,
                'name': tag.name,
                'slug': tag.slug,
                'post_count': post_count
            })
            
        return result
    
    def merge_tags(self, source_id: int, target_id: int) -> Dict:
        """合并标签
        
        Args:
            source_id: 源标签ID
            target_id: 目标标签ID
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            source_tag = db.session.get(Tag, source_id)
            target_tag = db.session.get(Tag, target_id)
            
            if not source_tag or not target_tag:
                return {'status': 'error', 'message': '标签不存在'}
                
            if source_id == target_id:
                return {'status': 'error', 'message': '不能合并相同的标签'}
                
            # 将源标签的文章关联到目标标签
            for post in source_tag.posts:
                if target_tag not in post.tags:
                    post.tags.append(target_tag)
                    
            # 删除源标签
            db.session.delete(source_tag)
            db.session.commit()
            
            return {
                'status': 'success',
                'message': '标签合并成功',
                'target_tag': target_tag
            }
            
        except Exception as e:
            db.session.rollback()
            return {'status': 'error', 'message': f'合并标签失败：{str(e)}'} 