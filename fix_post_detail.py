#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复文章详情页面的问题
"""

import sys
import os
import json
from datetime import datetime

# 添加当前目录到路径，以便导入应用
sys.path.insert(0, os.path.abspath('.'))

# 创建带有调试信息的日志
def log_info(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('fix_post_detail.log', 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

log_info("正在启动修复脚本...")

try:
    # 导入应用
    from app import create_app
    from app.models.post import Post, PostStatus
    from app.extensions import db
    
    log_info("应用导入成功")
    
    # 创建应用上下文
    app = create_app()
    with app.app_context():
        # 查找ID为4的文章
        post = Post.query.get(4)
        
        if post:
            log_info(f"找到文章: ID={post.id}, 标题={post.title}, 状态={post.status}")
            
            # 检查HTML内容
            html_content_exists = bool(post.html_content)
            log_info(f"HTML内容存在: {html_content_exists}")
            if html_content_exists:
                log_info(f"HTML内容长度: {len(post.html_content)}")
            
            # 检查目录
            toc_exists = bool(post._toc)
            log_info(f"目录存在: {toc_exists}")
            if toc_exists:
                try:
                    toc = json.loads(post._toc)
                    log_info(f"目录解析成功，包含 {len(toc)} 个条目")
                except Exception as e:
                    log_info(f"目录解析失败: {str(e)}")
                    # 修复目录
                    post._toc = '[]'
                    log_info("已重置目录为空数组")
            
            # 检查内容渲染
            content_ok = True
            if not post.html_content and post.content:
                log_info("文章有原始内容但没有HTML内容，尝试重新渲染")
                try:
                    post.update_html_content()
                    log_info("成功重新渲染HTML内容")
                except Exception as e:
                    log_info(f"渲染HTML内容失败: {str(e)}")
                    content_ok = False
            
            # 如果目录或内容有问题，保存修复
            if not toc_exists or not content_ok:
                try:
                    db.session.commit()
                    log_info("已保存文章修复")
                except Exception as e:
                    log_info(f"保存修复失败: {str(e)}")
                    db.session.rollback()
            
            # 最后检查文章状态
            log_info(f"最终文章状态: HTML内容长度={len(post.html_content or '')}, 目录项数量={len(json.loads(post._toc)) if post._toc else 0}")
        else:
            log_info("未找到ID为4的文章")
            
            # 查找所有文章
            posts = Post.query.all()
            log_info(f"数据库中共有 {len(posts)} 篇文章")
            for p in posts:
                log_info(f"ID={p.id}, 标题={p.title}, 状态={p.status}, 作者ID={p.author_id}")
            
            # 如果没有找到ID为4的文章，我们可以创建一个测试文章
            log_info("创建一个测试文章作为ID 4")
            new_post = Post(
                title="测试文章",
                content="这是一个测试文章的内容。\n\n## 标题1\n\n这是一些文本。\n\n## 标题2\n\n更多文本。",
                status=PostStatus.PUBLISHED,
                author_id=1  # 假设ID为1的用户是管理员
            )
            db.session.add(new_post)
            db.session.commit()
            log_info(f"创建了测试文章，ID={new_post.id}")
except Exception as e:
    log_info(f"执行过程中发生错误: {str(e)}")
    import traceback
    log_info(traceback.format_exc())

log_info("修复脚本执行完成") 