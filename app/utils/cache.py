"""
文件名：cache.py
描述：缓存工具模块
作者：denny
"""

from functools import wraps
from flask import current_app
from datetime import datetime, timedelta

class Cache:
    def __init__(self):
        self._cache = {}
        self._expires = {}

    def get(self, key):
        """获取缓存值"""
        if key in self._cache:
            # 检查是否过期
            if key in self._expires and datetime.now() > self._expires[key]:
                self.delete(key)
                return None
            return self._cache[key]
        return None

    def set(self, key, value, timeout=None):
        """设置缓存值"""
        self._cache[key] = value
        if timeout:
            self._expires[key] = datetime.now() + timedelta(seconds=timeout)

    def delete(self, key):
        """删除缓存值"""
        self._cache.pop(key, None)
        self._expires.pop(key, None)

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._expires.clear()

    def cached(self, timeout=300):
        """缓存装饰器"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # 生成缓存键
                cache_key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
                
                # 尝试从缓存获取
                result = self.get(cache_key)
                if result is not None:
                    return result
                
                # 执行函数并缓存结果
                result = f(*args, **kwargs)
                self.set(cache_key, result, timeout)
                return result
            return decorated_function
        return decorator

# 创建全局缓存实例
cache = Cache() 