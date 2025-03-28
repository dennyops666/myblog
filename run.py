"""
文件名：run.py
描述：应用入口文件
作者：denny
"""

import os
from app import create_app
from app.models import User, Post, Category, Tag, Comment

# 创建应用实例
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

