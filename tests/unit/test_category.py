"""
文件名：test_category.py
描述：分类模块单元测试
作者：denny
创建日期：2025-02-16
"""

import pytest
from app.models import Category
from app.services import CategoryService

def test_category_creation(app_context):
    """测试分类创建"""
    category = CategoryService.create_category(
        name='测试分类',
        description='这是一个测试分类'
    )
    assert category.id is not None
    assert category.name == '测试分类'
    assert category.description == '这是一个测试分类'

def test_category_query(app_context, test_category):
    """测试分类查询"""
    # 通过ID查询
    found = CategoryService.get_category_by_id(test_category.id)
    assert found is not None
    assert found.id == test_category.id
    
    # 获取所有分类
    categories = CategoryService.get_all_categories()
    assert len(categories) > 0
    assert test_category in categories

def test_category_update(app_context, test_category):
    """测试分类更新"""
    # 更新分类信息
    CategoryService.update_category(
        test_category,
        name='更新后的分类',
        description='更新后的描述'
    )
    
    # 验证更新结果
    updated = CategoryService.get_category_by_id(test_category.id)
    assert updated.name == '更新后的分类'
    assert updated.description == '更新后的描述'

def test_category_delete(app_context):
    """测试分类删除"""
    # 创建新分类
    category = CategoryService.create_category(
        name='待删除分类',
        description='这个分类将被删除'
    )
    
    # 删除分类
    CategoryService.delete_category(category)
    
    # 验证删除结果
    deleted = CategoryService.get_category_by_id(category.id)
    assert deleted is None

def test_category_with_posts(app_context, test_category, test_post):
    """测试带有文章的分类"""
    # 验证分类下的文章
    assert len(test_category.posts) > 0
    assert test_post in test_category.posts
    
    # 尝试删除带有文章的分类
    with pytest.raises(Exception):
        CategoryService.delete_category(test_category)

def test_duplicate_category_name(app_context, test_category):
    """测试重复的分类名称"""
    # 尝试创建同名分类
    with pytest.raises(Exception):
        CategoryService.create_category(
            name=test_category.name,
            description='这是一个重复的分类名称'
        )

def test_invalid_category_creation(app_context):
    """测试无效的分类创建"""
    # 测试空名称
    with pytest.raises(ValueError):
        CategoryService.create_category(
            name='',
            description='这是一个无效的分类'
        )
    
    # 测试过长的名称
    with pytest.raises(ValueError):
        CategoryService.create_category(
            name='a' * 51,  # 超过50个字符
            description='这是一个名称过长的分类'
        )

def test_category_posts_pagination(app_context, test_category):
    """测试分类文章分页"""
    # 获取分类下的分页文章
    page = 1
    per_page = 10
    pagination = CategoryService.get_posts_by_category(
        test_category.id,
        page=page,
        per_page=per_page
    )
    
    # 验证分页结果
    assert pagination.page == page
    assert pagination.per_page == per_page
    assert pagination.total >= 0 