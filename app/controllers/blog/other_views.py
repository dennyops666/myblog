"""
文件名：other_views.py
描述：额外的博客前台视图
"""

from flask import Blueprint, current_app, render_template
import sqlite3
import html
from datetime import datetime

other_bp = Blueprint('other', __name__)

@other_bp.route('/archive_html')
def archive_html():
    """
    直接输出HTML内容显示所有文章
    """
    try:
        # 连接SQLite数据库
        db_path = '/data/myblog/instance/blog-dev.db'
        conn = sqlite3.connect(db_path)
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
            <title>所有文章列表</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .post { margin-bottom: 10px; padding: 10px; border: 1px solid #eee; }
                .archived { background-color: #f8f9fa; }
                .published { background-color: #e9f7ef; }
                .title { font-weight: bold; }
                .status { color: #666; margin-left: 10px; }
                .date { color: #999; font-size: 0.9em; }
            </style>
        </head>
        <body>
            <h1>所有文章列表 (共 {total} 篇)</h1>
            <p>当前时间: {current_time}</p>
            
            <div>
                <h2>文章状态统计</h2>
        """.format(
            total=len(all_posts),
            current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # 添加状态统计
        cursor.execute("SELECT status, COUNT(*) as count FROM posts GROUP BY status")
        status_counts = cursor.fetchall()
        
        html_content += "<ul>"
        for status in status_counts:
            html_content += f"<li>状态: {status['status']}, 数量: {status['count']}</li>"
        html_content += "</ul>"
        
        # 添加文章列表
        html_content += "<h2>文章列表</h2>"
        
        for post in all_posts:
            status_class = "archived" if post['status'] == "ARCHIVED" else "published"
            
            # 格式化创建时间
            created_at = post['created_at']
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at).strftime('%Y-%m-%d')
                except:
                    created_at = "未知日期"
            else:
                created_at = str(created_at)
            
            html_content += f"""
            <div class="post {status_class}">
                <div class="title">ID: {post['id']} - {html.escape(post['title'])}
                    <span class="status">[{post['status']}]</span>
                </div>
                <div class="date">创建时间: {created_at}</div>
            </div>
            """
        
        # 完成HTML内容
        html_content += """
        </body>
        </html>
        """
        
        # 关闭数据库连接
        conn.close()
        
        return html_content
        
    except Exception as e:
        import traceback
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>错误</title></head>
        <body>
            <h1>发生错误</h1>
            <pre>{str(e)}</pre>
            <pre>{traceback.format_exc()}</pre>
        </body>
        </html>
        """
        return error_html 