"""
文件名：wsgi.py
描述：WSGI 应用入口
作者：denny
创建日期：2024-03-21
"""

import resource
import psutil
import logging
from app import create_app

# 设置资源限制 (8GB)
MAX_MEMORY = 8 * 1024 * 1024 * 1024  # 8GB in bytes
resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY, MAX_MEMORY))

# 配置日志
logging.basicConfig(
    filename='logs/memory_usage.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - Memory Usage: %(message)s'
)

def log_memory_usage():
    """记录内存使用情况"""
    process = psutil.Process()
    mem_info = process.memory_info()
    logging.info(f"{mem_info.rss / 1024 / 1024:.2f} MB")

app = create_app('development')
app.config['DEBUG'] = True
app.config['WTF_CSRF_SSL_STRICT'] = False
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = None

@app.before_request
def before_request():
    """每个请求前记录内存使用情况"""
    log_memory_usage()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
