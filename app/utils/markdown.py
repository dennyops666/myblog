"""
文件名：markdown.py
描述：Markdown 工具函数
作者：denny
创建日期：2025-02-16
"""

import re
import markdown
import bleach
from bleach.sanitizer import Cleaner
from bleach.linkifier import LinkifyFilter

def clean_href(attrs, new=False):
    """清理链接属性"""
    href = attrs.get((None, 'href'), '')
    if href:
        # 允许的协议
        allowed_protocols = ['http', 'https', 'mailto', 'tel']
        # 检查协议
        protocol = href.split(':', 1)[0].lower()
        if protocol not in allowed_protocols:
            return None
    return attrs

def clean_xss(text):
    """清理XSS相关内容"""
    if not isinstance(text, str):
        return text
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'data:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'vbscript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\son\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
    text = re.sub(r'alert\s*\([^)]*\)', '', text, flags=re.IGNORECASE)
    return text

def markdown_to_html(content):
    """将 Markdown 转换为 HTML"""
    # 配置 Markdown 扩展
    extensions = [
        'markdown.extensions.fenced_code',  # 代码块
        'markdown.extensions.codehilite',   # 代码高亮
        'markdown.extensions.tables',       # 表格
        'markdown.extensions.toc',          # 目录
        'markdown.extensions.nl2br',        # 换行
        'markdown.extensions.sane_lists',   # 列表
    ]
    
    # 配置扩展选项
    extension_configs = {
        'markdown.extensions.codehilite': {
            'css_class': 'highlight',
            'guess_lang': False
        },
        'markdown.extensions.toc': {
            'permalink': True,
            'toc_depth': 3,
            'anchorlink': True,
            'separator': '-',
            'slugify': lambda value, separator: value  # 保持原始文本作为ID
        }
    }
    
    # 创建 Markdown 实例
    md = markdown.Markdown(
        extensions=extensions,
        extension_configs=extension_configs
    )
    
    # 转换 Markdown 为 HTML
    html = md.convert(content)
    
    # 提取目录
    toc_items = []
    if hasattr(md, 'toc_tokens'):
        toc_items = _process_toc_tokens(md.toc_tokens)
    
    # 配置允许的 HTML 标签和属性
    allowed_tags = [
        'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'code', 'pre',
        'strong', 'em', 'a', 'img', 'table', 'thead', 'tbody',
        'tr', 'th', 'td'
    ]
    
    allowed_attributes = {
        'a': ['href', 'title', 'id', 'class'],
        'img': ['src', 'alt', 'title'],
        'code': ['class'],
        'pre': ['class'],
        '*': ['id', 'class']
    }

    # 创建自定义清理器
    cleaner = Cleaner(
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True,
        strip_comments=True,
        protocols=['http', 'https', 'mailto', 'tel']
    )
    
    # 清理 HTML
    html = cleaner.clean(html)
    
    # 进行额外的XSS清理
    html = clean_xss(html)
    
    return {
        'html': html,
        'toc': toc_items
    }

def _process_toc_tokens(tokens, level=1):
    """处理目录标记，生成扁平化的目录列表
    
    Args:
        tokens: 目录标记列表
        level: 当前目录级别
        
    Returns:
        list: 扁平化的目录列表
    """
    items = []
    for token in tokens:
        item = {
            'level': level,
            'text': token['name'],
            'id': f"header-{token['id']}",  # 添加header-前缀
            'anchor': f"header-{token['id']}"  # 保持一致的ID格式
        }
        items.append(item)
        if 'children' in token:
            items.extend(_process_toc_tokens(token['children'], level + 1))
    return items