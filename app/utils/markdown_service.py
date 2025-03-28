"""
文件名：markdown_service.py
描述：Markdown 服务
作者：denny
"""

import markdown
from markdown.extensions.toc import TocExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.attr_list import AttrListExtension
from markdown.extensions.def_list import DefListExtension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.meta import MetaExtension
from markdown.extensions.sane_lists import SaneListExtension
from markdown.extensions.smarty import SmartyExtension
from markdown.extensions.wikilinks import WikiLinkExtension
from pygments.formatters import HtmlFormatter

class MarkdownService:
    """Markdown 服务类"""
    
    def __init__(self):
        self.extensions = [
            'markdown.extensions.extra',
            TocExtension(permalink=True),
            FencedCodeExtension(),
            TableExtension(),
            CodeHiliteExtension(
                css_class='highlight',
                use_pygments=True,
                noclasses=False,
                pygments_style='monokai'
            ),
            AttrListExtension(),
            DefListExtension(),
            FootnoteExtension(),
            MetaExtension(),
            SaneListExtension(),
            SmartyExtension(),
            WikiLinkExtension()
        ]
        
        self.extension_configs = {
            'markdown.extensions.codehilite': {
                'css_class': 'highlight',
                'use_pygments': True,
                'noclasses': False,
                'pygments_style': 'monokai'
            }
        }
    
    def convert(self, text):
        """将 Markdown 文本转换为 HTML
        
        Args:
            text: Markdown 文本
            
        Returns:
            dict: 包含 HTML 内容和目录的字典
        """
        md = markdown.Markdown(
            extensions=self.extensions,
            extension_configs=self.extension_configs
        )
        
        html = md.convert(text)
        toc = self._parse_toc(md.toc_tokens) if hasattr(md, 'toc_tokens') else []
        
        # 生成代码高亮样式
        formatter = HtmlFormatter(style='monokai')
        highlight_css = formatter.get_style_defs('.highlight')
        
        return {
            'html': html,
            'toc': toc,
            'highlight_css': highlight_css
        }
    
    def _parse_toc(self, toc_tokens):
        """解析目录标记
        
        Args:
            toc_tokens: 目录标记列表
            
        Returns:
            list: 目录项列表
        """
        if not toc_tokens:
            return []
            
        result = []
        for token in toc_tokens:
            item = {
                'level': token['level'],
                'text': token['name'],
                'anchor': token['id']
            }
            if token.get('children', []):
                item['children'] = self._parse_toc(token['children'])
            result.append(item)
        
        return result 