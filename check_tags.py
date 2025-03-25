"""
检查标签数据
"""
from app import create_app
from app.models import Tag

app = create_app()

def check_tags():
    with app.app_context():
        tags = Tag.query.all()
        print("\n现有标签：")
        for tag in tags:
            print(f"ID: {tag.id}")
            print(f"名称: {tag.name}")
            print(f"别名: {tag.slug}")
            print(f"描述: {tag.description}")
            print("-" * 50)

if __name__ == '__main__':
    check_tags() 