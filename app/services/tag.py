"""
文件名：tag.py
描述：标签服务
作者：denny
创建日期：2024-03-21
"""

from flask import current_app
from app.models import Tag, db
from app.extensions import db
from app.services import SecurityService
from typing import List, Optional, Dict
from sqlalchemy import func

class TagService:
    def __init__(self):
        self.security = SecurityService()
    
    def create_tag(self, name: str, slug: str) -> Dict:
        """创建标签
        
        Args:
            name: 标签名称
            slug: 标签别名
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            # 检查标签名是否已存在
            if Tag.query.filter_by(name=name).first():
                return {'status': 'error', 'message': '标签名已存在'}
                
            # 检查别名是否已存在
            if Tag.query.filter_by(slug=slug).first():
                return {'status': 'error', 'message': '标签别名已存在'}
                
            tag = Tag(name=name, slug=slug)
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
        return Tag.query.get(tag_id)
    
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
        return Tag.query.all()
    
    def update_tag(self, tag_id: int, name: str = None, 
                  slug: str = None) -> Dict:
        """更新标签
        
        Args:
            tag_id: 标签ID
            name: 新的标签名称
            slug: 新的标签别名
            
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
                
            db.session.delete(tag)
            db.session.commit()
            return {'status': 'success', 'message': '标签删除成功'}
            
        except Exception as e:
            db.session.rollback()
            return {'status': 'error', 'message': f'删除标签失败：{str(e)}'}
    
    def get_tag_list(self, page=1, per_page=10):
        """获取标签列表（分页）
        
        Args:
            page: 页码
            per_page: 每页数量
            
        Returns:
            dict: 包含分页信息的字典
        """
        from app.models import Post
        
        pagination = Tag.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        tags = []
        for tag in pagination.items:
            post_count = Post.query.filter(
                Post.tags.any(id=tag.id),
                Post.status == 1
            ).count()
            tags.append({
                'id': tag.id,
                'name': tag.name,
                'slug': tag.slug,
                'post_count': post_count,
                'created_at': tag.created_at
            })
            
        return {
            'items': tags,
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num
        }
    
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
            tag_post_counts.append({
                'id': tag.id,
                'name': tag.name,
                'post_count': tag.posts.count()
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
            source_tag = Tag.query.get(source_id)
            target_tag = Tag.query.get(target_id)
            
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