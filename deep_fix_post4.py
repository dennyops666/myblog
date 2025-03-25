#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
深度修复文章ID为4的问题，并详细诊断错误原因
"""

import os
import sys
import json
import traceback
from datetime import datetime
from sqlalchemy import text

# 创建日志文件
log_file = 'fix_post4_detailed.log'
def log(message):
    with open(log_file, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")

log("开始修复文章ID为4...")

try:
    # 导入应用和相关模块
    from app import create_app
    from app.models.post import Post, PostStatus
    from app.extensions import db
    
    log("成功导入应用模块")
    
    # 创建应用上下文
    app = create_app()
    with app.app_context():
        # 获取ID为4的文章
        post = Post.query.get(4)
        
        if post:
            log(f"找到ID为4的文章: {post.title}")
            log(f"文章状态: {post.status}")
            log(f"作者ID: {post.author_id}")
            log(f"原始内容长度: {len(post.content or '')}")
            log(f"HTML内容长度: {len(post.html_content or '')}")
            
            # 检查TOC
            try:
                if post._toc:
                    toc_data = json.loads(post._toc)
                    log(f"TOC格式正确，包含 {len(toc_data)} 个条目")
                else:
                    log("TOC为空")
            except json.JSONDecodeError as e:
                log(f"TOC格式错误: {str(e)}")
                log(f"原始TOC: {post._toc[:100]}...")
                log("重置TOC为空数组")
                post._toc = '[]'
            
            # 检查内容中是否包含模板语法
            if post.content and ('{{' in post.content or '{%' in post.content):
                log("警告：文章内容中包含模板语法，可能导致渲染错误")
                # 转义内容中的模板语法
                content = post.content.replace('{{', '{ {').replace('{%', '{ %')
                post.content = content
                log("已转义模板语法")
            
            # 检查article对象属性
            log("检查文章对象属性...")
            for attr_name in dir(post):
                if not attr_name.startswith('_') and attr_name not in ('query', 'query_class', 'metadata'):
                    try:
                        attr_value = getattr(post, attr_name)
                        # 跳过方法和属性方法
                        if not callable(attr_value):
                            log(f"属性 {attr_name}: {repr(attr_value)}")
                    except Exception as e:
                        log(f"获取属性 {attr_name} 时出错: {str(e)}")
            
            # 完全重建HTML内容
            log("重新渲染HTML内容...")
            post.html_content = None
            try:
                post.update_html_content()
                log("HTML内容渲染成功")
            except Exception as e:
                log(f"渲染HTML内容失败: {str(e)}")
                log(traceback.format_exc())
                
                # 尝试简单的HTML转换作为应急措施
                log("使用应急方法生成HTML内容")
                content = post.content or ''
                # 简单的段落转换
                html_content = ''.join(f'<p>{p}</p>' for p in content.split('\n\n') if p.strip())
                post.html_content = html_content
            
            # 保存更改
            try:
                db.session.commit()
                log("已保存文章修改")
            except Exception as e:
                log(f"保存更改失败: {str(e)}")
                log(traceback.format_exc())
                db.session.rollback()
            
            # 作为最后手段，考虑创建新的文章替代问题文章
            if not post.html_content:
                log("HTML内容仍为空，创建替代文章")
                post.html_content = "<p>此文章内容已被重置</p>"
                post.content = "此文章内容已被重置"
                post._toc = '[]'
                db.session.commit()
                log("已创建替代内容")
        else:
            log("未找到ID为4的文章，创建测试文章")
            
            # 创建新文章
            new_post = Post(
                title="测试文章",
                content="这是一个测试文章。\n\n## 测试标题\n\n这是一些测试内容。",
                status=PostStatus.PUBLISHED,
                author_id=1  # 假设ID为1的用户是管理员
            )
            
            # 手动设置ID
            try:
                # 删除可能存在的ID为4的文章
                db.session.execute(text("DELETE FROM posts WHERE id = 4"))
                # 设置新文章ID
                db.session.add(new_post)
                db.session.flush()
                db.session.execute(text("UPDATE posts SET id = 4 WHERE id = :old_id"), {"old_id": new_post.id})
                db.session.commit()
                log(f"已创建ID为4的测试文章")
            except Exception as e:
                log(f"创建文章失败: {str(e)}")
                log(traceback.format_exc())
                db.session.rollback()
                
                # 不指定ID尝试创建
                new_post = Post(
                    title="测试文章 (自动ID)",
                    content="这是一个测试文章。\n\n## 测试标题\n\n这是一些测试内容。",
                    status=PostStatus.PUBLISHED,
                    author_id=1
                )
                db.session.add(new_post)
                db.session.commit()
                log(f"已创建新测试文章，ID为 {new_post.id}")
        
        # 检查post_detail视图函数中的问题
        log("检查视图函数的问题...")
        # 导入视图模块
        try:
            from app.blog.views import post_detail
            log("成功导入post_detail视图函数")
            
            # 分析视图函数代码
            import inspect
            source = inspect.getsource(post_detail)
            log("post_detail函数源码:")
            log(source)
            
            # 检查视图函数结构
            if "version_info" in source:
                log("发现version_info代码，可能存在日期格式问题")
            if "datetime" in source and "strftime" in source:
                log("发现datetime和strftime代码，可能存在日期格式问题")
        except Exception as e:
            log(f"分析视图函数失败: {str(e)}")
            log(traceback.format_exc())
        
        # 检查模板问题
        try:
            template_file = os.path.join(app.root_path, 'templates', 'blog', 'post_detail.html')
            if os.path.exists(template_file):
                log(f"模板文件存在: {template_file}")
                # 读取模板文件
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                    log(f"模板文件长度: {len(template_content)}")
            else:
                log(f"模板文件不存在: {template_file}")
        except Exception as e:
            log(f"分析模板失败: {str(e)}")

except Exception as e:
    log(f"修复过程中发生错误: {str(e)}")
    log(traceback.format_exc())

log("修复脚本执行完成，请查看日志以获取详细信息") 