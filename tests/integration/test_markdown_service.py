"""
文件名：test_markdown_service.py
描述：Markdown服务集成测试
作者：denny
"""

import pytest
from app.utils.markdown import MarkdownService
from app.services.toc import TocService
from app.models import Post
from app.extensions import db

@pytest.fixture
def markdown_service():
    return MarkdownService()

@pytest.fixture
def toc_service():
    return TocService()

class TestMarkdownIntegration:
    """Markdown服务集成测试 [IT-001]"""
    
    def test_markdown_to_html_conversion(self, markdown_service):
        """测试Markdown到HTML的转换"""
        markdown_text = """# Test Title
## Subtitle
This is a **bold** text with `code` and [link](http://example.com)
```python
def test():
    pass
```
"""
        result = markdown_service.convert(markdown_text)
        html = result['html']
        
        # 验证标题转换
        assert 'Test Title' in html
        assert 'Subtitle' in html
        
        # 验证基本格式
        assert '<strong>bold</strong>' in html
        assert '<code>code</code>' in html
        assert '<a href="http://example.com"' in html
        
        # 验证目录生成
        toc = result['toc']
        assert len(toc) == 2
        assert toc[0]['text'] == 'Test Title'
        assert toc[1]['text'] == 'Subtitle'

    def test_code_highlighting(self, markdown_service):
        """测试代码高亮集成"""
        code_block = """```python
def hello():
    print("Hello, World!")
```"""
        result = markdown_service.convert(code_block)
        html = result['html']
        
        # 验证代码高亮
        assert '<div class="highlight">' in html
        assert '<span class="k">def</span>' in html
        assert '<span class="nb">print</span>' in html

    def test_security_filter(self, markdown_service):
        """测试安全过滤器"""
        dangerous_markdown = """# Title
<script>alert('xss')</script>
[link](javascript:alert('xss'))
"""
        result = markdown_service.convert(dangerous_markdown)
        html = result['html']
        
        assert '<script>' not in html
        assert 'javascript:' not in html

    def test_markdown_integration_with_post(self, markdown_service, app):
        """测试Markdown与文章系统的集成"""
        with app.app_context():
            post = Post(
                title="Test Post",
                content="# Test Content\n## Section",
                author_id=1
            )
            db.session.add(post)
            db.session.commit()

            # 验证文章内容被正确转换为HTML
            assert 'Test Content' in post.html_content
            assert 'Section' in post.html_content


class TestTocIntegration:
    """目录服务集成测试 [IT-002]"""

    def test_toc_generation(self, toc_service):
        """测试目录结构生成"""
        markdown_text = """# Main Title
## Section 1
### Subsection 1.1
## Section 2
### Subsection 2.1
### Subsection 2.2
"""
        toc = toc_service.generate(markdown_text)
        assert len(toc) == 6  # 1 main + 2 sections + 3 subsections
        assert toc[0]['level'] == 1
        assert toc[0]['text'] == 'Main Title'
        assert toc[1]['level'] == 2
        assert toc[1]['text'] == 'Section 1'

    def test_toc_navigation(self, toc_service, test_client):
        """测试目录导航功能"""
        markdown_text = """# Title 1
## Section 1.1
Some content
## Section 1.2
More content
"""
        toc = toc_service.generate(markdown_text)
        
        # 验证目录项都有正确的锚点链接
        for item in toc:
            assert 'id' in item
            assert 'link' in item
            assert item['link'].startswith('#')

    def test_toc_update_mechanism(self, toc_service, test_client):
        """测试目录更新机制"""
        # 创建初始文章
        post = Post(
            title="Test Post",
            content="# Initial Title\n## Section 1",
            author_id=1
        )
        db.session.add(post)
        db.session.commit()

        # 验证初始目录
        initial_toc = toc_service.generate(post.content)
        assert len(initial_toc) == 2
        assert initial_toc[0]['text'] == 'Initial Title'

        # 更新文章内容
        post.content = "# Updated Title\n## New Section\n### Subsection"
        db.session.commit()

        # 验证目录已更新
        updated_toc = toc_service.generate(post.content)
        assert len(updated_toc) == 3
        assert updated_toc[0]['text'] == 'Updated Title'
        assert updated_toc[1]['text'] == 'New Section' 