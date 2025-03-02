"""
文件名：markdown.py
描述：Markdown 相关的工具函数
作者：denny
创建日期：2024-03-21
"""

import markdown
import bleach
import re
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, TextLexer, PythonLexer
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension
from markdown.extensions.nl2br import Nl2BrExtension

def format_code_block(code, lang=None):
    """格式化代码块，支持语法高亮"""
    # 移除空行
    code = code.strip()
    
    # 获取最小缩进
    lines = code.split('\n')
    min_indent = float('inf')
    for line in lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            min_indent = min(min_indent, indent)
    
    # 移除多余缩进
    if min_indent < float('inf'):
        code = '\n'.join(line[min_indent:] if line.strip() else '' for line in lines)
    
    # 选择合适的词法分析器
    try:
        if lang:
            lexer = get_lexer_by_name(lang, stripall=True)
        else:
            lexer = TextLexer()
    except:
        lexer = TextLexer()
    
    # 生成高亮HTML
    formatter = HtmlFormatter(style='monokai', cssclass='highlight')
    highlighted = highlight(code, lexer, formatter)
    
    # 如果指定了语言，添加语言标签
    if lang:
        return f'<div class="code-block"><div class="code-lang">{lang}</div>{highlighted}</div>'
    return f'<div class="code-block">{highlighted}</div>'

class CustomFencedCodePreprocessor(markdown.preprocessors.Preprocessor):
    """自定义代码块预处理器"""
    FENCED_BLOCK_RE = re.compile(r'''
        (?P<fence>^(?:~{3,}|`{3,}))[ ]*         # 开始标记
        (?:(?P<lang>[a-zA-Z0-9_+-]*)[ ]*)?      # 语言 (可选)
        \n                                       # 换行
        (?P<code>.*?)(?<=\n)                    # 代码内容
        (?P=fence)[ ]*$                         # 结束标记
        ''', re.MULTILINE | re.DOTALL | re.VERBOSE)

    def run(self, lines):
        text = '\n'.join(lines)
        while True:
            m = self.FENCED_BLOCK_RE.search(text)
            if not m:
                break
            lang = m.group('lang')
            code = m.group('code')
            formatted = format_code_block(code, lang)
            placeholder = self.md.htmlStash.store(formatted)
            text = text[:m.start()] + placeholder + text[m.end():]
        return text.split('\n')

class CustomFencedCodeExtension(markdown.Extension):
    """自定义代码块扩展"""
    def extendMarkdown(self, md):
        md.preprocessors.register(CustomFencedCodePreprocessor(md), 'fenced_code_block', 25)

def markdown_to_html(text):
    """将 Markdown 文本转换为 HTML"""
    # 配置 Markdown 扩展
    extensions = [
        'markdown.extensions.extra',  # 包含表格、代码块等扩展
        'markdown.extensions.meta',   # 元数据支持
        'markdown.extensions.nl2br',  # 换行支持
        'markdown.extensions.sane_lists',  # 列表格式化
        'markdown.extensions.smarty',  # 智能标点
        'markdown.extensions.toc',    # 目录支持
        'markdown.extensions.wikilinks',  # Wiki 链接支持
        CustomFencedCodeExtension(),  # 自定义代码块
        CodeHiliteExtension(css_class='highlight'),  # 代码高亮
        TableExtension(),  # 表格支持
        TocExtension(permalink=True)  # 目录支持，带链接
    ]

    # 配置 Markdown 转换器
    md = markdown.Markdown(extensions=extensions, output_format='html5')
    
    # 转换 Markdown 为 HTML
    html = md.convert(text)
    
    # 配置允许的 HTML 标签和属性
    allowed_tags = [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'div', 'em',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'li', 'ol', 'p',
        'pre', 'span', 'strong', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul',
        'dl', 'dt', 'dd'
    ]
    
    allowed_attributes = {
        'a': ['href', 'title', 'class', 'id', 'name'],
        'img': ['src', 'alt', 'title', 'class', 'id'],
        'div': ['class', 'id'],
        'span': ['class', 'id'],
        'code': ['class'],
        'pre': ['class'],
        '*': ['class', 'id']
    }

    # 清理 HTML
    clean_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    return clean_html