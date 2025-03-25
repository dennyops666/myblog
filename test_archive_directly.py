#!/usr/bin/env python3
"""
直接测试归档功能
"""
import sqlite3
import os
import sys
import json
from datetime import datetime
import traceback

# 配置变量
DB_PATH = "/data/myblog/instance/blog-dev.db"

# 确保数据库存在
if not os.path.exists(DB_PATH):
    print(f"错误: 数据库文件 {DB_PATH} 不存在!")
    sys.exit(1)

try:
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("===== 数据库中的文章状态 =====")
    cursor.execute("SELECT id, title, status FROM posts ORDER BY id")
    posts = cursor.fetchall()
    
    # 打印文章状态
    status_counts = {}
    for post in posts:
        status = post['status']
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1
        print(f"ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}")
    
    print(f"\n文章状态统计: {status_counts}")
    
    print("\n===== 当前SQL查询结果 =====")
    # 使用和views.py中相同的SQL查询逻辑
    cursor.execute("""
        SELECT id, title, created_at, status
        FROM posts 
        WHERE status = 'PUBLISHED' OR status = 'ARCHIVED'
        ORDER BY created_at DESC
    """)
    results = cursor.fetchall()
    
    print(f"SQL查询到 {len(results)} 篇文章:")
    for post in results:
        print(f"ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}, 创建时间: {post['created_at']}")
    
    print("\n===== 修复文章状态 =====")
    # 确保归档文章状态正确设置
    cursor.execute("""
        UPDATE posts 
        SET status = 'ARCHIVED' 
        WHERE title IN ('小型博客系统开发文档', 'test01')
    """)
    conn.commit()
    
    # 检查文章状态是否已更新
    cursor.execute("SELECT id, title, status FROM posts WHERE title IN ('小型博客系统开发文档', 'test01')")
    updated_posts = cursor.fetchall()
    for post in updated_posts:
        print(f"更新后: ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}")
    
    print("\n===== 创建测试归档文章 =====")
    # 创建一个新的归档测试文章
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    cursor.execute("""
        INSERT INTO posts (title, content, status, created_at, updated_at, author_id, summary, category_id)
        VALUES (?, ?, 'ARCHIVED', datetime('now'), datetime('now'), 1, '归档测试', 1)
    """, (f"归档测试_{timestamp}", f"这是一篇测试归档功能的文章。时间戳：{timestamp}"))
    conn.commit()
    new_post_id = cursor.lastrowid
    print(f"已创建测试文章 ID: {new_post_id}")
    
    print("\n===== 再次检查SQL查询结果 =====")
    cursor.execute("""
        SELECT id, title, created_at, status
        FROM posts 
        WHERE status = 'PUBLISHED' OR status = 'ARCHIVED'
        ORDER BY created_at DESC
    """)
    final_results = cursor.fetchall()
    
    print(f"SQL查询到 {len(final_results)} 篇文章:")
    for post in final_results:
        print(f"ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}, 创建时间: {post['created_at']}")
    
    # 关闭数据库连接
    conn.close()
    
    print("\n===== 测试完成 =====")
    print("请重启应用: /data/myblog/manage.sh restart")
    print("然后访问: http://localhost:5000/blog/archive")
    
except Exception as e:
    print(f"测试过程中出错: {str(e)}")
    traceback.print_exc() 