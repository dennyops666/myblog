"""
文件名：test_performance.py
描述：性能测试
作者：denny
创建日期：2024-03-20
"""

import time
import pytest
from concurrent.futures import ThreadPoolExecutor

def test_page_load_time(client, test_post):
    """测试页面加载时间"""
    # 测试首页加载时间
    start_time = time.time()
    response = client.get('/')
    load_time = time.time() - start_time
    assert load_time < 2.0  # 首页加载时间应小于2秒
    
    # 测试文章页面加载时间
    start_time = time.time()
    response = client.get(f'/post/{test_post.id}')
    load_time = time.time() - start_time
    assert load_time < 3.0  # 文章页面加载时间应小于3秒

def test_markdown_parsing_time():
    """测试Markdown解析性能"""
    from app.utils.markdown import markdown_to_html
    
    # 生成一个较大的Markdown文本
    large_markdown = '\n'.join([
        f'# 标题 {i}\n\n## 子标题 {i}\n\n这是第 {i} 段内容。\n\n```python\nprint("test")\n```'
        for i in range(100)  # 生成100个段落
    ])
    
    # 测试解析时间
    start_time = time.time()
    result = markdown_to_html(large_markdown)
    parse_time = time.time() - start_time
    
    # 解析时间应小于1秒
    assert parse_time < 1.0
    # 验证解析结果包含目录数据
    assert 'html' in result
    assert 'toc' in result
    assert len(result['toc']) == 200  # 100个一级标题和100个二级标题

def test_concurrent_requests(client, test_post):
    """测试并发请求"""
    def make_request():
        return client.get('/')
    
    # 模拟50个并发请求
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        responses = [f.result() for f in futures]
        
        # 验证所有请求都成功
        assert all(r.status_code == 200 for r in responses)

def test_comment_submission_time(client, test_post):
    """测试评论提交延迟"""
    start_time = time.time()
    response = client.post(
        f'/post/{test_post.id}/comment',
        data={
            'nickname': 'Performance Test',
            'email': 'test@example.com',
            'content': 'Testing comment submission time'
        }
    )
    submission_time = time.time() - start_time
    assert submission_time < 1.0  # 评论提交延迟应小于1秒

def test_database_query_time(client, test_post):
    """测试数据库查询响应时间"""
    # 测试文章列表查询时间
    start_time = time.time()
    response = client.get('/')
    query_time = time.time() - start_time
    assert query_time < 1.0  # 查询响应时间应小于1秒
    
    # 测试文章详情查询时间
    start_time = time.time()
    response = client.get(f'/post/{test_post.id}')
    query_time = time.time() - start_time
    assert query_time < 1.0  # 查询响应时间应小于1秒 