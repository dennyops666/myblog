"""
文件名：test_models.py
描述：模型单元测试
作者：denny
创建日期：2025-02-16
"""

def test_user_password_hashing(test_user):
    """测试用户密码哈希"""
    assert test_user.password_hash is not None
    assert test_user.verify_password('password')
    assert not test_user.verify_password('wrong_password')

def test_post_creation(test_post, test_user, test_category):
    """测试文章创建"""
    assert test_post.title == '测试文章'
    assert test_post.content == '这是一篇测试文章的内容'
    assert test_post.author_id == test_user.id
    assert test_post.category_id == test_category.id
    assert test_post.status == 1
    assert test_post.html_content is not None
    assert isinstance(test_post.toc, list)

def test_post_markdown_content():
    """测试文章Markdown内容解析"""
    from app.services import PostService
    
    # 创建包含标题的测试文章
    markdown_content = """
# 一级标题

## 二级标题1

这是一些内容

### 三级标题1.1

更多内容

## 二级标题2

最后的内容
"""
    
    post = PostService.create_post(
        title="测试Markdown文章",
        content=markdown_content,
        category_id=1,
        author_id=1
    )
    
    # 验证HTML内容
    assert '<h1>' in post.html_content
    assert '<h2>' in post.html_content
    assert '<h3>' in post.html_content
    
    # 验证目录结构
    assert len(post.toc) == 4  # 应该有4个标题
    assert post.toc[0]['level'] == 1  # 第一个是一级标题
    assert post.toc[1]['level'] == 2  # 第二个是二级标题
    assert post.toc[2]['level'] == 3  # 第三个是三级标题
    assert post.toc[3]['level'] == 2  # 第四个是二级标题
    
    # 验证目录项的文本内容
    assert post.toc[0]['text'] == '一级标题'
    assert post.toc[1]['text'] == '二级标题1'
    assert post.toc[2]['text'] == '三级标题1.1'
    assert post.toc[3]['text'] == '二级标题2'
    
    # 验证锚点链接
    assert all('anchor' in item for item in post.toc)
    assert all(item['anchor'].startswith('header-') for item in post.toc)

def test_post_update_content(test_post):
    """测试更新文章内容"""
    from app.services import PostService
    
    new_content = """
# 新标题

## 新的二级标题

更新后的内容
"""
    
    updated_post = PostService.update_post(
        test_post,
        content=new_content
    )
    
    # 验证内容已更新
    assert updated_post.content == new_content
    assert '<h1>' in updated_post.html_content
    assert '<h2>' in updated_post.html_content
    
    # 验证目录已更新
    assert len(updated_post.toc) == 2
    assert updated_post.toc[0]['text'] == '新标题'
    assert updated_post.toc[1]['text'] == '新的二级标题'

def test_category_creation(test_category):
    """测试分类创建"""
    assert test_category.name == '测试分类'
    assert test_category.description == '这是一个测试分类'

def test_tag_creation(test_tag):
    """测试标签创建"""
    assert test_tag.name == '测试标签'

def test_comment_creation(test_comment, test_post):
    """测试评论创建"""
    assert test_comment.content == '这是一条测试评论'
    assert test_comment.post_id == test_post.id
    assert test_comment.author_name == '测试用户'
    assert test_comment.author_email == 'test@example.com'
    assert test_comment.status == 1 