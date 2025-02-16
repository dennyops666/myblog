"""
文件名：test_tag.py
描述：标签模块单元测试
作者：denny
创建日期：2025-02-16
"""

import pytest
from app.models import Tag
from app.services import TagService

def test_tag_creation(app_context):
    """测试标签创建"""
    tag = TagService.create_tag(name='测试标签')
    assert tag.id is not None
    assert tag.name == '测试标签'

def test_tag_query(app_context, test_tag):
    """测试标签查询"""
    # 通过ID查询
    found = TagService.get_tag_by_id(test_tag.id)
    assert found is not None
    assert found.id == test_tag.id
    
    # 通过名称查询
    found = TagService.get_tag_by_name(test_tag.name)
    assert found is not None
    assert found.id == test_tag.id
    
    # 获取所有标签
    tags = TagService.get_all_tags()
    assert len(tags) > 0
    assert test_tag in tags

def test_tag_update(app_context, test_tag):
    """测试标签更新"""
    # 更新标签名称
    TagService.update_tag(test_tag.id, name='更新后的标签')
    
    # 验证更新结果
    updated = TagService.get_tag_by_id(test_tag.id)
    assert updated.name == '更新后的标签'

def test_tag_delete(app_context):
    """测试标签删除"""
    # 创建新标签
    tag = TagService.create_tag(name='待删除标签')
    
    # 删除标签
    result = TagService.delete_tag(tag.id)
    assert result is True
    
    # 验证删除结果
    deleted = TagService.get_tag_by_id(tag.id)
    assert deleted is None

def test_tag_with_posts(app_context, test_tag, test_post):
    """测试带有文章的标签"""
    # 为文章添加标签
    test_post.tags.append(test_tag)
    
    # 验证标签下的文章
    assert len(test_tag.posts.all()) > 0
    assert test_post in test_tag.posts

def test_duplicate_tag_name(app_context, test_tag):
    """测试重复的标签名称"""
    # 尝试创建同名标签
    with pytest.raises(Exception):
        TagService.create_tag(name=test_tag.name)

def test_invalid_tag_creation(app_context):
    """测试无效的标签创建"""
    # 测试空名称
    with pytest.raises(ValueError):
        TagService.create_tag(name='')
    
    # 测试过长的名称
    with pytest.raises(ValueError):
        TagService.create_tag(name='a' * 51)  # 超过50个字符

def test_tag_posts_pagination(app_context, test_tag):
    """测试标签文章分页"""
    # 获取标签下的分页文章
    page = 1
    per_page = 10
    pagination = TagService.get_posts_by_tag(
        test_tag.id,
        page=page,
        per_page=per_page
    )
    
    # 验证分页结果
    assert pagination.page == page
    assert pagination.per_page == per_page
    assert pagination.total >= 0

def test_tag_merge(app_context):
    """测试标签合并"""
    # 创建源标签和目标标签
    source_tag = TagService.create_tag(name='源标签')
    target_tag = TagService.create_tag(name='目标标签')
    
    # 创建一篇使用源标签的文章
    from app.services import PostService
    post = PostService.create_post(
        title='测试文章',
        content='测试内容',
        category_id=1,
        author_id=1
    )
    post.tags.append(source_tag)
    
    # 合并标签
    TagService.merge_tags(source_tag.id, target_tag.id)
    
    # 验证合并结果
    assert TagService.get_tag_by_id(source_tag.id) is None  # 源标签应被删除
    assert post in target_tag.posts  # 文章应转移到目标标签 