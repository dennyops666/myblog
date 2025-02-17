"""
文件名：test_post.py
描述：文章模型测试用例
作者：denny
创建日期：2025-02-16
"""

import pytest
from app.models import Post, db
from app.services import PostService
from app.utils.markdown import markdown_to_html

def test_post_creation(app_context, test_post, test_user, test_category):
    """测试文章创建"""
    assert test_post.title == '测试文章'
    assert test_post.content == '这是一篇测试文章的内容'
    assert test_post.author_id == test_user.id
    assert test_post.category_id == test_category.id
    assert test_post.status == 1

def test_post_markdown_parsing(app_context, test_user, test_category):
    """测试Markdown解析"""
    markdown_content = """
# 标题1

## 标题2

这是一段**加粗**的文字。

- 列表项1
- 列表项2

```python
def hello():
    print('Hello World')
```
"""
    
    post = PostService.create_post(
        title='Markdown测试',
        content=markdown_content,
        category_id=test_category.id,
        author_id=test_user.id,
        status=1
    )
    
    # 验证HTML内容
    assert 'id="标题1"' in post.html_content
    assert '标题1' in post.html_content
    assert '<strong>加粗</strong>' in post.html_content
    assert '<li>列表项1</li>' in post.html_content
    assert '<code>' in post.html_content
    
    # 验证目录结构
    assert len(post.toc) == 2
    assert post.toc[0]['text'] == '标题1'
    assert post.toc[1]['text'] == '标题2'

def test_post_update(app_context, test_post):
    """测试文章更新"""
    new_title = '更新后的标题'
    new_content = '更新后的内容'
    
    PostService.update_post(
        test_post,
        title=new_title,
        content=new_content
    )
    
    assert test_post.title == new_title
    assert test_post.content == new_content
    assert test_post.html_content is not None

def test_post_delete(app_context, test_post):
    """测试文章删除"""
    post_id = test_post.id
    PostService.delete_post(test_post)
    
    # 验证文章已被删除
    deleted_post = PostService.get_post_by_id(post_id)
    assert deleted_post is None

def test_post_query_methods(app_context, test_user, test_category):
    """测试文章查询方法"""
    # 创建测试数据
    posts = []
    for i in range(5):
        post = PostService.create_post(
            title=f'测试文章{i}',
            content=f'内容{i}',
            category_id=test_category.id,
            author_id=test_user.id,
            status=1
        )
        posts.append(post)
    
    # 测试分页查询
    page = PostService.get_posts_by_page(page=1, per_page=3)
    assert len(page.items) == 3
    
    # 测试分类查询
    category_posts = PostService.get_posts_by_category(test_category.id)
    assert len(category_posts.items) > 0
    
    # 测试最近文章查询
    recent_posts = PostService.get_recent_posts(limit=2)
    assert len(recent_posts) == 2

def test_invalid_post_creation(app_context, test_user, test_category):
    """测试无效的文章创建"""
    # 测试标题为空
    with pytest.raises(ValueError):
        PostService.create_post(
            title='',
            content='内容',
            category_id=test_category.id,
            author_id=test_user.id
        )
    
    # 测试内容为空
    with pytest.raises(ValueError):
        PostService.create_post(
            title='标题',
            content='',
            category_id=test_category.id,
            author_id=test_user.id
        )
    
    # 测试无效的分类ID
    with pytest.raises(ValueError):
        PostService.create_post(
            title='标题',
            content='内容',
            category_id=999,  # 不存在的分类ID
            author_id=test_user.id
        )