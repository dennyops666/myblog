"""
文件名：markdown.py
描述：Markdown 工具函数
作者：denny
创建日期：2025-02-16
"""

import re
import markdown
import bleach
from bleach.sanitizer import ALLOWED_ATTRIBUTES, ALLOWED_PROTOCOLS
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound
from markdown.extensions import fenced_code, toc, tables, attr_list

# 创建允许的HTML标签列表
ALLOWED_TAGS = [
    'p', 'div', 'span', 'pre', 'code', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'strong', 'em', 'a', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'ul', 'ol', 'li', 'blockquote', 'hr', 'br', 'sup', 'sub', 'del'
]

# 扩展允许的属性
ALLOWED_ATTRIBUTES.update({
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'a': ['href', 'title', 'rel'],
    'code': ['class'],
    'pre': ['class'],
    '*': ['id', 'class']
})

class HighlightRenderer(markdown.extensions.Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(CodeBlockPreprocessor(md), 'highlight', 175)

class CodeBlockPreprocessor(markdown.preprocessors.Preprocessor):
    def run(self, lines):
        new_lines = []
        in_code_block = False
        code_block_lines = []
        language = None
        
        for line in lines:
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    language = line.strip()[3:].strip() or None
                    code_block_lines = []
                else:
                    in_code_block = False
                    code = '\n'.join(code_block_lines)
                    try:
                        if language:
                            lexer = get_lexer_by_name(language)
                        else:
                            lexer = guess_lexer(code)
                    except ClassNotFound:
                        lexer = get_lexer_by_name('text')
                        
                    formatter = HtmlFormatter(style='default', cssclass='highlight')
                    highlighted = highlight(code, lexer, formatter)
                    new_lines.append(highlighted)
            elif in_code_block:
                code_block_lines.append(line)
            else:
                new_lines.append(line)
                
        return new_lines

def markdown_to_html(content):
    """将 Markdown 转换为 HTML，并提取目录结构"""
    if not content:
        return {'html': '', 'toc': []}
        
    # 创建 Markdown 实例
    md = markdown.Markdown(extensions=[
        'fenced_code',
        'codehilite',
        'tables',
        'toc',
        'attr_list',
        'nl2br',
        HighlightRenderer()
    ], extension_configs={
        'toc': {
            'permalink': True,
            'toc_depth': 3
        },
        'codehilite': {
            'css_class': 'highlight',
            'guess_lang': False
        }
    })
    
    # 转换 Markdown 为 HTML
    html = md.convert(content)
    
    # 提取目录结构
    toc_html = getattr(md, 'toc', '')
    toc_items = []
    if toc_html:
        # 解析目录 HTML 为列表结构
        pattern = r'<a href="#(.+?)">(.+?)</a>'
        matches = re.finditer(pattern, toc_html)
        for match in matches:
            anchor, title = match.groups()
            # 计算标题级别（通过正则匹配 h1_, h2_ 等前缀）
            level_match = re.match(r'^h(\d+)_', anchor)
            if level_match:
                level = int(level_match.group(1))
                toc_items.append({
                    'level': level,
                    'anchor': anchor,
                    'title': title
                })
    
    # 清理 HTML
    def clean_href(name, value):
        """清理链接，只允许安全的协议和内部链接"""
        if name == 'href':
            url = value.lower()
            if url.startswith('#') or url.startswith('/'):
                return value
            if any(url.startswith(protocol + ':') for protocol in ALLOWED_PROTOCOLS):
                return value
            return ''
        return value
    
    html = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        filters=[clean_href]
    )
    
    return {
        'html': html,
        'toc': toc_items
    }