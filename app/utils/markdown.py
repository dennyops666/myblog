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
from bs4 import BeautifulSoup

class MarkdownService:
    @staticmethod
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

    @staticmethod
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

    def convert(self, content):
        """将 Markdown 转换为 HTML"""
        if not content:
            return {'html': '', 'toc': []}
            
        # 配置 Markdown 扩展
        extensions = [
            'markdown.extensions.fenced_code',
            'markdown.extensions.tables',
            'markdown.extensions.toc',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists',
            'markdown.extensions.attr_list',
            'markdown.extensions.def_list',
            'markdown.extensions.footnotes',
            'markdown.extensions.abbr',
            'markdown.extensions.meta',
            'markdown.extensions.codehilite'
        ]
        
        # 配置扩展选项
        extension_configs = {
            'markdown.extensions.toc': {
                'slugify': lambda value, separator: value,  # 不做任何转换，保持原始文本
                'permalink': False,  # 禁用自动生成的永久链接
                'toc_depth': 3,
                'anchorlink': False,  # 禁用自动锚点链接
                'separator': '-'
            },
            'markdown.extensions.fenced_code': {
                'lang_prefix': 'language-'
            },
            'markdown.extensions.codehilite': {
                'css_class': 'highlight',
                'guess_lang': False
            }
        }
        
        # 创建 Markdown 实例
        md = markdown.Markdown(
            extensions=extensions,
            extension_configs=extension_configs,
            output_format='html5'
        )
        
        # 预处理内容，保护特殊字符
        content = self.clean_xss(content)
        
        # 转换 Markdown 为 HTML
        html = md.convert(content)
        
        # 提取目录
        toc_items = []
        if hasattr(md, 'toc_tokens'):
            toc_items = self._process_toc_tokens(md.toc_tokens)
        
        # 修改 HTML 中的标题 ID
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            # 获取标题文本
            text = tag.get_text().strip()
            # 设置 ID
            tag['id'] = text
        
        html = str(soup)
        
        # 配置允许的 HTML 标签和属性
        allowed_tags = [
            'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'blockquote', 'code', 'pre',
            'strong', 'em', 'a', 'img', 'table', 'thead', 'tbody',
            'tr', 'th', 'td', 'hr', 'sup', 'sub', 'dl', 'dt', 'dd',
            'div', 'span'
        ]
        
        allowed_attributes = {
            'a': ['href', 'title', 'rel', 'class'],
            'img': ['src', 'alt', 'title'],
            'code': ['class'],
            'pre': ['class'],
            'span': ['class'],
            'div': ['class'],
            'p': ['class'],
            'td': ['colspan', 'rowspan'],
            'th': ['colspan', 'rowspan'],
            'h1': ['id'],
            'h2': ['id'],
            'h3': ['id'],
            'h4': ['id'],
            'h5': ['id'],
            'h6': ['id']
        }

        # 创建自定义清理器
        cleaner = Cleaner(
            tags=allowed_tags,
            attributes=allowed_attributes,
            protocols=['http', 'https', 'mailto', 'tel'],
            strip=True,
            strip_comments=True,
            filters=[]
        )
        
        # 清理 HTML
        html = cleaner.clean(html)
        
        return {
            'html': html,
            'toc': toc_items
        }

    def _process_toc_tokens(self, tokens, level=1):
        """处理目录标记，生成扁平化的目录列表"""
        items = []
        for token in tokens:
            item = {
                'level': level,
                'text': token['name'],
                'id': f'header-{token["name"]}',  # 添加 header- 前缀
                'anchor': f'header-{token["name"]}'  # 添加 header- 前缀
            }
            items.append(item)
            if 'children' in token:
                items.extend(self._process_toc_tokens(token['children'], level + 1))
        return items

def markdown_to_html(content):
    """兼容函数，创建MarkdownService实例并调用convert方法"""
    service = MarkdownService()
    return service.convert(content)