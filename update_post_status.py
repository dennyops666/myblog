#!/usr/bin/env python3
"""
直接修改数据库中文章的状态，确保特定文章为归档状态
"""
import sqlite3
import os
import sys
from datetime import datetime

# 数据库文件路径
DB_PATH = "/data/myblog/instance/blog-dev.db"

# 检查数据库文件是否存在
if not os.path.exists(DB_PATH):
    print(f"错误: 数据库文件 {DB_PATH} 不存在!")
    sys.exit(1)

try:
    print("\n===== 开始更新文章状态 =====")
    
    # 连接SQLite数据库
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 首先查看所有文章的状态
    print("\n当前所有文章的状态:")
    cursor.execute("SELECT id, title, status FROM posts ORDER BY id")
    posts = cursor.fetchall()
    for post in posts:
        print(f"ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}")
    
    # 统计各个状态的文章数量
    cursor.execute("SELECT status, COUNT(*) as count FROM posts GROUP BY status")
    status_counts = cursor.fetchall()
    print("\n文章状态统计:")
    for status in status_counts:
        print(f"状态: {status['status']}, 数量: {status['count']}")
    
    # 确保所有状态值为大写
    cursor.execute("UPDATE posts SET status = upper(status)")
    conn.commit()
    print("\n已将所有状态转换为大写")
    
    # 设置特定文章为归档状态
    print("\n设置指定文章为归档状态:")
    cursor.execute("""
        UPDATE posts 
        SET status = 'ARCHIVED' 
        WHERE title IN ('小型博客系统开发文档', 'test01')
    """)
    updated_rows = cursor.rowcount
    conn.commit()
    print(f"已更新 {updated_rows} 篇文章为归档状态")
    
    # 查看更新后的文章
    print("\n更新后的指定文章状态:")
    cursor.execute("SELECT id, title, status FROM posts WHERE title IN ('小型博客系统开发文档', 'test01')")
    updated_posts = cursor.fetchall()
    for post in updated_posts:
        print(f"ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}")
    
    # 创建一个新的归档测试文章
    print("\n创建新的归档测试文章:")
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    cursor.execute("""
        INSERT INTO posts (
            title, content, status, created_at, updated_at,
            author_id, summary, category_id
        ) VALUES (
            ?, ?, 'ARCHIVED', datetime('now'), datetime('now'),
            1, '直接更新脚本测试', 1
        )
    """, (f"直接归档测试_{timestamp}", f"这是一篇通过直接数据库更新脚本创建的归档测试文章，创建于 {timestamp}"))
    new_post_id = cursor.lastrowid
    conn.commit()
    print(f"已创建新的归档文章，ID: {new_post_id}, 标题: 直接归档测试_{timestamp}")
    
    # 再次验证归档文章
    print("\n归档文章验证:")
    cursor.execute("SELECT id, title, status FROM posts WHERE status = 'ARCHIVED'")
    archive_posts = cursor.fetchall()
    for post in archive_posts:
        print(f"ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}")
    
    # 统计各状态文章数量
    cursor.execute("SELECT status, COUNT(*) as count FROM posts GROUP BY status")
    final_counts = cursor.fetchall()
    print("\n最终文章状态统计:")
    for status in final_counts:
        print(f"状态: {status['status']}, 数量: {status['count']}")
    
    # 关闭数据库连接
    conn.close()
    
    print("\n===== 文章状态更新完成 =====")
    print("请重启应用程序并访问归档页面查看效果: http://localhost:5000/blog/archive")
    
except Exception as e:
    print(f"更新过程中出错: {str(e)}")
    import traceback
    traceback.print_exc() 