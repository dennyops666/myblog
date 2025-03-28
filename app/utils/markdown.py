"""
文件名：markdown.py
描述：Markdown 相关的工具函数
作者：denny
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
    
    # 确保代码的特殊字符被正确转义
    import html
    code = html.escape(code)
    
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
        if lang and lang.lower() in ['javascript', 'js', 'python', 'py', 'java', 'c', 'cpp', 'csharp', 'go', 'php', 'ruby', 'rust', 'sql', 'bash', 'sh', 'html', 'css', 'xml', 'json', 'yaml', 'typescript', 'ts']:
            # 使用指定的词法分析器
            lexer = get_lexer_by_name(lang, stripall=True)
        else:
            # 默认使用普通文本词法分析器
            lexer = TextLexer()
    except Exception as e:
        print(f"获取词法分析器失败: {str(e)}")
        lexer = TextLexer()
    
    # 生成高亮HTML
    formatter = HtmlFormatter(style='monokai', cssclass='highlight', linenos=False)
    
    try:
        highlighted = highlight(code, lexer, formatter)
    except Exception as e:
        print(f"代码高亮失败: {str(e)}")
        # 如果高亮失败，使用简单的pre标签
        highlighted = f'<pre>{code}</pre>'
    
    # 如果指定了语言，添加语言标签
    if lang:
        return f'<div class="code-block">{highlighted}<div class="code-lang">{lang}</div></div>'
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
            if lang:
                lang = lang.strip().lower()
                
            code = m.group('code')
            
            # 打印调试信息
            print(f"识别到代码块，语言: {lang}, 代码长度: {len(code)}")
            
            try:
                formatted = format_code_block(code, lang)
                placeholder = self.md.htmlStash.store(formatted)
                text = text[:m.start()] + placeholder + text[m.end():]
            except Exception as e:
                print(f"处理代码块时出错: {str(e)}")
                # 如果处理失败，保持原样
                formatted = f"<pre><code>{code}</code></pre>"
                placeholder = self.md.htmlStash.store(formatted)
                text = text[:m.start()] + placeholder + text[m.end():]
                
        return text.split('\n')

class CustomFencedCodeExtension(markdown.Extension):
    """自定义代码块扩展"""
    def extendMarkdown(self, md):
        md.preprocessors.register(CustomFencedCodePreprocessor(md), 'fenced_code_block', 25)

def markdown_to_html(text):
    """将 Markdown 文本转换为 HTML"""
    # 对于显示为原始Markdown的情况进行预处理
    # 修复标题格式：确保#号后有空格
    text = re.sub(r'^(#{1,6})([^#\s])', r'\1 \2', text, flags=re.MULTILINE)
    
    # 修复列表格式：确保-号后有空格
    text = re.sub(r'^(\s*)-([^\s])', r'\1- \2', text, flags=re.MULTILINE)
    
    # 修复数字列表格式：确保.号后有空格
    text = re.sub(r'^(\s*\d+)\.([^\s])', r'\1. \2', text, flags=re.MULTILINE)
    
    # 使用Python-Markdown渲染Markdown内容
    html = markdown.markdown(
        text,
        extensions=[
            'markdown.extensions.extra',  # 包括tables, abbr, attr_list, def_list, fenced_code, footnotes
            'markdown.extensions.codehilite',  # 代码高亮
            'markdown.extensions.nl2br',  # 换行符转为<br>
            'markdown.extensions.sane_lists',  # 改进的列表处理
            'markdown.extensions.toc',  # 目录生成
            'markdown.extensions.tables',  # 表格支持
        ],
        output_format='html5'
    )
    
    # 配置允许的 HTML 标签和属性
    allowed_tags = [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'div', 'em',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'li', 'ol', 'p',
        'pre', 'span', 'strong', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul',
        'dl', 'dt', 'dd'
    ]
    
    allowed_attributes = {
        'a': ['href', 'title', 'class', 'id', 'name', 'target'],
        'img': ['src', 'alt', 'title', 'class', 'id', 'width', 'height'],
        'div': ['class', 'id', 'style'],
        'span': ['class', 'id', 'style'],
        'code': ['class'],
        'pre': ['class'],
        '*': ['class', 'id']
    }

    # 使用bleach清理HTML内容
    clean_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    # 为代码块添加额外的容器，方便添加复制按钮
    clean_html = re.sub(
        r'<div class="highlight"><pre>(.+?)</pre></div>',
        r'<div class="code-block"><pre>\1</pre></div>',
        clean_html,
        flags=re.DOTALL
    )
    
    return clean_html