#!/usr/bin/env python
"""
文件名：wsgi.py
描述：WSGI 应用入口
作者：denny
"""

import logging
from app import create_app

# 配置日志
logging.basicConfig(
    filename='logs/myblog.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s\n%(exc_info)s'
)

# 创建应用实例
application = create_app()

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000)
