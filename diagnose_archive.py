#!/usr/bin/env python3
"""
全面诊断归档功能问题
"""
import sys
import traceback
from datetime import datetime, UTC
from app import create_app
from app.extensions import db
from app.models.post import Post, PostStatus
from sqlalchemy import or_, text

app = create_app()

def print_header(title):
    print(f"\n{'=' * 20} {title} {'=' * 20}")

def print_divider():
    print('-' * 60)

try:
    with app.app_context():
        print_header("数据库连接检查")
        try:
            # 测试数据库连接
            result = db.session.execute(text('SELECT 1')).scalar()
            print(f"数据库连接正常: {result == 1}")
        except Exception as e:
            print(f"数据库连接异常: {str(e)}")
            traceback.print_exc()
        
        print_header("数据库状态检查")
        try:
            # 获取数据库中的表
            tables = db.engine.table_names()
            print(f"数据库中的表: {', '.join(tables)}")
            
            # 检查posts表
            posts_count = db.session.query(db.func.count(Post.id)).scalar()
            print(f"文章总数: {posts_count}")
        except Exception as e:
            print(f"数据库状态检查失败: {str(e)}")
            traceback.print_exc()
        
        print_header("文章状态检查")
        try:
            # 检查所有文章的状态
            posts = Post.query.all()
            status_counts = {}
            for post in posts:
                status = str(post.status)
                if status not in status_counts:
                    status_counts[status] = 0
                status_counts[status] += 1
            
            print(f"状态统计: {status_counts}")
            print_divider()
            
            # 获取所有文章
            print("所有文章:")
            for post in posts:
                print(f"ID: {post.id}, 标题: {post.title}")
                print(f"  状态: {post.status} (类型: {type(post.status)})")
                print(f"  创建时间: {post.created_at}")
                print()
        except Exception as e:
            print(f"文章状态检查失败: {str(e)}")
            traceback.print_exc()
        
        print_header("归档查询测试")
        try:
            # 使用PostStatus.ARCHIVED查询
            archived_posts = Post.query.filter_by(status=PostStatus.ARCHIVED).all()
            print(f"使用PostStatus.ARCHIVED查询到 {len(archived_posts)} 篇文章")
            for post in archived_posts:
                print(f"  ID: {post.id}, 标题: {post.title}, 状态: {post.status}")
            
            print_divider()
            
            # 使用字符串'ARCHIVED'查询
            str_archived_posts = Post.query.filter_by(status='ARCHIVED').all()
            print(f"使用字符串'ARCHIVED'查询到 {len(str_archived_posts)} 篇文章")
            for post in str_archived_posts:
                print(f"  ID: {post.id}, 标题: {post.title}, 状态: {post.status}")
            
            print_divider()
            
            # 使用OR条件查询
            or_posts = Post.query.filter(
                or_(Post.status == PostStatus.PUBLISHED, Post.status == PostStatus.ARCHIVED)
            ).all()
            print(f"使用OR条件查询到 {len(or_posts)} 篇文章")
            for i, post in enumerate(or_posts):
                print(f"  {i+1}. ID: {post.id}, 标题: {post.title}, 状态: {post.status}")
        
        except Exception as e:
            print(f"归档查询测试失败: {str(e)}")
            traceback.print_exc()
        
        print_header("修复测试")
        try:
            # 创建一篇测试归档文章
            title = f"归档测试_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
            post = Post(
                title=title,
                content=f"测试内容，创建于 {datetime.now(UTC)}",
                status=PostStatus.ARCHIVED,
                author_id=1  # 假设ID为1的用户存在
            )
            
            # 保存到数据库
            db.session.add(post)
            db.session.commit()
            print(f"创建测试文章成功: ID={post.id}, 标题={post.title}, 状态={post.status}")
            
            # 验证文章状态
            test_post = Post.query.get(post.id)
            print(f"验证文章状态: {test_post.status} (类型: {type(test_post.status)})")
            
            # 清理测试文章
            db.session.delete(test_post)
            db.session.commit()
            print("测试文章已删除")
            
        except Exception as e:
            print(f"修复测试失败: {str(e)}")
            traceback.print_exc()
            db.session.rollback()

except Exception as e:
    print(f"运行诊断脚本时出错: {str(e)}")
    traceback.print_exc()

print("\n脚本执行完成") 