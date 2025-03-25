"""
清理标签数据
"""
from app import create_app
from app.models import Tag, db

app = create_app()

def clean_tags():
    with app.app_context():
        try:
            # 删除所有标签
            Tag.query.delete()
            db.session.commit()
            print("所有标签已清除")
        except Exception as e:
            db.session.rollback()
            print(f"清除标签失败: {str(e)}")

if __name__ == '__main__':
    clean_tags() 