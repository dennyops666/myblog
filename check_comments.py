from app import create_app; from app.models.comment import Comment; app = create_app(); with app.app_context(): print(f"评论总数：{Comment.query.count()}")
