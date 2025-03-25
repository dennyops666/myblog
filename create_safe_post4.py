#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建一个安全的ID为4的文章，完全替代有问题的文章
"""

import os
import sys
import traceback
from datetime import datetime
from sqlalchemy import text

def log(message):
    with open('create_post4.log', 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")

log("开始创建安全的文章...")

try:
    # 导入应用和相关模块
    from app import create_app
    from app.models.post import Post, PostStatus
    from app.extensions import db
    
    log("成功导入应用模块")
    
    # 创建应用上下文
    app = create_app()
    with app.app_context():
        # 先检查ID为4的文章
        post = Post.query.get(4)
        
        if post:
            log(f"找到现有ID为4的文章: {post.title}")
            # 删除旧数据
            db.session.delete(post)
            db.session.commit()
            log("已删除原文章")
        
        # 创建安全的测试文章
        safe_content = """# 测试文章

这是一个安全的测试文章，用于替代可能存在问题的文章。

## 测试标题1

这是一些测试内容。

## 测试标题2

更多的测试内容。

### 小标题

* 列表项1
* 列表项2
* 列表项3

```python
# 代码示例
def hello():
    print("Hello World!")
```

---

感谢阅读这篇测试文章。
"""
            
        # 创建新文章
        try:
            new_post = Post(
                title="安全测试文章",
                content=safe_content,
                status=PostStatus.PUBLISHED,
                author_id=1,  # 假设ID为1的用户是管理员
                _toc='[]'  # 确保TOC是一个有效的空JSON数组
            )
            
            # 关闭文章的HTML自动生成，手动设置HTML内容
            new_post.html_content = f"""
<h1>测试文章</h1>
<p>这是一个安全的测试文章，用于替代可能存在问题的文章。</p>
<h2>测试标题1</h2>
<p>这是一些测试内容。</p>
<h2>测试标题2</h2>
<p>更多的测试内容。</p>
<h3>小标题</h3>
<ul>
<li>列表项1</li>
<li>列表项2</li>
<li>列表项3</li>
</ul>
<pre><code class="language-python"># 代码示例
def hello():
    print("Hello World!")
</code></pre>
<hr>
<p>感谢阅读这篇测试文章。</p>
"""
            
            # 添加文章到数据库
            db.session.add(new_post)
            db.session.commit()
            log(f"创建了新文章，ID: {new_post.id}")
            
            # 使用SQL将文章ID设为4
            if new_post.id != 4:
                log(f"将文章ID从 {new_post.id} 修改为 4")
                db.session.execute(text("UPDATE posts SET id = 4 WHERE id = :old_id"), {"old_id": new_post.id})
                db.session.commit()
                log("成功修改文章ID为4")
        except Exception as e:
            log(f"创建文章失败: {str(e)}")
            log(traceback.format_exc())
            db.session.rollback()
            
            # 直接使用SQL插入文章
            log("尝试使用SQL直接插入文章")
            sql = """
            INSERT INTO posts (id, title, content, html_content, toc, status, author_id, created_at, updated_at)
            VALUES (4, '安全测试文章', :content, :html_content, '[]', 'PUBLISHED', 1, :now, :now)
            """
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.session.execute(text(sql), {
                "content": safe_content,
                "html_content": "<h1>测试文章</h1><p>这是安全的测试内容</p>",
                "now": now
            })
            db.session.commit()
            log("成功使用SQL插入文章")
except Exception as e:
    log(f"执行过程中发生错误: {str(e)}")
    log(traceback.format_exc())

log("脚本执行完成") 