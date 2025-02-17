"""
文件名：toc.py
描述：目录服务
作者：denny
创建日期：2024-03-21
"""

import re
from bs4 import BeautifulSoup

class TocService:
    def __init__(self):
        pass

    def generate(self, content):
        """从Markdown内容生成目录"""
        if not content:
            return []
            
        # 使用正则表达式匹配标题
        headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        
        toc = []
        for header in headers:
            level = len(header[0])  # '#' 的数量表示级别
            text = header[1].strip()
            
            # 生成ID
            header_id = self._generate_id(text)
            
            # 只添加前三级标题
            if level <= 3:
                toc.append({
                    'level': level,
                    'text': text,
                    'id': header_id,
                    'link': f'#{header_id}'
                })
            
        return toc

    def _generate_id(self, text):
        """生成标题ID"""
        # 移除HTML标签
        text = BeautifulSoup(text, 'html.parser').get_text()
        
        # 转换为小写
        text = text.lower()
        
        # 替换空格为连字符
        text = re.sub(r'\s+', '-', text)
        
        # 移除非字母数字字符
        text = re.sub(r'[^\w\-]', '', text)
        
        # 确保ID唯一性
        return f'header-{text}'

    def update_headers(self, html_content):
        """更新HTML中的标题ID"""
        if not html_content:
            return html_content
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 处理所有标题标签
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            # 生成ID
            header_id = self._generate_id(tag.get_text())
            
            # 设置ID属性
            tag['id'] = header_id
            
        return str(soup) 