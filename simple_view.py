#!/usr/bin/env python3
"""
简单查看文章脚本
"""

import sqlite3
import sys

def view_post(post_id):
    """查看文章内容"""
    try:
        # 连接数据库
        conn = sqlite3.connect('instance/blog-dev.db')
        cursor = conn.cursor()
        
        # 查询文章
        cursor.execute("""
            SELECT id, title, content, html_content, status, view_count, created_at, updated_at
            FROM posts 
            WHERE id = ?
        """, (post_id,))
        
        post = cursor.fetchone()
        
        if not post:
            print(f"错误：找不到ID为 {post_id} 的文章")
            return
        
        # 打印文章信息
        print(f"文章ID: {post[0]}")
        print(f"标题: {post[1]}")
        print(f"状态: {post[4]}")
        print(f"浏览量: {post[5]}")
        print(f"创建时间: {post[6]}")
        print(f"更新时间: {post[7]}")
        print("\n--- 正文内容 ---")
        print(post[2] or "无内容")
        print("--- 正文结束 ---")
        
        # 查询评论
        cursor.execute("""
            SELECT nickname, content, created_at
            FROM comments
            WHERE post_id = ? AND status = 'APPROVED'
            ORDER BY created_at DESC
        """, (post_id,))
        
        comments = cursor.fetchall()
        
        print(f"\n评论 ({len(comments)})")
        if comments:
            for i, comment in enumerate(comments, 1):
                print(f"\n评论 {i}:")
                print(f"  昵称: {comment[0]}")
                print(f"  内容: {comment[1]}")
                print(f"  时间: {comment[2]}")
        else:
            print("暂无评论")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python simple_view.py <post_id>")
        sys.exit(1)
    
    try:
        post_id = int(sys.argv[1])
    except ValueError:
        print("错误：文章ID必须是一个整数")
        sys.exit(1)
    
    view_post(post_id) 