"""
文件名：post_service.py
描述：文章服务类
作者：denny
创建日期：2025-02-16
"""

from datetime import datetime
from sqlalchemy import extract, func, desc
from app.models import Post, Tag, db, Category
from app.utils.markdown import markdown_to_html
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_

class PostService:
    @staticmethod
    def create_post(title, content, category_id, author_id, status=1, is_sticky=False):
        """创建新文章"""
        try:
            if not title or not content:
                raise ValueError("标题和内容不能为空")
            
            # 验证分类ID
            category = db.session.get(Category, category_id)
            if not category:
                raise ValueError("无效的分类ID")
            
            # 解析Markdown内容
            parsed = markdown_to_html(content)
            
            post = Post(
                title=title,
                content=content,
                html_content=parsed['html'],
                toc=parsed['toc'],
                category_id=category_id,
                author_id=author_id,
                status=status,
                is_sticky=is_sticky
            )
            
            db.session.add(post)
            db.session.commit()
            return post
        except IntegrityError:
            db.session.rollback()
            raise ValueError("文章创建失败，请检查输入")
    
    @staticmethod
    def get_post_by_id(post_id):
        """根据ID获取文章"""
        return db.session.get(Post, post_id)
    
    @staticmethod
    def get_posts_by_category(category_id, page=1, per_page=10):
        """获取分类下的文章列表"""
        return Post.query.filter_by(
            category_id=category_id, 
            status=1
        ).order_by(
            desc(Post.created_at)
        ).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
    
    @staticmethod
    def get_posts_by_tag(tag_id, page=1, per_page=10):
        """获取标签下的文章列表"""
        return Post.query.filter(
            Post.tags.any(id=tag_id),
            Post.status == 1
        ).order_by(
            desc(Post.created_at)
        ).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
    
    @staticmethod
    def get_posts_by_page(page=1, per_page=10, only_published=True):
        """分页获取文章列表"""
        query = Post.query
        if only_published:
            query = query.filter_by(status=1)
        return query.order_by(desc(Post.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    @staticmethod
    def get_total_posts():
        """获取文章总数"""
        return Post.query.filter_by(status=1).count()
    
    @staticmethod
    def get_recent_posts(limit=5):
        """获取最近文章"""
        return Post.query.filter_by(status=1)\
            .order_by(Post.created_at.desc())\
            .limit(limit).all()
    
    @staticmethod
    def get_sticky_posts():
        """获取置顶文章"""
        return Post.query.filter_by(status=1, is_sticky=True)\
            .order_by(Post.created_at.desc()).all()
    
    @staticmethod
    def get_related_posts(post, limit=5):
        """获取相关文章"""
        # 根据相同标签获取相关文章
        tag_ids = [tag.id for tag in post.tags]
        if tag_ids:
            return Post.query.filter(
                Post.id != post.id,
                Post.status == 1,
                Post.tags.any(Tag.id.in_(tag_ids))
            ).limit(limit).all()
        return []
    
    @staticmethod
    def get_prev_next_post(post):
        """获取上一篇和下一篇文章"""
        prev_post = Post.query.filter(
            Post.status == 1,
            Post.created_at < post.created_at
        ).order_by(Post.created_at.desc()).first()
        
        next_post = Post.query.filter(
            Post.status == 1,
            Post.created_at > post.created_at
        ).order_by(Post.created_at.asc()).first()
        
        return {
            'prev': prev_post,
            'next': next_post
        }
    
    @staticmethod
    def get_archives():
        """获取文章归档"""
        posts = Post.query.filter_by(status=1).order_by(desc(Post.created_at)).all()
        archives = {}
        
        for post in posts:
            year = post.created_at.year
            month = post.created_at.month
            key = f"{year}-{month:02d}"
            
            if key not in archives:
                archives[key] = []
            archives[key].append(post)
            
        return archives
    
    @staticmethod
    def get_posts_by_archive(year, month, page=1, per_page=10):
        """获取归档下的文章"""
        return Post.query.filter(
            and_(
                extract('year', Post.created_at) == year,
                extract('month', Post.created_at) == month,
                Post.status == 1
            )
        ).order_by(
            desc(Post.created_at)
        ).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
    
    @staticmethod
    def update_post(post, **kwargs):
        """更新文章"""
        for key, value in kwargs.items():
            if hasattr(post, key):
                setattr(post, key, value)
        
        # 如果更新了content，重新生成HTML内容
        if 'content' in kwargs:
            post.update_html_content()
        
        try:
            db.session.commit()
            return post
        except Exception as e:
            db.session.rollback()
            raise ValueError(f'更新文章失败：{str(e)}')
    
    @staticmethod
    def delete_post(post):
        """删除文章"""
        try:
            db.session.delete(post)
            db.session.commit()
        except:
            db.session.rollback()
            raise ValueError("文章删除失败")
    
    @staticmethod
    def search_posts(search_query, page=1, per_page=10):
        """搜索文章"""
        return Post.query.filter(
            and_(
                search_query,
                Post.status == 1
            )
        ).order_by(
            desc(Post.created_at)
        ).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        ) 