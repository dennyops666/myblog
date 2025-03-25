#!/usr/bin/env python3
"""
简单生成文章归档HTML
"""
import sqlite3
import os

# 数据库文件路径
DB_PATH = "/data/myblog/instance/blog-dev.db"
OUTPUT_PATH = "/data/myblog/app/static/archive_list.html"

# 连接数据库
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 查询所有文章
cursor.execute("SELECT id, title, status FROM posts ORDER BY id")
posts = cursor.fetchall()

# 统计状态数量
cursor.execute("SELECT status, COUNT(*) as count FROM posts GROUP BY status")
status_counts = cursor.fetchall()

# 生成简单HTML
html = """
<!DOCTYPE html>
<html>
<head>
    <title>文章列表</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        .archived { background-color: #eee; }
    </style>
</head>
<body>
    <h1>文章列表</h1>
    <h2>状态统计</h2>
    <ul>
"""

# 添加状态统计
for status in status_counts:
    html += f"<li>{status['status']}: {status['count']}篇</li>"

html += """
    </ul>
    <h2>所有文章</h2>
    <table border="1" cellpadding="5">
        <tr>
            <th>ID</th>
            <th>标题</th>
            <th>状态</th>
        </tr>
"""

# 添加文章列表
for post in posts:
    css_class = ' class="archived"' if post['status'] == 'ARCHIVED' else ''
    html += f"""
        <tr{css_class}>
            <td>{post['id']}</td>
            <td>{post['title']}</td>
            <td>{post['status']}</td>
        </tr>
    """

html += """
    </table>
</body>
</html>
"""

# 确保输出目录存在
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# 写入HTML文件
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

# 关闭数据库连接
conn.close()

print(f"归档列表已生成: {OUTPUT_PATH}")
print(f"访问地址: http://localhost:5000/static/archive_list.html") 