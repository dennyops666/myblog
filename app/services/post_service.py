"""
文件名：post_service.py
描述：文章服务类
作者：denny
创建日期：2025-02-16
"""

from datetime import datetime
from sqlalchemy import extract, func, desc
from app.models import Post, Tag, db
from app.utils.markdown import markdown_to_html

class PostService:
    @staticmethod
    def create_post(title, content, category_id, author_id, summary=None, tags=None, status=0):
        """创建新文章"""
        if not title or not content:
            raise ValueError("标题和内容不能为空")
            
        # 解析Markdown内容
        parsed = markdown_to_html(content)
        
        post = Post(
            title=title,
            content=content,
            html_content=parsed['html'],
            toc=parsed['toc'],
            category_id=category_id,
            author_id=author_id,
            summary=summary,
            status=status
        )
        
        if tags:
            post.tags = tags
            
        db.session.add(post)
        db.session.commit()
        return post
    
    @staticmethod
    def get_post_by_id(post_id):
        """根据ID获取文章"""
        return Post.query.get(post_id)
    
    @staticmethod
    def get_posts_by_category(category_id, page=1, per_page=10):
        """获取分类下的文章列表"""
        return Post.query.filter_by(category_id=category_id, status=1)\
            .order_by(Post.created_at.desc())\
            .paginate(page=page, per_page=per_page)
    
    @staticmethod
    def get_posts_by_tag(tag_id, page=1, per_page=10):
        """获取标签下的文章列表"""
        tag = Tag.query.get(tag_id)
        if tag:
            return tag.posts.filter_by(status=1)\
                .order_by(Post.created_at.desc())\
                .paginate(page=page, per_page=per_page)
        return None
    
    @staticmethod
    def get_posts_by_page(page=1, per_page=10):
        """分页获取文章列表"""
        return Post.query.filter_by(status=1)\
            .order_by(Post.is_sticky.desc(), Post.created_at.desc())\
            .paginate(page=page, per_page=per_page)
    
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
        year_col = extract('year', Post.created_at).label('year')
        month_col = extract('month', Post.created_at).label('month')
        count_col = func.count(Post.id).label('count')
        
        archives = db.session.query(
            year_col,
            month_col,
            count_col
        ).filter(Post.status == 1)\
        .group_by(year_col, month_col)\
        .order_by(desc(year_col), desc(month_col))\
        .all()
        
        result = []
        for year, month, count in archives:
            result.append({
                'year': int(year),
                'month': int(month),
                'count': count
            })
        return result
    
    @staticmethod
    def update_post(post, **kwargs):
        """更新文章"""
        for key, value in kwargs.items():
            if key == 'content':
                post.update_content(value)
            else:
                setattr(post, key, value)
        db.session.commit()
        return post
    
    @staticmethod
    def delete_post(post):
        """删除文章"""
        db.session.delete(post)
        db.session.commit()
    
    @staticmethod
    def search_posts(keyword, page=1, per_page=10):
        """搜索文章"""
        return Post.query.filter(
            Post.status == 1,
            (Post.title.ilike(f'%{keyword}%') |
             Post.content.ilike(f'%{keyword}%'))
        ).order_by(Post.created_at.desc())\
        .paginate(page=page, per_page=per_page) 