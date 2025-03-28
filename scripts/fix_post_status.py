#!/usr/bin/env python
"""
文件名：fix_post_status.py
描述：检查并修复文章状态与发布状态的一致性
"""

import os
import sys
import logging

# 设置日志
logging.basicConfig(
    filename='scripts/fix_post_status.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 设置Flask日志级别
import flask.cli
flask.cli.show_server_banner = lambda *args: None
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('flask').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)

from app import create_app
from app.models.post import Post, PostStatus
from app.extensions import db

# 创建应用实例但关闭大部分日志
app = create_app()
app.logger.setLevel(logging.ERROR)

def fix_post_status_consistency():
    """检查并修复所有文章的状态与发布状态一致性"""
    with app.app_context():
        print("开始检查文章状态一致性...")
        logging.info("开始检查文章状态一致性...")
        
        # 查询所有文章
        posts = Post.query.all()
        inconsistent_count = 0
        
        for post in posts:
            # 检查状态一致性
            if post.status == PostStatus.PUBLISHED and not post.published:
                msg = f"不一致: ID={post.id}, 标题='{post.title}', 状态={post.status.value}, published={post.published}"
                print(msg)
                logging.info(msg)
                post.published = True
                inconsistent_count += 1
            elif post.status != PostStatus.PUBLISHED and post.published:
                msg = f"不一致: ID={post.id}, 标题='{post.title}', 状态={post.status.value}, published={post.published}"
                print(msg)
                logging.info(msg)
                post.published = False
                inconsistent_count += 1
        
        if inconsistent_count > 0:
            msg = f"发现 {inconsistent_count} 篇文章状态不一致，开始修复..."
            print(msg)
            logging.info(msg)
            db.session.commit()
            print("修复完成!")
            logging.info("修复完成!")
        else:
            msg = "所有文章状态一致，无需修复。"
            print(msg)
            logging.info(msg)

if __name__ == "__main__":
    try:
        fix_post_status_consistency()
    except Exception as e:
        print(f"发生错误: {str(e)}")
        logging.error(f"发生错误: {str(e)}", exc_info=True) 