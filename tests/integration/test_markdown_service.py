import pytest
from app.services.markdown import MarkdownService
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
        html = markdown_service.convert(markdown_text)
        assert '<h1>Test Title</h1>' in html
        assert '<h2>Subtitle</h2>' in html
        assert '<strong>bold</strong>' in html
        assert '<code>code</code>' in html
        assert '<a href="http://example.com">link</a>' in html
        assert '<pre><code class="language-python">' in html

    def test_code_highlighting(self, markdown_service):
        """测试代码高亮集成"""
        code_block = """```python
def hello():
    print("Hello, World!")
```"""
        html = markdown_service.convert(code_block)
        assert 'class="language-python"' in html
        assert 'def hello()' in html
        assert 'print(' in html

    def test_security_filter(self, markdown_service):
        """测试安全过滤器"""
        dangerous_markdown = """# Title
<script>alert('xss')</script>
[link](javascript:alert('xss'))
"""
        html = markdown_service.convert(dangerous_markdown)
        assert '<script>' not in html
        assert 'javascript:' not in html

    def test_markdown_integration_with_post(self, markdown_service, test_client):
        """测试Markdown与文章系统的集成"""
        post = Post(
            title="Test Post",
            content="# Test Content\n## Section",
            author_id=1
        )
        db.session.add(post)
        db.session.commit()

        # 验证文章内容被正确转换为HTML
        assert '<h1>Test Content</h1>' in post.html_content
        assert '<h2>Section</h2>' in post.html_content


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
        assert len(toc) == 5  # 1 main + 2 sections + 2 subsections
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