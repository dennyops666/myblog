#!/usr/bin/env python3
"""
生成静态HTML归档页面
"""
import sqlite3
import os
import sys
import html
from datetime import datetime

# 配置
DB_PATH = "/data/myblog/instance/blog-dev.db"
OUTPUT_PATH = "/data/myblog/app/static/archive_page.html"

if not os.path.exists(DB_PATH):
    print(f"错误: 数据库文件 {DB_PATH} 不存在!")
    sys.exit(1)

try:
    # 连接SQLite数据库
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 查询所有文章
    cursor.execute("""
        SELECT id, title, status, created_at 
        FROM posts 
        ORDER BY created_at DESC
    """)
    all_posts = cursor.fetchall()
    
    # 生成HTML内容
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>文章归档</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ padding-top: 20px; padding-bottom: 20px; }}
            .post {{ margin-bottom: 10px; padding: 10px; border: 1px solid #eee; }}
            .archived {{ background-color: #f8f9fa; }}
            .published {{ background-color: #e9f7ef; }}
            .title {{ font-weight: bold; }}
            .status {{ color: #666; margin-left: 10px; }}
            .date {{ color: #999; font-size: 0.9em; }}
            .year-section {{ margin-bottom: 30px; }}
            .month-section {{ margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row">
                <div class="col-md-8 mx-auto">
                    <div class="card">
                        <div class="card-body">
                            <h1 class="card-title mb-4">文章归档 (共 {total} 篇)</h1>
                            <p class="text-muted">生成时间: {current_time}</p>
                            
                            <div class="mb-4">
                                <h2 class="h4">文章状态统计</h2>
    """.format(
        total=len(all_posts),
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    # 添加状态统计
    cursor.execute("SELECT status, COUNT(*) as count FROM posts GROUP BY status")
    status_counts = cursor.fetchall()
    
    html_content += "<ul class='list-group mb-3'>"
    for status in status_counts:
        html_content += f"<li class='list-group-item'>状态: <span class='badge bg-secondary'>{status['status']}</span>, 数量: {status['count']}</li>"
    html_content += "</ul>"
    
    # 创建年月归档结构
    year_month_posts = {}
    for post in all_posts:
        created_at = post['created_at']
        if isinstance(created_at, str):
            try:
                date_obj = datetime.fromisoformat(created_at)
            except:
                # 如果转换失败，使用当前时间
                date_obj = datetime.now()
        else:
            # 已经是日期对象
            date_obj = datetime.now()
        
        year = date_obj.year
        month = date_obj.month
        
        if year not in year_month_posts:
            year_month_posts[year] = {}
        
        if month not in year_month_posts[year]:
            year_month_posts[year][month] = []
        
        year_month_posts[year][month].append(post)
    
    # 添加年月结构
    html_content += "<h2 class='h3 mt-4'>文章按年月归档</h2>"
    
    # 对年份进行降序排序
    sorted_years = sorted(year_month_posts.keys(), reverse=True)
    for year in sorted_years:
        html_content += f"""
        <div class="year-section">
            <h3 class="h4 mt-3">{year}年</h3>
        """
        
        # 对月份进行降序排序
        sorted_months = sorted(year_month_posts[year].keys(), reverse=True)
        for month in sorted_months:
            posts = year_month_posts[year][month]
            
            html_content += f"""
            <div class="month-section">
                <h4 class="h5 mt-3">{month}月 ({len(posts)}篇)</h4>
                <ul class="list-group">
            """
            
            for post in posts:
                status_badge = "bg-secondary" if post['status'] == "ARCHIVED" else "bg-success"
                status_text = post['status']
                
                # 格式化创建时间
                created_at = post['created_at']
                if isinstance(created_at, str):
                    try:
                        date_str = datetime.fromisoformat(created_at).strftime('%Y-%m-%d')
                    except:
                        date_str = "未知日期"
                else:
                    date_str = str(created_at)
                
                # 安全处理HTML内容
                safe_title = html.escape(post['title'])
                
                html_content += f"""
                <li class="list-group-item">
                    <span class="date">{date_str}</span>
                    <a href="/blog/post/{post['id']}" class="ms-2">{safe_title}</a>
                    <span class="badge {status_badge} float-end">{status_text}</span>
                </li>
                """
            
            html_content += """
                </ul>
            </div>
            """
        
        html_content += """
        </div>
        """
    
    # 完成HTML内容
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
    
    # 确保目录存在
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # 写入文件
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"归档页面已生成: {OUTPUT_PATH}")
    print(f"访问地址: http://localhost:5000/static/archive_page.html")
    
    # 关闭数据库连接
    conn.close()
    
except Exception as e:
    print(f"生成过程出错: {str(e)}")
    import traceback
    traceback.print_exc() 