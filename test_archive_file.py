#!/usr/bin/env python3
"""
测试归档功能并将结果写入文件
"""
import sqlite3
import os
import sys
import json
from datetime import datetime
import traceback

# 配置变量
DB_PATH = "/data/myblog/instance/blog-dev.db"
OUTPUT_PATH = "/data/myblog/archive_test_results.txt"

# 重定向输出到文件
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    # 确保数据库存在
    if not os.path.exists(DB_PATH):
        f.write(f"错误: 数据库文件 {DB_PATH} 不存在!\n")
        sys.exit(1)

    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        f.write("===== 数据库中的文章状态 =====\n")
        cursor.execute("SELECT id, title, status FROM posts ORDER BY id")
        posts = cursor.fetchall()
        
        # 打印文章状态
        status_counts = {}
        for post in posts:
            status = post['status']
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
            f.write(f"ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}\n")
        
        f.write(f"\n文章状态统计: {status_counts}\n")
        
        f.write("\n===== 当前SQL查询结果 =====\n")
        # 使用和views.py中相同的SQL查询逻辑
        cursor.execute("""
            SELECT id, title, created_at, status
            FROM posts 
            WHERE status = 'PUBLISHED' OR status = 'ARCHIVED'
            ORDER BY created_at DESC
        """)
        results = cursor.fetchall()
        
        f.write(f"SQL查询到 {len(results)} 篇文章:\n")
        for post in results:
            f.write(f"ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}, 创建时间: {post['created_at']}\n")
        
        f.write("\n===== 修复文章状态 =====\n")
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
            f.write(f"更新后: ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}\n")
        
        f.write("\n===== 创建测试归档文章 =====\n")
        # 创建一个新的归档测试文章
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        cursor.execute("""
            INSERT INTO posts (title, content, status, created_at, updated_at, author_id, summary, category_id)
            VALUES (?, ?, 'ARCHIVED', datetime('now'), datetime('now'), 1, '归档测试', 1)
        """, (f"归档测试_{timestamp}", f"这是一篇测试归档功能的文章。时间戳：{timestamp}"))
        conn.commit()
        new_post_id = cursor.lastrowid
        f.write(f"已创建测试文章 ID: {new_post_id}\n")
        
        f.write("\n===== 再次检查SQL查询结果 =====\n")
        cursor.execute("""
            SELECT id, title, created_at, status
            FROM posts 
            WHERE status = 'PUBLISHED' OR status = 'ARCHIVED'
            ORDER BY created_at DESC
        """)
        final_results = cursor.fetchall()
        
        f.write(f"SQL查询到 {len(final_results)} 篇文章:\n")
        for post in final_results:
            f.write(f"ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}, 创建时间: {post['created_at']}\n")
        
        # 关闭数据库连接
        conn.close()
        
        f.write("\n===== 测试完成 =====\n")
        f.write("请重启应用: /data/myblog/manage.sh restart\n")
        f.write("然后访问: http://localhost:5000/blog/archive\n")
        
    except Exception as e:
        f.write(f"测试过程中出错: {str(e)}\n")
        f.write(traceback.format_exc()) 