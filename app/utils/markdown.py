"""
文件名：markdown.py
描述：Markdown 工具函数
作者：denny
创建日期：2024-03-21
"""

import re
import markdown
import bleach
from bleach.sanitizer import Cleaner
from bleach.linkifier import LinkifyFilter
from bleach.css_sanitizer import CSSSanitizer
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension

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
    """清理XSS相关内容，但保留Markdown特殊字符"""
    if not isinstance(text, str):
        return text
    # 只清理明确的XSS模式，保留Markdown特殊字符
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'data:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'vbscript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\son\w+\s*=', '', text, flags=re.IGNORECASE)
    return text

def markdown_to_html(content):
    """将 Markdown 转换为 HTML"""
    if not content:
        return {'html': '', 'toc': []}
        
    # 配置 Markdown 扩展
    extensions = [
        FencedCodeExtension(),
        CodeHiliteExtension(css_class='highlight', guess_lang=False),
        'markdown.extensions.tables',
        'markdown.extensions.toc',
        'markdown.extensions.nl2br',
        'markdown.extensions.sane_lists',
        'markdown.extensions.attr_list',
        'markdown.extensions.def_list',
        'markdown.extensions.footnotes',
        'markdown.extensions.abbr',
        'markdown.extensions.meta'
    ]
    
    # 配置扩展选项
    extension_configs = {
        'markdown.extensions.toc': {
            'slugify': lambda value, separator: value,  # 使用原始文本作为ID
            'permalink': True,
            'toc_depth': 3,
            'anchorlink': True,
            'separator': '-'
        },
        'markdown.extensions.codehilite': {
            'css_class': 'highlight',
            'guess_lang': False,
            'use_pygments': True,
            'noclasses': False
        }
    }
    
    # 创建 Markdown 实例
    md = markdown.Markdown(
        extensions=extensions,
        extension_configs=extension_configs,
        output_format='html5'
    )
    
    # 预处理内容，保护特殊字符
    content = content.replace('&', '&amp;')
    content = content.replace('<', '&lt;')
    content = content.replace('>', '&gt;')
    
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
        'tr', 'th', 'td', 'hr', 'sup', 'sub', 'dl', 'dt', 'dd',
        'div', 'span', 'abbr', 'acronym', 'del', 'ins'
    ]
    
    allowed_attributes = {
        'a': ['href', 'title', 'id', 'class', 'rel'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'code': ['class'],
        'pre': ['class'],
        'span': ['class', 'style'],
        'div': ['class'],
        'p': ['class'],
        'td': ['colspan', 'rowspan', 'align'],
        'th': ['colspan', 'rowspan', 'align'],
        '*': ['id', 'class', 'title']
    }

    # 配置允许的CSS属性
    allowed_css_properties = [
        'color', 'background-color', 'text-align', 'font-weight',
        'font-style', 'text-decoration', 'margin', 'padding',
        'border', 'width', 'height'
    ]

    # 创建CSS清理器
    css_sanitizer = CSSSanitizer(
        allowed_css_properties=allowed_css_properties,
        allowed_svg_properties=[],
    )

    # 创建自定义清理器，配置更宽松的规则
    cleaner = Cleaner(
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=['http', 'https', 'mailto', 'tel'],
        strip=True,
        strip_comments=True,
        filters=[LinkifyFilter],
        css_sanitizer=css_sanitizer
    )
    
    # 清理 HTML，但保持基本的Markdown格式
    html = cleaner.clean(html)
    
    # 恢复特殊字符的HTML实体
    html = html.replace('&amp;', '&')
    html = html.replace('&lt;', '<')
    html = html.replace('&gt;', '>')
    
    return {
        'html': html,
        'toc': toc_items
    }

def _process_toc_tokens(tokens, level=1):
    """处理目录标记，生成扁平化的目录列表"""
    items = []
    for token in tokens:
        item = {
            'level': level,
            'text': token['name'],
            'id': f"header-{token['id']}",  # 添加header-前缀
            'anchor': f"header-{token['id']}"  # 添加header-前缀
        }
        items.append(item)
        if 'children' in token:
            items.extend(_process_toc_tokens(token['children'], level + 1))
    return items