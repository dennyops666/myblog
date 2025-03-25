#!/usr/bin/env python3
"""
修复所有文章状态
"""
import sqlite3
import os
import sys
from datetime import datetime

DB_PATH = "/data/myblog/instance/blog-dev.db"

if not os.path.exists(DB_PATH):
    print(f"错误: 数据库文件 {DB_PATH} 不存在!")
    sys.exit(1)

try:
    print("开始修复所有文章状态...")
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 检查文章表结构
    cursor.execute("PRAGMA table_info(posts)")
    columns = cursor.fetchall()
    print("\n文章表结构:")
    for col in columns:
        print(f"列: {col['name']}, 类型: {col['type']}")
    
    # 查看所有状态
    cursor.execute("SELECT id, title, status FROM posts ORDER BY id")
    posts = cursor.fetchall()
    
    print("\n当前文章状态列表:")
    for post in posts:
        print(f"ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}")
    
    # 归类统计
    status_counts = {}
    for post in posts:
        status = post['status']
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1
    
    print("\n状态统计:")
    for status, count in status_counts.items():
        print(f"状态: {status}, 数量: {count}")
    
    # 更新所有状态为标准大写
    cursor.execute("UPDATE posts SET status = UPPER(status)")
    conn.commit()
    print("\n已将所有状态更新为大写")
    
    # 为特定文章设置ARCHIVED状态
    cursor.execute("""
        UPDATE posts 
        SET status = 'ARCHIVED' 
        WHERE title IN ('小型博客系统开发文档', 'test01')
        OR title LIKE '归档测试%'
        OR title LIKE '最终归档测试%'
        OR title LIKE '直接归档测试%'
    """)
    updated_count = cursor.rowcount
    conn.commit()
    print(f"\n已将 {updated_count} 篇文章状态设置为 ARCHIVED")
    
    # 确保其他文章为PUBLISHED状态
    cursor.execute("UPDATE posts SET status = 'PUBLISHED' WHERE status != 'ARCHIVED'")
    published_count = cursor.rowcount
    conn.commit()
    print(f"\n已将 {published_count} 篇文章状态设置为 PUBLISHED")
    
    # 重新统计
    cursor.execute("SELECT status, COUNT(*) as count FROM posts GROUP BY status")
    new_status_counts = cursor.fetchall()
    print("\n更新后状态统计:")
    for status in new_status_counts:
        print(f"状态: {status['status']}, 数量: {status['count']}")
    
    # 确认文章状态
    cursor.execute("SELECT id, title, status FROM posts ORDER BY id")
    updated_posts = cursor.fetchall()
    print("\n更新后文章状态列表:")
    for post in updated_posts:
        print(f"ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}")
    
    # 创建确认用的归档测试文章
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    title = f"确认归档测试_{timestamp}"
    
    cursor.execute("""
        INSERT INTO posts (title, content, status, created_at, updated_at, author_id, summary)
        VALUES (?, ?, 'ARCHIVED', datetime('now'), datetime('now'), 1, '最终状态确认测试')
    """, (title, f"这是一篇用于确认归档功能的文章，创建于 {timestamp}"))
    conn.commit()
    new_post_id = cursor.lastrowid
    
    print(f"\n创建确认归档文章: ID={new_post_id}, 标题={title}")
    
    # 关闭连接
    conn.close()
    
    print("\n修复完成，请重启应用查看效果")
    print("重启命令: /data/myblog/manage.sh restart")
    print("访问链接: http://localhost:5000/blog/archive")
    
except Exception as e:
    print(f"修复过程出错: {str(e)}")
    import traceback
    traceback.print_exc() 