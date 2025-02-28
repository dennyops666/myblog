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
from datetime import timedelta

# 设置资源限制 (8GB)
MAX_MEMORY = 8 * 1024 * 1024 * 1024  # 8GB in bytes
resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY, MAX_MEMORY))

# 配置日志
logging.basicConfig(
    filename='logs/myblog.log',
    level=logging.DEBUG,  # 改为DEBUG级别
    format='%(asctime)s - %(levelname)s - %(message)s\n%(exc_info)s'  # 添加异常信息
)

def log_memory_usage():
    """记录内存使用情况"""
    process = psutil.Process()
    mem_info = process.memory_info()
    logging.info(f"{mem_info.rss / 1024 / 1024:.2f} MB")

app = create_app('development')  # 改为development环境
app.config.update(
    DEBUG=True,  # 开启调试模式
    WTF_CSRF_ENABLED=False,  # 禁用 CSRF 保护
    SESSION_COOKIE_SECURE=False,  # 允许非 HTTPS 的会话 cookie
    SESSION_COOKIE_HTTPONLY=True,  # 防止 JavaScript 访问会话 cookie
    SESSION_COOKIE_SAMESITE='Lax',  # 允许跨站点请求
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),  # 会话有效期7天
    SESSION_REFRESH_EACH_REQUEST=True,  # 每次请求都刷新会话
    REMEMBER_COOKIE_DURATION=timedelta(days=7),  # 记住我 cookie 持续时间7天
    REMEMBER_COOKIE_SECURE=False,  # 允许非 HTTPS
    REMEMBER_COOKIE_HTTPONLY=True,  # 防止 JavaScript 访问
    REMEMBER_COOKIE_SAMESITE='Lax',  # 允许跨站点请求
)

@app.before_request
def before_request():
    """每个请求前记录内存使用情况"""
    log_memory_usage()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # 开启调试模式
