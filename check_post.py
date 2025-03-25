#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查特定文章ID的详细信息
"""

import sys
import sqlite3
import json
from datetime import datetime
from pprint import pprint
from app import create_app
from app.models.post import Post

# 连接数据库
db_path = "/data/myblog/instance/blog-dev.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 查询指定文章
post_id = 4  # 要查询的文章ID
cursor.execute("""
    SELECT id, title, content, html_content, toc, highlight_css, summary, 
           category_id, author_id, status, is_sticky, view_count, comments_count,
           created_at, updated_at, is_private
    FROM posts 
    WHERE id = ?
""", (post_id,))

post = cursor.fetchone()

if post:
    # 打印基本信息
    print(f"文章ID: {post['id']}")
    print(f"标题: {post['title']}")
    print(f"状态: {post['status']}")
    print(f"创建时间: {post['created_at']}")
    print(f"更新时间: {post['updated_at']}")
    print(f"是否置顶: {post['is_sticky']}")
    print(f"是否私有: {post['is_private']}")
    print(f"浏览量: {post['view_count']}")
    print(f"评论数: {post['comments_count']}")
    
    # 输出内容信息
    content_length = len(post['content']) if post['content'] else 0
    html_length = len(post['html_content']) if post['html_content'] else 0
    print(f"原始内容长度: {content_length}")
    print(f"HTML内容长度: {html_length}")
    
    # 解析TOC
    if post['toc']:
        try:
            toc = json.loads(post['toc'])
            print(f"目录项数量: {len(toc)}")
        except json.JSONDecodeError:
            print("目录解析失败，格式不是有效的JSON")
            print(f"目录原始内容: {post['toc'][:100]}...")
    else:
        print("文章没有目录")
    
    # 检查分类
    if post['category_id']:
        cursor.execute("SELECT id, name FROM categories WHERE id = ?", (post['category_id'],))
        category = cursor.fetchone()
        if category:
            print(f"分类: ID={category['id']}, 名称={category['name']}")
        else:
            print(f"分类ID {post['category_id']} 不存在")
    else:
        print("文章没有分类")
    
    # 检查作者
    if post['author_id']:
        cursor.execute("SELECT id, username FROM users WHERE id = ?", (post['author_id'],))
        author = cursor.fetchone()
        if author:
            print(f"作者: ID={author['id']}, 用户名={author['username']}")
        else:
            print(f"作者ID {post['author_id']} 不存在")
    else:
        print("文章没有作者")
    
    # 检查评论
    cursor.execute("SELECT COUNT(*) as count FROM comments WHERE post_id = ?", (post_id,))
    comment_count = cursor.fetchone()['count']
    print(f"评论数量: {comment_count}")
    
    # 检查html_content开头，可能有助于诊断模板渲染问题
    if post['html_content']:
        print("\nHTML内容前100个字符:")
        print(post['html_content'][:100])
    
    # 检查内容中可能导致错误的构造
    content_problems = []
    if post['content'] and "{{" in post['content']:
        content_problems.append("内容包含Jinja2模板语法 '{{' 可能导致渲染问题")
    if post['content'] and "{%" in post['content']:
        content_problems.append("内容包含Jinja2模板语法 '{%' 可能导致渲染问题")
    
    if content_problems:
        print("\n可能的内容问题:")
        for problem in content_problems:
            print(f"- {problem}")
else:
    print(f"没有找到ID为 {post_id} 的文章")

conn.close()
print("\n检查完成")

def check_post(post_id):
    app = create_app()
    with app.app_context():
        post = Post.query.get(post_id)
        if post:
            print(f"文章ID {post_id} 存在")
            print(f"标题: {post.title}")
            print(f"状态: {post.status}")
            print(f"HTML内容长度: {len(post.html_content) if post.html_content else 0}")
            print(f"更新时间: {post.updated_at}")
        else:
            print(f"文章ID {post_id} 不存在")

if __name__ == "__main__":
    check_post(6) 