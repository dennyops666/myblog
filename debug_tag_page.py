import os
import sys
from flask import Flask, current_app
from app.extensions import db
from app.models.tag import Tag
from app.services.post import PostService
from app.utils.pagination import Pagination

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///instance/blog-dev.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    post_service = PostService()
    tag_id = 5
    tag = Tag.query.get(tag_id)
    print(f"标签ID {tag_id}:", tag.name if tag else "不存在")
    
    try:
        page = 1
        per_page = 10
        print("开始测试get_posts_by_tag方法...")
        pagination = post_service.get_posts_by_tag(tag_id, page, per_page)
        print(f"成功获取到 {pagination.total if pagination else 0} 篇文章")
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        print(traceback.format_exc())
