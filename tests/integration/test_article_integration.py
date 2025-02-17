"""
文件名：test_article_integration.py
描述：文章创建集成测试
作者：denny
创建日期：2024-03-21
"""

import pytest
from app.models import Post, Category, Tag
from app.services.post import PostService
from app.utils.markdown import MarkdownService
from app.services.toc import TocService
from app.extensions import db, cache

@pytest.fixture
def post_service():
    return PostService()

class TestArticleCreationIntegration:
    """文章创建流程集成测试 [IT-003]"""

    def test_article_creation_with_markdown(self, post_service, app):
        """测试文章创建与Markdown解析"""
        with app.app_context():
            post = post_service.create(
                title="Test Article",
                content="# Test Content\n## Section 1\nThis is a test.",
                author_id=1
            )
            
            assert post.title == "Test Article"
            assert "Test Content" in post.html_content
            assert "Section 1" in post.html_content

    def test_category_tag_association(self, post_service, app):
        """测试分类标签关联"""
        with app.app_context():
            # 创建分类和标签
            category = Category(name="Test Category")
            tag1 = Tag(name="Test Tag 1")
            tag2 = Tag(name="Test Tag 2")
            
            db.session.add_all([category, tag1, tag2])
            db.session.commit()
            
            # 创建文章并关联分类和标签
            post = post_service.create(
                title="Test Article",
                content="Test content",
                author_id=1,
                category_id=category.id,
                tag_ids=[tag1.id, tag2.id]
            )
            
            assert post.category.name == "Test Category"
            assert len(post.tags) == 2
            assert "Test Tag 1" in [tag.name for tag in post.tags]
            assert "Test Tag 2" in [tag.name for tag in post.tags]

    def test_toc_auto_generation(self, post_service, app):
        """测试目录自动生成"""
        with app.app_context():
            post = post_service.create(
                title="Test Article",
                content="""# Main Title
## Section 1
### Subsection 1.1
## Section 2
### Subsection 2.1""",
                author_id=1
            )
            
            assert post.toc
            assert len(post.toc) == 5  # 1 main + 2 sections + 2 subsections
            assert post.toc[0]['text'] == "Main Title"
            assert post.toc[1]['text'] == "Section 1"

    def test_index_update(self, post_service, app):
        """测试索引更新"""
        with app.app_context():
            # 创建文章
            post = post_service.create(
                title="Test Article",
                content="Test content for search",
                author_id=1
            )
            
            # 更新文章
            post_service.update(
                post.id,
                title="Updated Title",
                content="Updated content for search"
            )
            
            # 清除缓存
            cache.clear()
            
            # 验证搜索结果
            results = post_service.search("Updated content")
            assert len(results) > 0
            assert results[0].id == post.id


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