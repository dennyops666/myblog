"""
文件名：markdown.py
描述：Markdown工具类
作者：denny
创建日期：2024-03-21
"""

import markdown
import bleach
from bleach.sanitizer import ALLOWED_TAGS, ALLOWED_ATTRIBUTES
from typing import Optional, Dict

# 允许的HTML标签
CUSTOM_ALLOWED_TAGS = list(ALLOWED_TAGS) + [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'div', 'span', 'br', 'hr',
    'ul', 'ol', 'li',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'img', 'a',
    'code', 'pre',
    'blockquote',
    'strong', 'em', 'del'
]

# 允许的HTML属性
CUSTOM_ALLOWED_ATTRIBUTES = {
    **ALLOWED_ATTRIBUTES,
    'img': ['src', 'alt', 'title'],
    'a': ['href', 'title', 'target'],
    'code': ['class'],
    'pre': ['class']
}

class MarkdownService:
    """Markdown服务类"""
    
    def __init__(self):
        """初始化Markdown服务"""
        self.md = markdown.Markdown(
            extensions=[
                'markdown.extensions.fenced_code',  # 代码块
                'markdown.extensions.tables',       # 表格
                'markdown.extensions.codehilite',   # 代码高亮
                'markdown.extensions.toc',          # 目录
                'markdown.extensions.nl2br'         # 换行
            ]
        )
        
    def convert(self, text: Optional[str], clean: bool = True) -> Dict:
        """将Markdown文本转换为HTML
        
        Args:
            text: Markdown文本
            clean: 是否清理HTML标签
            
        Returns:
            dict: 包含HTML和目录的字典
        """
        if not text:
            return {'html': '', 'toc': ''}
            
        # 转换Markdown为HTML
        html = self.md.convert(text)
        toc = self.md.toc if hasattr(self.md, 'toc') else ''
        
        # 清理HTML标签
        if clean:
            html = bleach.clean(
                html,
                tags=CUSTOM_ALLOWED_TAGS,
                attributes=CUSTOM_ALLOWED_ATTRIBUTES,
                strip=True
            )
            
        return {'html': html, 'toc': toc}
        
def markdown_to_html(text: Optional[str], clean: bool = True) -> str:
    """将Markdown文本转换为HTML（兼容函数）
    
    Args:
        text: Markdown文本
        clean: 是否清理HTML标签
        
    Returns:
        str: HTML文本
    """
    service = MarkdownService()
    result = service.convert(text, clean)
    return result['html']