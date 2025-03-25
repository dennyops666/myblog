#!/usr/bin/env python3
"""
手动启动Flask应用的脚本
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 