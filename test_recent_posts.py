from app import create_app
from app.services import get_post_service
import logging
import traceback

# 设置日志级别
logging.basicConfig(level=logging.INFO)

# 创建应用实例
app = create_app()

with app.app_context():
    try:
        print("\n===== 开始测试获取最近文章 =====")
        post_service = get_post_service()
        
        # 获取最近文章
        recent_posts = post_service.get_recent_posts(limit=10)
        
        # 打印结果
        print(f"查询结果类型: {type(recent_posts)}")
        print(f"查询到的文章数量: {len(recent_posts) if recent_posts else 0}")
        
        if recent_posts:
            print("\n文章列表:")
            for i, post in enumerate(recent_posts, 1):
                print(f"{i}. ID={post.id}, 标题='{post.title}', 状态={post.status.name if post.status else 'None'}")
                print(f"   创建时间={post.created_at}, 类型={type(post)}")
                
            # 测试最近文章是否可以在模板中正常渲染
            print("\n测试文章属性访问:")
            for post in recent_posts[:1]:  # 仅测试第一篇文章
                print(f"标题: {post.title}")
                print(f"创建时间: {post.created_at}")
                print(f"状态: {post.status.name}")
                try:
                    print(f"作者: {post.author.username if post.author else 'None'}")
                except Exception as e:
                    print(f"访问作者出错: {str(e)}")
                
                try:
                    print(f"分类: {post.category.name if post.category else 'None'}")
                except Exception as e:
                    print(f"访问分类出错: {str(e)}")
                
                try:
                    print(f"阅读次数: {post.view_count}")
                except Exception as e:
                    print(f"访问阅读次数出错: {str(e)}")
        else:
            print("没有获取到任何文章!")
            
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        traceback.print_exc()
        
    print("\n===== 测试结束 =====") 