#!/usr/bin/env python3
"""
直接归档视图函数
"""
from flask import Blueprint, current_app

# 创建蓝图
archive_bp = Blueprint('archive', __name__, url_prefix='/archive')

@archive_bp.route('/')
def direct_archive():
    """直接从数据库读取并显示归档页面"""
    try:
        import sqlite3
        from datetime import datetime
        
        # 连接数据库
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        current_app.logger.info(f"连接数据库: {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询所有已发布和已归档的文章
        cursor.execute("""
            SELECT id, title, created_at, status 
            FROM posts 
            WHERE status IN ('PUBLISHED', 'ARCHIVED', 'published', 'archived')
            ORDER BY created_at DESC
        """)
        all_posts = cursor.fetchall()
        
        # 为调试输出文章数量和状态
        current_app.logger.info(f"获取到 {len(all_posts)} 篇文章")
        for post in all_posts:
            current_app.logger.info(f"文章ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}")
        
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
        result = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>文章归档</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }
                h1 { color: #333; }
                h2 { color: #555; margin-top: 30px; }
                h3 { color: #777; }
                ul { list-style-type: none; padding-left: 20px; }
                li { margin-bottom: 8px; }
                li a { color: #337ab7; text-decoration: none; }
                li a:hover { text-decoration: underline; }
                .archived { color: #888; }
                .status-count { background: #f5f5f5; padding: 10px; margin-bottom: 20px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>文章归档</h1>
            <div class="status-count">
                <p>共找到 ''' + str(len(all_posts)) + ''' 篇文章</p>
            </div>
        '''
        
        # 按年月排序
        for year in sorted(archive_dict.keys(), reverse=True):
            result += f'<h2>{year}年</h2>'
            for month in sorted(archive_dict[year].keys(), reverse=True):
                result += f'<h3>{month}月</h3><ul>'
                for post in archive_dict[year][month]:
                    status_class = ' class="archived"' if post['status'].upper() == 'ARCHIVED' else ''
                    status_mark = ' [归档]' if post['status'].upper() == 'ARCHIVED' else ''
                    result += f'<li{status_class}><a href="/blog/post/{post["id"]}">{post["title"]}</a>{status_mark}</li>'
                result += '</ul>'
        
        result += '''
        </body>
        </html>
        '''
        
        return result
    except Exception as e:
        import traceback
        error_message = f"归档页面加载失败: {str(e)}\n{traceback.format_exc()}"
        current_app.logger.error(error_message)
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>错误</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
                h1 {{ color: red; }}
                pre {{ background: #f5f5f5; padding: 10px; border-radius: 5px; overflow: auto; }}
            </style>
        </head>
        <body>
            <h1>归档页面加载失败</h1>
            <pre>{error_message}</pre>
        </body>
        </html>
        ''' 