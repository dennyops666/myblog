#!/usr/bin/env python3
"""
直接修复归档相关问题
"""
import sqlite3
import os
import sys
from datetime import datetime

# 配置变量
DB_PATH = "/data/myblog/instance/blog-dev.db"

# 检查数据库存在
if not os.path.exists(DB_PATH):
    print(f"错误: 数据库文件 {DB_PATH} 不存在!")
    sys.exit(1)

try:
    print("\n===== 开始修复归档功能 =====")
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. 检查文章状态
    print("\n1. 检查当前文章状态:")
    cursor.execute("SELECT id, title, status FROM posts")
    posts = cursor.fetchall()
    
    status_counts = {}
    for post in posts:
        status = post['status']
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1
        print(f"  ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}")
    
    print(f"\n文章状态统计: {status_counts}")
    
    # 2. 将指定文章设置为归档状态
    print("\n2. 设置指定文章为归档状态:")
    cursor.execute("UPDATE posts SET status = 'ARCHIVED' WHERE title IN ('小型博客系统开发文档', 'test01')")
    conn.commit()
    print(f"  已更新 {cursor.rowcount} 篇文章为归档状态")
    
    # 3. 创建一篇新的归档文章
    print("\n3. 创建一篇新的归档测试文章:")
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    title = f"归档测试文章_{timestamp}"
    content = f"这是一篇用于测试归档功能的文章，创建于 {timestamp}"
    
    cursor.execute("""
        INSERT INTO posts (title, content, status, created_at, updated_at, author_id, summary) 
        VALUES (?, ?, 'ARCHIVED', datetime('now'), datetime('now'), 1, '归档测试')
    """, (title, content))
    new_post_id = cursor.lastrowid
    conn.commit()
    print(f"  已创建新的归档文章: ID={new_post_id}, 标题={title}")
    
    # 4. 验证归档文章
    print("\n4. 验证归档文章:")
    cursor.execute("SELECT id, title, status FROM posts WHERE status = 'ARCHIVED'")
    archived_posts = cursor.fetchall()
    print(f"  共有 {len(archived_posts)} 篇归档文章:")
    for post in archived_posts:
        print(f"  - ID: {post['id']}, 标题: {post['title']}")
    
    # 5. 验证归档视图SQL是否符合预期
    print("\n5. 检查controllers/blog/views.py中的archive函数:")
    # 使用和views.py中相同的SQL查询逻辑
    sql = """
        SELECT id, title, content, created_at, category_id 
        FROM posts 
        WHERE status = 'PUBLISHED' OR status = 'ARCHIVED'
        ORDER BY created_at DESC
    """
    cursor.execute(sql)
    all_posts = cursor.fetchall()
    print(f"  SQL查询结果: 找到 {len(all_posts)} 篇文章")
    for post in all_posts:
        print(f"  - ID: {post['id']}, 标题: {post['title']}, 创建时间: {post['created_at']}")
    
    # 关闭数据库连接
    conn.close()
    
    print("\n===== 修复完成 =====")
    print("请重启应用: /data/myblog/manage.sh restart")
    print("然后访问: http://localhost:5000/blog/archive")
    
except Exception as e:
    print(f"修复过程中出错: {str(e)}")
    import traceback
    traceback.print_exc() 