#!/usr/bin/env python3
"""
最终修复归档功能
"""
import os
import sys
import sqlite3
import traceback
from datetime import datetime
import shutil

# 配置变量
DB_PATH = "/data/myblog/instance/blog-dev.db"
VIEWS_PATH = "/data/myblog/app/controllers/blog/views.py"
BACKUP_PATH = "/data/myblog/app/controllers/blog/views.py.bak"

# 创建日志文件
log_file = "/data/myblog/fix_archive_log.txt"
with open(log_file, 'w') as f:
    f.write(f"=== 归档功能最终修复脚本 - {datetime.now()} ===\n\n")

# 日志函数
def log(message):
    print(message)
    with open(log_file, 'a') as f:
        f.write(message + "\n")

# 1. 检查数据库是否存在
if not os.path.exists(DB_PATH):
    log(f"错误: 数据库文件 {DB_PATH} 不存在!")
    sys.exit(1)

try:
    # 2. 备份代码文件
    if os.path.exists(VIEWS_PATH):
        shutil.copy2(VIEWS_PATH, BACKUP_PATH)
        log(f"已创建视图文件备份: {BACKUP_PATH}")
    
    # 3. 修复数据库中的状态
    log("\n=== 1. 修复数据库 ===")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 检查状态列类型
    cursor.execute("PRAGMA table_info(posts)")
    columns = cursor.fetchall()
    for col in columns:
        if col['name'] == 'status':
            log(f"状态列定义: {col}")
    
    # 查询当前状态
    cursor.execute("SELECT id, title, status FROM posts ORDER BY id")
    posts = cursor.fetchall()
    
    status_counts = {}
    for post in posts:
        status = post['status']
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1
    
    log(f"当前状态统计: {status_counts}")
    
    # 确保所有状态值为大写字符串
    cursor.execute("UPDATE posts SET status = upper(status)")
    conn.commit()
    log("已将所有状态值转换为大写")
    
    # 确保特定文章设置为归档状态
    cursor.execute("""
        UPDATE posts 
        SET status = 'ARCHIVED' 
        WHERE title IN ('小型博客系统开发文档', 'test01')
    """)
    conn.commit()
    
    # 创建一个测试归档文章
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    cursor.execute("""
        INSERT INTO posts (
            title, content, status, created_at, updated_at, 
            author_id, summary, category_id
        ) VALUES (
            ?, ?, 'ARCHIVED', datetime('now'), datetime('now'),
            1, '归档测试', 1
        )
    """, (f"最终归档测试_{timestamp}", f"这是通过最终修复脚本创建的归档测试文章。时间戳：{timestamp}"))
    conn.commit()
    new_post_id = cursor.lastrowid
    log(f"已创建测试归档文章: ID={new_post_id}")
    
    # 再次检查状态
    cursor.execute("SELECT status, COUNT(*) as count FROM posts GROUP BY status")
    new_counts = cursor.fetchall()
    for status in new_counts:
        log(f"修复后状态: {status['status']}, 数量: {status['count']}")
    
    # 4. 修改视图代码
    log("\n=== 2. 修改归档视图代码 ===")
    
    archive_view_code = '''@blog_bp.route('/archive')
@blog_bp.route('/archive/<date>')
def archive(date=None):
    """
    文章归档页面
    :param date: 归档日期，格式为 yyyy-MM
    :return:
    """
    try:
        # 直接连接数据库进行查询
        import sqlite3
        from datetime import datetime
        
        # 连接SQLite数据库
        db_path = '/data/myblog/instance/blog-dev.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询所有已发布和已归档的文章
        cursor.execute("""
            SELECT p.id, p.title, p.created_at, c.id as category_id, c.name as category_name, p.status
            FROM posts p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.status = 'PUBLISHED' OR p.status = 'ARCHIVED'
            ORDER BY p.created_at DESC
        """)
        
        rows = cursor.fetchall()
        current_app.logger.info(f"归档页面查询到 {len(rows)} 篇文章")
        
        # 创建文章对象列表
        all_posts = []
        for row in rows:
            # 创建一个简单的类来存储文章数据
            class PostObj:
                pass
            
            post = PostObj()
            post.id = row['id']
            post.title = row['title']
            post.status = row['status']
            
            # 处理创建时间
            created_at = row['created_at']
            if isinstance(created_at, str):
                try:
                    post.created_at = datetime.fromisoformat(created_at)
                except:
                    post.created_at = datetime.now()  # 默认值
            else:
                post.created_at = created_at
            
            # 处理分类
            if row['category_id']:
                class CategoryObj:
                    pass
                
                category = CategoryObj()
                category.id = row['category_id']
                category.name = row['category_name']
                post.category = category
            else:
                post.category = None
            
            all_posts.append(post)
            current_app.logger.info(f"文章: ID={post.id}, 标题={post.title}, 状态={post.status}")
        
        # 按年月分组归档
        archives = {}
        for post in all_posts:
            if not post.created_at:
                continue
            key = f"{post.created_at.year}-{post.created_at.month:02d}"
            if key not in archives:
                archives[key] = []
            archives[key].append(post)
        
        # 创建归档字典，按年月组织
        archive_dict = {}
        sorted_years = []
        
        # 遍历所有归档信息
        for key, posts in archives.items():
            # 分割年月
            year, month = key.split('-')
            year = int(year)
            month = int(month)
            
            # 添加到归档字典
            if year not in archive_dict:
                archive_dict[year] = {}
                sorted_years.append(year)
            
            archive_dict[year][month] = posts
        
        # 对年份进行排序（降序）
        sorted_years.sort(reverse=True)
        
        # 关闭数据库连接
        conn.close()
        
        return render_template('blog/archive.html',
                              archive_dict=archive_dict,
                              sorted_years=sorted_years)
        
    except Exception as e:
        current_app.logger.error(f"获取归档页面失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return render_template('blog/error.html', error_message='服务器内部错误'), 500'''
    
    # 读取当前文件内容
    with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找归档函数并替换
    import re
    pattern = r'@blog_bp\.route\(\'/archive\'\)[\s\S]*?def archive[\s\S]*?return render_template\([\s\S]*?\), 500'
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, archive_view_code, content)
        
        # 写入文件
        with open(VIEWS_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        log("已成功修改归档视图函数")
    else:
        log("警告: 未找到归档视图函数进行替换")
    
    # 5. 清理缓存
    log("\n=== 3. 清理缓存 ===")
    # 导入应用创建函数
    sys.path.append('/data/myblog')
    try:
        from app import create_app
        from app.extensions import cache
        
        app = create_app()
        with app.app_context():
            cache.clear()
            log("已清除缓存")
    except Exception as e:
        log(f"清除缓存失败: {str(e)}")
    
    log("\n=== 修复完成 ===")
    log("请重启应用: /data/myblog/manage.sh restart")
    log("然后访问: http://localhost:5000/blog/archive")
    
except Exception as e:
    log(f"修复过程出错: {str(e)}")
    log(traceback.format_exc()) 