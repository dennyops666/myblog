#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
列出所有文章的基本信息
"""

import sqlite3

# 连接数据库
db_path = "/data/myblog/instance/blog-dev.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 查询所有文章
cursor.execute("SELECT id, title, status, author_id, category_id FROM posts ORDER BY id")
posts = cursor.fetchall()

# 打印文章信息
if posts:
    print(f"找到 {len(posts)} 篇文章:")
    for post in posts:
        print(f"ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}")
else:
    print("数据库中没有文章")

conn.close() 