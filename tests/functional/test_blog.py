"""
文件名: test_blog.py
描述: 博客功能测试
作者: denny
创建日期: 2025-02-16
"""

def test_index(client, test_post):
    """测试首页"""
    response = client.get('/')
    assert response.status_code == 200
    assert 'MyBlog'.encode() in response.data
    assert test_post.title.encode() in response.data

def test_post_detail(client, test_post, test_comment):
    """测试文章详情页"""
    response = client.get(f'/post/{test_post.id}')
    assert response.status_code == 200
    assert test_post.title.encode() in response.data
    assert test_post.content.encode() in response.data
    assert test_comment.content.encode() in response.data
    
    # 验证目录导航存在
    if test_post.toc:
        assert 'class="toc-nav"'.encode() in response.data
        # 验证目录项
        for item in test_post.toc:
            assert item['text'].encode() in response.data
            assert f'href="#{item["anchor"]}"'.encode() in response.data

def test_post_with_markdown_content(client):
    """测试带有Markdown内容的文章显示"""
    from app.services import PostService
    
    # 创建测试文章
    markdown_content = """
# 测试标题

## 第一部分

这是第一部分的内容

### 子部分

这是子部分的内容

## 第二部分

这是第二部分的内容

```python
def hello():
    print("Hello, World!")
```
"""
    
    post = PostService.create_post(
        title="Markdown测试文章",
        content=markdown_content,
        category_id=1,
        author_id=1,
        status=1
    )
    
    # 访问文章详情页
    response = client.get(f'/post/{post.id}')
    assert response.status_code == 200
    
    # 验证标题和内容正确渲染
    assert '<h1'.encode() in response.data
    assert '<h2'.encode() in response.data
    assert '<h3'.encode() in response.data
    
    # 验证代码块正确渲染
    assert '<pre'.encode() in response.data
    assert '<code'.encode() in response.data
    assert 'print("Hello, World!")'.encode() in response.data
    
    # 验证目录导航
    assert 'class="toc-nav"'.encode() in response.data
    assert '测试标题'.encode() in response.data
    assert '第一部分'.encode() in response.data
    assert '子部分'.encode() in response.data
    assert '第二部分'.encode() in response.data

def test_archive(client, test_post, test_category, test_tag):
    """测试归档页面"""
    # 测试时间线归档
    response = client.get('/archive?type=time')
    assert response.status_code == 200
    assert test_post.title.encode() in response.data
    
    # 测试分类归档
    response = client.get(f'/archive?type=category&category_id={test_category.id}')
    assert response.status_code == 200
    assert test_category.name.encode() in response.data
    assert test_post.title.encode() in response.data
    
    # 测试标签归档
    response = client.get(f'/archive?type=tag&tag_id={test_tag.id}')
    assert response.status_code == 200
    assert test_tag.name.encode() in response.data

def test_about(client):
    """测试关于页面"""
    response = client.get('/about')
    assert response.status_code == 200
    assert 'About MyBlog'.encode() in response.data

def test_create_comment(client, test_post):
    """测试创建评论"""
    response = client.post(
        f'/post/{test_post.id}/comment',
        data={
            'nickname': 'Test User',
            'email': 'test@example.com',
            'content': 'This is a test comment'
        }
    )
    assert response.status_code == 302  # 重定向到文章详情页
    
    # 验证评论是否创建成功
    response = client.get(f'/post/{test_post.id}')
    assert 'This is a test comment'.encode() in response.data 