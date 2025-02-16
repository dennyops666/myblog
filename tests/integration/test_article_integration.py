import pytest
from app.models import Post, Category, Tag
from app.services.post import PostService
from app.services.markdown import MarkdownService
from app.services.toc import TocService
from app.extensions import db, cache

@pytest.fixture
def post_service():
    return PostService()

class TestArticleCreationIntegration:
    """文章创建流程集成测试 [IT-003]"""

    def test_article_creation_with_markdown(self, post_service, test_client):
        """测试文章创建与Markdown解析集成"""
        content = """# Test Article
## Section 1
This is a test article with **markdown** content.
"""
        post = post_service.create(
            title="Test Article",
            content=content,
            author_id=1
        )
        
        # 验证Markdown解析
        assert '<h1>Test Article</h1>' in post.html_content
        assert '<strong>markdown</strong>' in post.html_content

    def test_category_tag_association(self, post_service, test_client):
        """测试分类标签关联"""
        # 创建测试分类和标签
        category = Category(name="Test Category")
        tag1 = Tag(name="Test Tag 1")
        tag2 = Tag(name="Test Tag 2")
        db.session.add_all([category, tag1, tag2])
        db.session.commit()

        # 创建带分类和标签的文章
        post = post_service.create(
            title="Test Article",
            content="Test content",
            author_id=1,
            category_id=category.id,
            tags=[tag1.id, tag2.id]
        )

        # 验证关联
        assert post.category.name == "Test Category"
        assert len(post.tags) == 2
        assert "Test Tag 1" in [tag.name for tag in post.tags]

    def test_toc_auto_generation(self, post_service, test_client):
        """测试目录自动生成"""
        content = """# Main Title
## Section 1
### Subsection 1.1
## Section 2
### Subsection 2.1
"""
        post = post_service.create(
            title="Test Article",
            content=content,
            author_id=1
        )

        # 验证目录生成
        toc = post.get_toc()
        assert len(toc) == 5
        assert toc[0]['text'] == 'Main Title'
        assert toc[1]['text'] == 'Section 1'

    def test_index_update(self, post_service, test_client):
        """测试索引更新"""
        post = post_service.create(
            title="Test Article",
            content="Test content for search",
            author_id=1
        )

        # 验证文章可以被搜索
        search_results = post_service.search("Test content")
        assert post.id in [p.id for p in search_results]


class TestArticleUpdateIntegration:
    """文章更新流程集成测试 [IT-004]"""

    def test_content_update_and_html_regeneration(self, post_service, test_client):
        """测试内容更新与HTML重生成"""
        # 创建初始文章
        post = post_service.create(
            title="Initial Title",
            content="# Initial Content",
            author_id=1
        )
        initial_html = post.html_content

        # 更新文章内容
        updated_content = """# Updated Content
## New Section
This is updated content with **new** formatting.
"""
        post_service.update(
            post_id=post.id,
            title="Updated Title",
            content=updated_content
        )

        # 验证HTML已重新生成
        assert post.html_content != initial_html
        assert '<h1>Updated Content</h1>' in post.html_content
        assert '<strong>new</strong>' in post.html_content

    def test_toc_sync_update(self, post_service, test_client):
        """测试目录同步更新"""
        # 创建初始文章
        post = post_service.create(
            title="Test Article",
            content="# Initial Title\n## Section 1",
            author_id=1
        )
        initial_toc = post.get_toc()

        # 更新文章内容
        post_service.update(
            post_id=post.id,
            content="# New Title\n## New Section\n### Subsection"
        )

        # 验证目录已更新
        updated_toc = post.get_toc()
        assert len(updated_toc) > len(initial_toc)
        assert updated_toc[0]['text'] == 'New Title'

    def test_related_data_update(self, post_service, test_client):
        """测试关联数据更新"""
        # 创建初始分类和标签
        category1 = Category(name="Category 1")
        category2 = Category(name="Category 2")
        tag1 = Tag(name="Tag 1")
        tag2 = Tag(name="Tag 2")
        db.session.add_all([category1, category2, tag1, tag2])
        db.session.commit()

        # 创建初始文章
        post = post_service.create(
            title="Test Article",
            content="Test content",
            author_id=1,
            category_id=category1.id,
            tags=[tag1.id]
        )

        # 更新文章关联
        post_service.update(
            post_id=post.id,
            category_id=category2.id,
            tags=[tag2.id]
        )

        # 验证关联更新
        assert post.category.id == category2.id
        assert len(post.tags) == 1
        assert post.tags[0].id == tag2.id

    def test_cache_update(self, post_service, test_client):
        """测试缓存更新"""
        # 创建文章并缓存
        post = post_service.create(
            title="Test Article",
            content="Test content",
            author_id=1
        )
        cache.set(f'post_{post.id}', post)

        # 更新文章
        post_service.update(
            post_id=post.id,
            title="Updated Title",
            content="Updated content"
        )

        # 验证缓存已更新
        cached_post = cache.get(f'post_{post.id}')
        assert cached_post.title == "Updated Title"
        assert cached_post.content == "Updated content" 