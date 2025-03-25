#!/usr/bin/env python3
"""
向应用添加直接归档视图的辅助脚本
"""

# 要添加的函数代码
FUNCTION_CODE = """
@blog_bp.route('/direct_archive')
def direct_archive():
    \"""直接从数据库读取并显示归档页面\"""
    try:
        import sqlite3
        from datetime import datetime
        from flask import current_app
        
        # 连接数据库
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询所有已发布和已归档的文章
        cursor.execute(\"""
            SELECT id, title, created_at, status 
            FROM posts 
            WHERE status IN ('PUBLISHED', 'ARCHIVED', 'published', 'archived')
            ORDER BY created_at DESC
        \""")
        all_posts = cursor.fetchall()
        
        # 为调试输出文章数量和状态
        print(f"获取到 {len(all_posts)} 篇文章")
        for post in all_posts:
            print(f"文章ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}")
        
        # 按年月分组
        archive_dict = {}
        for post in all_posts:
            created_at = post['created_at']
            if isinstance(created_at, str):
                # 转换字符串日期为datetime对象
                try:
                    dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        dt = datetime.strptime(created_at, '%Y-%m-%d')
                    except ValueError:
                        # 如果无法解析，使用当前日期
                        dt = datetime.now()
            else:
                # 如果是数字(时间戳)，转换为datetime
                try:
                    dt = datetime.fromtimestamp(created_at)
                except (TypeError, ValueError):
                    dt = datetime.now()
            
            year = dt.year
            month = dt.month
            
            if year not in archive_dict:
                archive_dict[year] = {}
            
            if month not in archive_dict[year]:
                archive_dict[year][month] = []
            
            archive_dict[year][month].append({
                'id': post['id'],
                'title': post['title'],
                'status': post['status']
            })
        
        # 关闭连接
        conn.close()
        
        # 返回HTML
        result = '<h1>文章归档</h1>'
        
        # 添加调试信息
        result += f'<p>共找到 {len(all_posts)} 篇文章</p>'
        
        # 按年月排序
        for year in sorted(archive_dict.keys(), reverse=True):
            result += f'<h2>{year}年</h2>'
            for month in sorted(archive_dict[year].keys(), reverse=True):
                result += f'<h3>{month}月</h3><ul>'
                for post in archive_dict[year][month]:
                    status_mark = ' [归档]' if post['status'].upper() == 'ARCHIVED' else ''
                    result += f'<li><a href="/blog/post/{post["id"]}">{post["title"]}</a>{status_mark}</li>'
                result += '</ul>'
        
        return result
    except Exception as e:
        import traceback
        error_message = f"归档页面加载失败: {str(e)}\\n{traceback.format_exc()}"
        current_app.logger.error(error_message)
        return f'<h1>归档页面加载失败</h1><pre>{error_message}</pre>'
"""

# 添加函数到views.py文件
import os

views_file = "/data/myblog/app/controllers/blog/views.py"

# 读取原文件内容
with open(views_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 检查函数是否已经存在
if "def direct_archive" in content:
    print("函数已存在，无需添加")
else:
    # 添加函数到文件末尾
    with open(views_file, 'a', encoding='utf-8') as f:
        f.write("\n" + FUNCTION_CODE)
    print(f"已将direct_archive函数添加到 {views_file}")

print("操作完成")
print("请重启应用后访问: http://localhost:5000/blog/direct_archive") 