#!/usr/bin/env python3
"""
命令行归档工具
"""
import sqlite3
import sys
from datetime import datetime

# 数据库文件路径
DB_PATH = "/data/myblog/instance/blog-dev.db"

def get_posts():
    """获取所有文章"""
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询所有文章
        cursor.execute("""
            SELECT id, title, created_at, status 
            FROM posts 
            WHERE status IN ('PUBLISHED', 'ARCHIVED', 'published', 'archived')
            ORDER BY created_at DESC
        """)
        posts = cursor.fetchall()
        
        # 获取数据库中所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table['name'] for table in cursor.fetchall()]
        
        # 获取post表结构
        cursor.execute("PRAGMA table_info(posts)")
        columns = cursor.fetchall()
        
        # 关闭连接
        conn.close()
        
        print(f"数据库中的表: {', '.join(tables)}")
        print(f"posts表结构: {', '.join([col['name'] for col in columns])}")
        print(f"获取到 {len(posts)} 篇文章")
        
        # 输出文章信息
        for post in posts:
            print(f"文章ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}")
            
            # 尝试解析created_at
            created_at = post['created_at']
            if isinstance(created_at, str):
                print(f"  创建时间(字符串): {created_at}")
            else:
                print(f"  创建时间(非字符串): {created_at}, 类型: {type(created_at)}")
                try:
                    dt = datetime.fromtimestamp(created_at)
                    print(f"  转换后的时间: {dt}")
                except Exception as e:
                    print(f"  时间转换失败: {e}")
        
        return posts
    except Exception as e:
        print(f"获取文章失败: {e}")
        return []

if __name__ == "__main__":
    print("开始查询归档文章...")
    get_posts()
    print("查询完成!") 