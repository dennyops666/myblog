#!/usr/bin/env python3
"""
直接生成归档页面
"""
import sqlite3
import os
import sys
import json
from datetime import datetime
from collections import defaultdict

# 配置变量
DB_PATH = "/data/myblog/instance/blog-dev.db"
OUTPUT_PATH = "/data/myblog/static/archive.html"

# 检查数据库存在
if not os.path.exists(DB_PATH):
    print(f"错误: 数据库文件 {DB_PATH} 不存在!")
    sys.exit(1)

try:
    print("\n===== 开始生成归档页面 =====")
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 使用SQL查询所有PUBLISHED和ARCHIVED状态的文章
    sql = """
        SELECT id, title, content, created_at, category_id 
        FROM posts 
        WHERE status = 'PUBLISHED' OR status = 'ARCHIVED'
        ORDER BY created_at DESC
    """
    cursor.execute(sql)
    posts = cursor.fetchall()
    
    print(f"查询到 {len(posts)} 篇文章")
    
    # 获取分类信息
    categories = {}
    cursor.execute("SELECT id, name FROM categories")
    for category in cursor.fetchall():
        categories[category['id']] = category['name']
    
    # 按年月分组归档
    archives = defaultdict(lambda: defaultdict(list))
    for post in posts:
        try:
            created_at = datetime.fromisoformat(post['created_at']) if isinstance(post['created_at'], str) else post['created_at']
            if not created_at:
                continue
                
            year = created_at.year
            month = created_at.month
            
            category_name = categories.get(post['category_id'], None) if post['category_id'] else None
            
            archives[year][month].append({
                'id': post['id'],
                'title': post['title'],
                'created_at': post['created_at'],
                'category': category_name
            })
        except Exception as e:
            print(f"处理文章 {post['id']} 时出错: {e}")
    
    # 生成HTML内容
    print("生成HTML内容...")
    
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>文章归档</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .year-section { margin-bottom: 30px; }
            .month-section { margin-bottom: 20px; }
            .post-item { margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px dashed #eee; }
            .post-date { color: #6c757d; font-size: 0.9rem; }
            .post-title { font-weight: 500; }
            .month-title { font-size: 1.2rem; margin-bottom: 15px; padding-bottom: 5px; border-bottom: 1px solid #dee2e6; }
        </style>
    </head>
    <body>
        <div class="container py-5">
            <div class="row">
                <div class="col-md-8 mx-auto">
                    <div class="card">
                        <div class="card-body">
                            <h1 class="card-title mb-4">文章归档</h1>
    """
    
    # 添加年月文章列表
    sorted_years = sorted(archives.keys(), reverse=True)
    
    if sorted_years:
        for year in sorted_years:
            html_content += f"""
                            <div class="year-section">
                                <h2 class="h3 mb-3">{year}年</h2>
            """
            
            sorted_months = sorted(archives[year].keys(), reverse=True)
            for month in sorted_months:
                posts = archives[year][month]
                html_content += f"""
                                <div class="month-section">
                                    <h3 class="month-title">{month}月 ({len(posts)}篇)</h3>
                                    <ul class="list-unstyled">
                """
                
                for post in posts:
                    created_at = post['created_at']
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.fromisoformat(created_at)
                            date_str = created_at.strftime('%Y-%m-%d')
                        except:
                            date_str = created_at
                    else:
                        date_str = created_at.strftime('%Y-%m-%d')
                    
                    category_badge = f'<span class="badge bg-secondary ms-2">{post["category"]}</span>' if post["category"] else ''
                    
                    html_content += f"""
                                        <li class="post-item">
                                            <span class="post-date">{date_str}</span>
                                            <a href="/blog/post/{post['id']}" class="post-title ms-2">{post['title']}</a>
                                            {category_badge}
                                        </li>
                    """
                
                html_content += """
                                    </ul>
                                </div>
                """
            
            html_content += """
                            </div>
            """
    else:
        html_content += """
                            <p class="text-center text-muted">暂无文章</p>
        """
    
    # 添加页面底部
    html_content += """
                        </div>
                    </div>
                    <div class="mt-4 text-center">
                        <a href="/" class="btn btn-primary">返回首页</a>
                    </div>
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    # 写入HTML文件
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # 关闭数据库连接
    conn.close()
    
    print(f"归档页面已生成: {OUTPUT_PATH}")
    print("\n===== 生成完成 =====")
    print("现在可以通过 http://localhost:5000/static/archive.html 访问归档页面")
    
except Exception as e:
    print(f"生成过程中出错: {str(e)}")
    import traceback
    traceback.print_exc() 