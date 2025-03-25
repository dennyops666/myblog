#!/usr/bin/env python3
"""
独立脚本：查看文章内容
用途：直接从数据库读取文章内容，避开Flask应用中可能存在的问题
"""

import sqlite3
import sys
import os
import json
from datetime import datetime

def get_post_by_id(post_id):
    """从数据库获取指定ID的文章"""
    db_path = '/data/myblog/instance/blog-dev.db'
    
    if not os.path.exists(db_path):
        print(f"错误：数据库文件不存在: {db_path}")
        return None
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        cursor = conn.cursor()
        
        # 查询文章基本信息
        cursor.execute("""
            SELECT p.*, c.name as category_name
            FROM posts p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
        """, (post_id,))
        
        post = cursor.fetchone()
        
        if not post:
            print(f"错误：文章ID {post_id} 不存在")
            return None
        
        # 查询文章标签
        cursor.execute("""
            SELECT t.name
            FROM tags t
            JOIN post_tags pt ON t.id = pt.tag_id
            WHERE pt.post_id = ?
        """, (post_id,))
        
        tags = [row['name'] for row in cursor.fetchall()]
        
        # 查询文章评论
        cursor.execute("""
            SELECT c.*
            FROM comments c
            WHERE c.post_id = ? AND c.status = 'APPROVED'
            ORDER BY c.created_at DESC
        """, (post_id,))
        
        comments = [dict(row) for row in cursor.fetchall()]
        
        # 构建文章对象
        post_data = dict(post)
        post_data['tags'] = tags
        post_data['comments'] = comments
        post_data['category_name'] = post['category_name']
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        return post_data
        
    except sqlite3.Error as e:
        print(f"数据库错误：{str(e)}")
        return None
    except Exception as e:
        print(f"未知错误：{str(e)}")
        return None

def format_post(post):
    """格式化文章内容"""
    if not post:
        return "无法获取文章内容"
    
    # 文章基本信息
    lines = [
        f"文章ID: {post['id']}",
        f"标题: {post['title']}",
        f"状态: {post['status']}",
        f"创建时间: {post.get('created_at', 'unknown')}",
        f"更新时间: {post.get('updated_at', 'unknown')}",
        f"分类: {post.get('category_name', 'unknown')}",
        f"浏览次数: {post.get('view_count', 0)}",
        f"标签: {', '.join(post['tags']) if post['tags'] else '无'}"
    ]
    
    # 文章正文
    lines.append("\n--- 正文开始 ---")
    lines.append(post.get('content', '') or '')
    lines.append("--- 正文结束 ---")
    
    # 文章评论
    lines.append(f"\n评论 ({len(post['comments'])})")
    if post['comments']:
        for i, comment in enumerate(post['comments'], 1):
            lines.append(f"\n评论 {i}:")
            lines.append(f"  昵称: {comment.get('nickname', '匿名')}")
            lines.append(f"  内容: {comment.get('content', '')}")
            lines.append(f"  时间: {comment.get('created_at', 'unknown')}")
    else:
        lines.append("暂无评论")
    
    return "\n".join(lines)

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python view_post.py <post_id>")
        return
    
    try:
        post_id = int(sys.argv[1])
    except ValueError:
        print("错误：文章ID必须是一个整数")
        return
    
    post = get_post_by_id(post_id)
    if post:
        print(format_post(post))
    
if __name__ == "__main__":
    main() 