#!/usr/bin/env python3
"""缓存清理脚本"""
from app.extensions import cache
from app import create_app

if __name__ == "__main__":
    # 创建应用上下文
    app = create_app()
    with app.app_context():
        # 清除所有缓存
        print("正在清除所有缓存...")
        cache.clear()
        print("缓存清除完成")
        
        # 验证缓存是否已清除
        test_key = "test_key"
        cache.set(test_key, "test_value")
        value = cache.get(test_key)
        print(f"测试缓存: {test_key} = {value}")
        
        cache.delete(test_key)
        value = cache.get(test_key)
        print(f"删除后: {test_key} = {value}") 