#!/usr/bin/env python3
"""
调试博客首页视图函数
"""
import os
import sys
import sqlite3
from datetime import datetime
from pprint import pprint

# 使用SQLite直接从数据库获取数据
def get_data_from_db():
    try:
        db_path = "/data/myblog/instance/blog-dev.db"
        print(f"数据库路径: {db_path}")
        
        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            print(f"错误: 数据库文件不存在: {db_path}")
            return
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 检查表结构
        print("\n--- 表结构 ---")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"表: {table['name']}")
        
        # 检查文章表结构
        print("\n--- 文章表结构 ---")
        cursor.execute("PRAGMA table_info(posts)")
        columns = cursor.fetchall()
        for column in columns:
            print(f"列: {column['name']} ({column['type']})")
        
        # 获取所有文章
        print("\n--- 所有文章 ---")
        cursor.execute("SELECT id, title, status FROM posts ORDER BY id")
        posts = cursor.fetchall()
        print(f"共有 {len(posts)} 篇文章")
        for post in posts:
            print(f"文章ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}, 状态类型: {type(post['status'])}")
        
        # 获取已发布和已归档的文章
        print("\n--- 已发布和已归档的文章 ---")
        cursor.execute("SELECT id, title, status FROM posts WHERE status IN ('PUBLISHED', 'ARCHIVED', 'published', 'archived') ORDER BY id")
        filtered_posts = cursor.fetchall()
        print(f"共有 {len(filtered_posts)} 篇过滤后的文章")
        for post in filtered_posts:
            print(f"文章ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}")
        
        # 关闭连接
        conn.close()
    except Exception as e:
        import traceback
        print(f"错误: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    print("开始调试博客首页...")
    get_data_from_db()
    print("调试完成") 