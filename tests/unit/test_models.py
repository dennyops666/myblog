"""
文件名：test_models.py
描述：模型单元测试
作者：denny
"""

from app.models import User, Post, Category, Tag, Comment
from app.utils.markdown import markdown_to_html

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

def test_markdown_parsing():
    """测试Markdown内容解析"""
    # 创建测试Markdown内容
    markdown_content = """
# 标题1

## 标题2

这是一段**加粗**的文字。

- 列表项1
- 列表项2

```python
def test():
    print('Hello')
```
"""
    
    # 解析Markdown内容
    result = markdown_to_html(markdown_content)
    
    # 验证HTML内容
    assert 'id="标题1"' in result['html']
    assert '标题1' in result['html']
    assert '标题2' in result['html']
    assert '<strong>加粗</strong>' in result['html']
    assert '<li>列表项1</li>' in result['html']
    assert '<code>' in result['html']
    
    # 验证目录结构
    assert len(result['toc']) == 2  # 应该有2个标题
    assert result['toc'][0]['level'] == 1  # 第一个是一级标题
    assert result['toc'][1]['level'] == 2  # 第二个是二级标题
    
    # 验证目录项的文本内容
    assert result['toc'][0]['text'] == '标题1'
    assert result['toc'][1]['text'] == '标题2'
    
    # 验证锚点链接
    assert all('id' in item for item in result['toc'])
    assert all('anchor' in item for item in result['toc'])

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
    assert 'id="新标题"' in updated_post.html_content
    assert '新标题' in updated_post.html_content
    assert '新的二级标题' in updated_post.html_content
    assert '更新后的内容' in updated_post.html_content
    
    # 验证目录已更新
    assert len(updated_post.toc) == 2
    assert updated_post.toc[0]['text'] == '新标题'
    assert updated_post.toc[1]['text'] == '新的二级标题'
    assert updated_post.toc[0]['anchor'].startswith('header-')
    assert updated_post.toc[1]['anchor'].startswith('header-')

def test_category_creation(test_category):
    """测试分类创建"""
    assert test_category.name == '测试分类'
    assert test_category.description == '这是一个测试分类'

def test_tag_creation(test_tag):
    """测试标签创建"""
    assert test_tag.name == '测试标签'

def test_comment_creation(test_comment, test_post, test_user):
    """测试评论创建"""
    assert test_comment.content == '这是一条测试评论'
    assert test_comment.post_id == test_post.id
    assert test_comment.author_id == test_user.id
    assert test_comment.author.username == 'test'  # 通过关联获取作者用户名 