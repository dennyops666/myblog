#!/usr/bin/env python3
"""
简单的Flask应用，用于测试服务能否运行
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '服务正常运行中!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True) 