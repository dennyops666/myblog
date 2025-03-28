"""
文件名：pagination.py
描述：分页工具类
作者：denny
"""

from math import ceil

class Pagination:
    def __init__(self, query, page, per_page):
        self.query = query
        self.page = page
        self.per_page = per_page
        self.total = query.count()
        self.items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    @property
    def pages(self):
        """总页数"""
        if self.per_page == 0 or self.total == 0:
            return 0
        return int(ceil(self.total / float(self.per_page)))
    
    @property
    def has_prev(self):
        """是否有上一页"""
        return self.page > 1
    
    @property
    def has_next(self):
        """是否有下一页"""
        return self.page < self.pages
    
    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        """生成分页序号"""
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num 